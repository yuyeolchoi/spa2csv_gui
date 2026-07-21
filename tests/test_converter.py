import csv
from pathlib import Path

from spa_to_csv.converter import convert_spa_to_csv


def test_convert_name_encoding_and_contents(synthetic_spa: Path) -> None:
    output = convert_spa_to_csv(synthetic_spa)
    assert output.name == "한글 시료.csv"
    with output.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ["Wavenumber (cm-1)", "Intensity"]
    assert rows[1:] == [["4000.0", "0.25"], ["2200.0", "0.5"], ["400.0", "1.0"]]


def test_existing_csv_is_overwritten(synthetic_spa: Path) -> None:
    output = synthetic_spa.with_suffix(".csv")
    output.write_text("old", encoding="utf-8")
    convert_spa_to_csv(synthetic_spa)
    assert "old" not in output.read_text(encoding="utf-8")
