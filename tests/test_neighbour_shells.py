from almgsi_dft.neighbour_shells import group_neighbour_shells, minimum_image_distance, select_shell_site
from almgsi_dft.structures import al_2x2x2_conventional_supercell


def test_neighbour_shells_first_second_far():
    atoms = al_2x2x2_conventional_supercell()
    first = select_shell_site(atoms, 0, 1, 0.03)
    second = select_shell_site(atoms, 0, 2, 0.03)
    far = select_shell_site(atoms, 0, "far", 0.03)
    assert first.distance < second.distance < far.distance
    assert first.index != second.index != far.index


def test_minimum_image_distance_is_periodic():
    atoms = al_2x2x2_conventional_supercell()
    distance = minimum_image_distance(atoms, 0, 31)
    assert distance > 0
    assert distance < max(atoms.cell.lengths())


def test_neighbour_shell_tolerance():
    atoms = al_2x2x2_conventional_supercell()
    shells = group_neighbour_shells(atoms, 0, tolerance=0.2)
    assert any(site.shell == 1 for site in shells)
