import os
from pathlib import Path

from spa_to_csv.app import MAX_WORKERS, find_spa_files, unique_spa_paths, worker_count


def test_unique_spa_paths_filters_and_deduplicates(tmp_path: Path) -> None:
    spa = tmp_path / "시료.SPA"
    txt = tmp_path / "notes.txt"
    result = unique_spa_paths([spa], [spa, txt, tmp_path / "." / "시료.SPA"])
    assert result == [spa.resolve()]


def test_unique_spa_paths_accepts_extensionless_split_files(tmp_path: Path) -> None:
    # OMNIC series split writes extension-less SPA files (e.g. sample0000).
    split0 = tmp_path / "CsFA_CO20000"
    split1 = tmp_path / "CsFA_CO20001"
    csv = tmp_path / "already.csv"  # outputs must not be re-ingested
    srs = tmp_path / "series.srs"  # the series container itself is not a spectrum
    result = unique_spa_paths([], [split0, split1, csv, srs])
    assert result == [split0.resolve(), split1.resolve()]


def test_find_spa_files_recurses_subfolders(tmp_path: Path) -> None:
    # Parent holds per-series subfolders of extension-less split files.
    (tmp_path / "series_a").mkdir()
    (tmp_path / "series_b").mkdir()
    (tmp_path / "series_a" / "s0000").write_bytes(b"x")
    (tmp_path / "series_a" / "s0001").write_bytes(b"x")
    (tmp_path / "series_b" / "t0000").write_bytes(b"x")
    (tmp_path / "top.spa").write_bytes(b"x")
    (tmp_path / "series_a" / "s0000.csv").write_bytes(b"x")  # output, skip
    (tmp_path / "series_a" / "notes.txt").write_bytes(b"x")  # not a spectrum

    found = {p.name for p in find_spa_files(tmp_path)}
    assert found == {"s0000", "s0001", "t0000", "top.spa"}


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
