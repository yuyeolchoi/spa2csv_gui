from pathlib import Path

from spa_to_csv.app import unique_spa_paths


def test_unique_spa_paths_filters_and_deduplicates(tmp_path: Path) -> None:
    spa = tmp_path / "시료.SPA"
    txt = tmp_path / "notes.txt"
    result = unique_spa_paths([spa], [spa, txt, tmp_path / "." / "시료.SPA"])
    assert result == [spa.resolve()]
