from pathlib import Path

import numpy as np
import pytest

from conftest import make_spa
from spa_to_csv.parser import SpaParseError, parse_spa


def test_parse_synthetic_spa(synthetic_spa: Path) -> None:
    x, y, meta = parse_spa(synthetic_spa)
    np.testing.assert_allclose(x, [4000, 2200, 400])
    np.testing.assert_allclose(y, [0.25, 0.5, 1.0])
    assert meta["point_count"] == 3


def test_wavenumbers_use_omnic_float32_grid(tmp_path: Path) -> None:
    first = np.float32(4000.188)
    last = np.float32(649.904)
    spa = make_spa(
        tmp_path / "float32-grid.spa", values=range(7), first=first, last=last
    )

    wavenumbers, _, _ = parse_spa(spa)

    expected = np.linspace(last, first, 7, dtype=np.float32)[::-1].astype(np.float64)
    float64_grid = np.linspace(float(first), float(last), 7, dtype=np.float64)
    np.testing.assert_array_equal(wavenumbers, expected)
    assert not np.array_equal(wavenumbers, float64_grid)


def test_parse_error_names_file(tmp_path: Path) -> None:
    broken = tmp_path / "손상.spa"
    broken.write_bytes(b"bad")
    with pytest.raises(SpaParseError, match="손상.spa"):
        parse_spa(broken)
