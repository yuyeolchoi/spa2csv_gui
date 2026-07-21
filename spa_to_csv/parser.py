"""Minimal parser for the spectrum stored in a Thermo OMNIC SPA file."""

from __future__ import annotations

from pathlib import Path
import struct
from typing import Any

import numpy as np


class SpaParseError(ValueError):
    """Raised when an SPA file does not contain a readable spectrum."""


# OMNIC lays out a directory of 16-byte entries. The entry count is a uint16 at
# offset 294; the entries themselves start at 304. Within each entry: a uint8
# "key" at +0, the referenced block position (uint32) at +2, and the block
# length (uint32) at +6. Field offsets and key meanings follow the format
# reverse-engineered by spectrochempy's read_omnic.
NLINES_OFFSET = 294
DIRECTORY_OFFSET = 304
DIRECTORY_ENTRY_SIZE = 16
HEADER_ENTRY_KEY = 2  # block holds nx, firstx, lastx
DATA_ENTRY_KEY = 3  # block holds the float32 intensity array

# Field offsets inside the header block (key 2).
HEADER_NX = 4
HEADER_FIRSTX = 16
HEADER_LASTX = 20


def _fail(path: Path, reason: str) -> SpaParseError:
    return SpaParseError(f"{path.name}: {reason}")


def _directory_entries(data: bytes, path: Path) -> list[tuple[int, int, int]]:
    """Return (key, block_position, block_length) for each directory entry."""

    if len(data) < NLINES_OFFSET + 2:
        raise _fail(path, "파일이 SPA 디렉터리를 포함하기에 너무 짧습니다")

    declared = struct.unpack_from("<H", data, NLINES_OFFSET)[0]
    available = (len(data) - DIRECTORY_OFFSET) // DIRECTORY_ENTRY_SIZE
    if declared < 1:
        raise _fail(path, "디렉터리 항목 수가 0입니다")
    if declared > available:
        raise _fail(path, "디렉터리가 파일 범위를 벗어납니다")

    entries: list[tuple[int, int, int]] = []
    for index in range(declared):
        base = DIRECTORY_OFFSET + index * DIRECTORY_ENTRY_SIZE
        key = data[base]
        block_position, block_length = struct.unpack_from("<II", data, base + 2)
        if block_position:
            entries.append((key, block_position, block_length))
    return entries


def parse_spa(file_path: str | Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Return wavenumbers, intensities and basic metadata from an SPA file.

    OMNIC records block locations in 16-byte directory entries. The header block
    (key 2) carries the point count and wavenumber range; the intensity block
    (key 3) holds a contiguous float32 array.
    """

    path = Path(file_path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise _fail(path, f"파일을 읽을 수 없습니다 ({exc})") from exc

    entries = _directory_entries(data, path)
    header_blocks = [(pos, length) for key, pos, length in entries if key == HEADER_ENTRY_KEY]
    data_blocks = [(pos, length) for key, pos, length in entries if key == DATA_ENTRY_KEY]
    if not header_blocks:
        raise _fail(path, "스펙트럼 헤더 블록(key 2)을 찾을 수 없습니다")
    if not data_blocks:
        raise _fail(path, "스펙트럼 데이터 블록(key 3)을 찾을 수 없습니다")

    # The first key-2/key-3 pair is OMNIC's primary spectrum. Later entries can
    # describe history, interferograms, or derived spectra.
    header_offset = header_blocks[0][0]
    data_offset, data_length = data_blocks[0]
    if header_offset + HEADER_LASTX + 4 > len(data):
        raise _fail(path, "스펙트럼 헤더가 잘렸습니다")

    point_count = struct.unpack_from("<I", data, header_offset + HEADER_NX)[0]
    first_x = struct.unpack_from("<f", data, header_offset + HEADER_FIRSTX)[0]
    last_x = struct.unpack_from("<f", data, header_offset + HEADER_LASTX)[0]
    if point_count < 1:
        raise _fail(path, "스펙트럼 포인트 수가 올바르지 않습니다")
    if not np.isfinite(first_x) or not np.isfinite(last_x):
        raise _fail(path, "파수 범위가 올바르지 않습니다")

    # The directory records the block length; trust the header point count but
    # never read past the recorded block or the file end.
    byte_count = point_count * 4
    if data_length and byte_count > data_length:
        raise _fail(path, "스펙트럼 데이터 길이가 헤더와 일치하지 않습니다")
    if data_offset + byte_count > len(data):
        raise _fail(path, "스펙트럼 데이터가 잘렸습니다")

    intensities = np.frombuffer(
        data, dtype="<f4", count=point_count, offset=data_offset
    ).astype(np.float64)
    if not np.all(np.isfinite(intensities)):
        raise _fail(path, "강도 데이터에 유효하지 않은 값이 있습니다")
    # OMNIC constructs its ascending x-axis in single precision, so build that
    # grid and reverse it to preserve the parser's descending-axis contract.
    wavenumbers = np.linspace(
        np.float32(last_x), np.float32(first_x), point_count, dtype=np.float32
    )[::-1].astype(np.float64)
    meta = {
        "source": str(path),
        "point_count": point_count,
        "first_wavenumber": float(first_x),
        "last_wavenumber": float(last_x),
        "data_offset": data_offset,
        "header_offset": header_offset,
    }
    return wavenumbers, intensities, meta
