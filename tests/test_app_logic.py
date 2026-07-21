import os
from pathlib import Path

from spa_to_csv.app import MAX_WORKERS, unique_spa_paths, worker_count


def test_unique_spa_paths_filters_and_deduplicates(tmp_path: Path) -> None:
    spa = tmp_path / "시료.SPA"
    txt = tmp_path / "notes.txt"
    result = unique_spa_paths([spa], [spa, txt, tmp_path / "." / "시료.SPA"])
    assert result == [spa.resolve()]


def test_worker_count_never_exceeds_files_or_cap() -> None:
    assert MAX_WORKERS == 4
    assert worker_count(0) == 1
    assert worker_count(1) == 1
    # never more threads than files
    assert worker_count(2) <= 2
    # honors the upper cap regardless of core count
    assert worker_count(10_000) <= MAX_WORKERS
    # scales with available cores but stays within the cap
    expected = max(1, min(10_000, (os.cpu_count() or 4) * 2, MAX_WORKERS))
    assert worker_count(10_000) == expected
