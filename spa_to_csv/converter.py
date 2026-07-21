"""CSV conversion functions."""

from __future__ import annotations

import csv
from pathlib import Path

from .parser import parse_spa


def _omnic_float(value: float) -> str:
    """Format a number like an OMNIC CSV export."""

    mantissa, exp = f"{value:.6e}".split("e")
    return f"{mantissa}e{int(exp):+04d}"


def convert_spa_to_csv(file_path: str | Path) -> Path:
    """Convert one SPA file beside the source and overwrite an existing CSV."""

    source = Path(file_path)
    wavenumbers, intensities, _ = parse_spa(source)
    destination = source.with_suffix(".csv")
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\r\n")
        writer.writerows(
            (_omnic_float(wavenumber), _omnic_float(intensity))
            for wavenumber, intensity in zip(wavenumbers[::-1], intensities[::-1])
        )
    return destination
