import os
from pathlib import Path

from spa_to_csv.app import unique_spa_paths, worker_count


def test_unique_spa_paths_filters_and_deduplicates(tmp_path: Path) -> None:
    spa = tmp_path / "시료.SPA"
    txt = tmp_path / "notes.txt"
    result = unique_spa_paths([spa], [spa, txt, tmp_path / "." / "시료.SPA"])
    assert result == [spa.resolve()]


def test_worker_count_never_exceeds_files_or_cap() -> None:
    assert worker_count(0) == 1
    assert worker_count(1) == 1
    # never more threads than files
    assert worker_count(2) <= 2
    # honors an upper cap regardless of core count
    assert worker_count(10_000) <= 16
    # scales with available cores but stays within the cap
    expected = max(1, min(10_000, (os.cpu_count() or 4) * 2, 16))
    assert worker_count(10_000) == expected
