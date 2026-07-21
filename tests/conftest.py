from __future__ import annotations

import struct
from pathlib import Path

import pytest


def make_spa(path: Path, values=(0.25, 0.5, 1.0), first=4000.0, last=400.0) -> Path:
    header_offset = 400
    data_offset = 512
    content = bytearray(data_offset + 4 * len(values))
    content[30] = 2
    struct.pack_into("<BBI10x", content, 304, 2, 0, data_offset)
    struct.pack_into("<BBI10x", content, 320, 3, 0, header_offset)
    struct.pack_into("<Iff", content, header_offset + 4, len(values), first, last)
    struct.pack_into(f"<{len(values)}f", content, data_offset, *values)
    path.write_bytes(content)
    return path


@pytest.fixture
def synthetic_spa(tmp_path: Path) -> Path:
    return make_spa(tmp_path / "한글 시료.spa")
