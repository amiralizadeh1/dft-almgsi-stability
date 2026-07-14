from almgsi_dft.structures import al_2x2x2_conventional_supercell, isolated_substitution, mg_si_pair


def test_al_supercell_has_32_sites():
    atoms = al_2x2x2_conventional_supercell()
    assert len(atoms) == 32
    assert atoms.get_chemical_symbols().count("Al") == 32


def test_isolated_substitution_is_deterministic():
    mg = isolated_substitution("Mg")
    si = isolated_substitution("Si")
    assert mg.metadata["solute_index"] == si.metadata["solute_index"] == 1
    assert mg.atoms.get_chemical_symbols().count("Mg") == 1
    assert si.atoms.get_chemical_symbols().count("Si") == 1


def test_pair_compositions():
    pair = mg_si_pair(1)
    symbols = pair.atoms.get_chemical_symbols()
    assert symbols.count("Al") == 30
    assert symbols.count("Mg") == 1
    assert symbols.count("Si") == 1
