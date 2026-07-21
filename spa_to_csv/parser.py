"""Minimal parser for the spectrum stored in a Thermo OMNIC SPA file."""

from __future__ import annotations

from pathlib import Path
import struct
from typing import Any

import numpy as np


class SpaParseError(ValueError):
    """Raised when an SPA file does not contain a readable spectrum."""


DIRECTORY_OFFSET = 304
DIRECTORY_ENTRY_SIZE = 16
DATA_ENTRY_TYPE = 2
HEADER_ENTRY_TYPE = 3


def _fail(path: Path, reason: str) -> SpaParseError:
    return SpaParseError(f"{path.name}: {reason}")


def _directory_entries(data: bytes, path: Path) -> list[tuple[int, int]]:
    if len(data) <= DIRECTORY_OFFSET:
        raise _fail(path, "파일이 SPA 디렉터리를 포함하기에 너무 짧습니다")

    declared = data[30] if len(data) > 30 else 0
    available = (len(data) - DIRECTORY_OFFSET) // DIRECTORY_ENTRY_SIZE
    if not declared:
        raise _fail(path, "디렉터리 항목 수가 0입니다")
    if declared > available:
        raise _fail(path, "디렉터리가 파일 범위를 벗어납니다")

    entries: list[tuple[int, int]] = []
    for index in range(declared):
        base = DIRECTORY_OFFSET + index * DIRECTORY_ENTRY_SIZE
        entry_type = data[base]
        block_offset = struct.unpack_from("<I", data, base + 2)[0]
        if block_offset:
            entries.append((entry_type, block_offset))
    return entries


def parse_spa(file_path: str | Path) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """Return wavenumbers, intensities and basic metadata from an SPA file.

    OMNIC stores block locations in 16-byte directory entries.  The spectrum
    data block is type 2 and its matching header is type 3.
    """

    path = Path(file_path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise _fail(path, f"파일을 읽을 수 없습니다 ({exc})") from exc

    entries = _directory_entries(data, path)
    data_offsets = [offset for kind, offset in entries if kind == DATA_ENTRY_TYPE]
    header_offsets = [offset for kind, offset in entries if kind == HEADER_ENTRY_TYPE]
    if not data_offsets:
        raise _fail(path, "스펙트럼 데이터 블록(type 2)을 찾을 수 없습니다")
    if not header_offsets:
        raise _fail(path, "스펙트럼 헤더 블록(type 3)을 찾을 수 없습니다")

    # The first type-2/type-3 pair is OMNIC's primary spectrum. Other entries
    # can describe history, interferograms, or derived spectra.
    data_offset, header_offset = data_offsets[0], header_offsets[0]
    if header_offset + 16 > len(data):
        raise _fail(path, "스펙트럼 헤더가 잘렸습니다")

    point_count = struct.unpack_from("<I", data, header_offset + 4)[0]
    first_x, last_x = struct.unpack_from("<ff", data, header_offset + 8)
    if point_count < 1:
        raise _fail(path, "스펙트럼 포인트 수가 올바르지 않습니다")
    if not np.isfinite(first_x) or not np.isfinite(last_x):
        raise _fail(path, "파수 범위가 올바르지 않습니다")

    byte_count = point_count * 4
    if data_offset + byte_count > len(data):
        raise _fail(path, "스펙트럼 데이터가 잘렸습니다")

    intensities = np.frombuffer(
        data, dtype="<f4", count=point_count, offset=data_offset
    ).astype(np.float64)
    if not np.all(np.isfinite(intensities)):
        raise _fail(path, "강도 데이터에 유효하지 않은 값이 있습니다")
    wavenumbers = np.linspace(first_x, last_x, point_count, dtype=np.float64)
    meta = {
        "source": str(path),
        "point_count": point_count,
        "first_wavenumber": float(first_x),
        "last_wavenumber": float(last_x),
        "data_offset": data_offset,
        "header_offset": header_offset,
    }
    return wavenumbers, intensities, meta
