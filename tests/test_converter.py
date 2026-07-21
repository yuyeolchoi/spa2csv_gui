import csv
import re
from pathlib import Path

from spa_to_csv.converter import _omnic_float, convert_spa_to_csv


def test_convert_name_encoding_and_contents(synthetic_spa: Path) -> None:
    output = convert_spa_to_csv(synthetic_spa)
    assert output.name == "한글 시료.csv"
    with output.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows == [
        ["4.000000e+002", "1.000000e+000"],
        ["2.200000e+003", "5.000000e-001"],
        ["4.000000e+003", "2.500000e-001"],
    ]
    assert rows[0][0] != "Wavenumber (cm-1)"
    assert [float(row[0]) for row in rows] == sorted(float(row[0]) for row in rows)
    assert all(re.fullmatch(r"-?\d\.\d{6}e[+-]\d{3}", value) for row in rows for value in row)

    raw_output = output.read_bytes()
    assert raw_output.endswith(b"\r\n")
    assert b"\n" not in raw_output.replace(b"\r\n", b"")


def test_existing_csv_is_overwritten(synthetic_spa: Path) -> None:
    output = synthetic_spa.with_suffix(".csv")
    output.write_text("old", encoding="utf-8")
    convert_spa_to_csv(synthetic_spa)
    assert "old" not in output.read_text(encoding="utf-8")


def test_omnic_float() -> None:
    assert _omnic_float(649.904) == "6.499040e+002"
    assert _omnic_float(0.0386065).endswith("e-002")
    assert _omnic_float(-649.904) == "-6.499040e+002"
    assert _omnic_float(0.0) == "0.000000e+000"
    assert _omnic_float(1.23e120) == "1.230000e+120"
