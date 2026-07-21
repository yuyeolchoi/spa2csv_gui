from __future__ import annotations

import struct
from pathlib import Path

import pytest


def make_spa(path: Path, values=(0.25, 0.5, 1.0), first=4000.0, last=400.0) -> Path:
    """Write a minimal but format-accurate OMNIC SPA file.

    Layout mirrors the real format: uint16 entry count at 294, 16-byte
    directory entries from 304 (key at +0, block position at +2, block length
    at +6), key 2 = header (nx at +4, firstx at +16, lastx at +20),
    key 3 = float32 intensity block.
    """

    header_offset = 400
    data_offset = 512
    data_length = 4 * len(values)
    content = bytearray(data_offset + data_length)
    struct.pack_into("<H", content, 294, 2)  # two directory entries
    # entry 0 (key 2 -> header block), entry 1 (key 3 -> intensity block)
    struct.pack_into("<BxII", content, 304, 2, header_offset, 0)
    struct.pack_into("<BxII", content, 320, 3, data_offset, data_length)
    struct.pack_into("<I", content, header_offset + 4, len(values))
    struct.pack_into("<f", content, header_offset + 16, first)
    struct.pack_into("<f", content, header_offset + 20, last)
    struct.pack_into(f"<{len(values)}f", content, data_offset, *values)
    path.write_bytes(content)
    return path


@pytest.fixture
def synthetic_spa(tmp_path: Path) -> Path:
    return make_spa(tmp_path / "한글 시료.spa")
