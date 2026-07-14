"""Minimum-image neighbour-shell identification."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from ase import Atoms


@dataclass(frozen=True)
class ShellSite:
    """A site grouped into a neighbour shell."""

    index: int
    distance: float
    shell: int


def minimum_image_distance(atoms: Atoms, i: int, j: int) -> float:
    """Return the minimum-image distance between two atom indices in Angstrom."""
    return float(atoms.get_distance(i, j, mic=True))


def group_neighbour_shells(atoms: Atoms, center_index: int, tolerance: float = 0.03) -> list[ShellSite]:
    """Group all non-centre atoms around a site into distance shells."""
    distances = [
        (i, minimum_image_distance(atoms, center_index, i))
        for i in range(len(atoms))
        if i != center_index
    ]
    distances.sort(key=lambda item: (item[1], item[0]))
    shell_representatives: list[float] = []
    grouped: list[ShellSite] = []
    for index, distance in distances:
        for shell_number, representative in enumerate(shell_representatives, start=1):
            if abs(distance - representative) <= tolerance:
                grouped.append(ShellSite(index, float(distance), shell_number))
                break
        else:
            shell_representatives.append(distance)
            grouped.append(ShellSite(index, float(distance), len(shell_representatives)))
    return sorted(grouped, key=lambda site: (site.shell, site.distance, site.index))


def select_shell_site(atoms: Atoms, center_index: int, shell: int | str, tolerance: float) -> ShellSite:
    """Select the lowest-index site from a requested shell, or from the farthest shell."""
    grouped = group_neighbour_shells(atoms, center_index, tolerance)
    requested = max(site.shell for site in grouped) if shell == "far" else int(shell)
    choices = [site for site in grouped if site.shell == requested]
    if not choices:
        raise ValueError(f"No sites found for shell {shell}")
    return sorted(choices, key=lambda site: (site.distance, site.index))[0]


def cell_vectors_list(atoms: Atoms) -> list[list[float]]:
    """Return cell vectors as JSON-friendly nested lists."""
    return np.asarray(atoms.cell).astype(float).tolist()
