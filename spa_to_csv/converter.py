"""CSV conversion functions."""

from __future__ import annotations

import csv
from pathlib import Path

from .parser import parse_spa


def convert_spa_to_csv(file_path: str | Path) -> Path:
    """Convert one SPA file beside the source and overwrite an existing CSV."""

    source = Path(file_path)
    wavenumbers, intensities, _ = parse_spa(source)
    destination = source.with_suffix(".csv")
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["Wavenumber (cm-1)", "Intensity"])
        writer.writerows(zip(wavenumbers, intensities))
    return destination
