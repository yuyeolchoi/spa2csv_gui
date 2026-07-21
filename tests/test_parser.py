from pathlib import Path

import numpy as np
import pytest

from spa_to_csv.parser import SpaParseError, parse_spa


def test_parse_synthetic_spa(synthetic_spa: Path) -> None:
    x, y, meta = parse_spa(synthetic_spa)
    np.testing.assert_allclose(x, [4000, 2200, 400])
    np.testing.assert_allclose(y, [0.25, 0.5, 1.0])
    assert meta["point_count"] == 3


def test_parse_error_names_file(tmp_path: Path) -> None:
    broken = tmp_path / "손상.spa"
    broken.write_bytes(b"bad")
    with pytest.raises(SpaParseError, match="손상.spa"):
        parse_spa(broken)
