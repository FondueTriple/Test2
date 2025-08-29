import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from wine_cellar import WineCellar


def test_add_remove_and_comment(tmp_path):
    cellar_file = tmp_path / "cellar.json"
    cellar = WineCellar(filepath=str(cellar_file))

    bottle = cellar.add_bottle("Chateau Test", 2020)
    assert bottle.id == 1
    assert "vivino.com" in bottle.vivino_url

    cellar.add_comment(bottle.id, "Excellent")
    assert cellar.bottles[bottle.id].comments == ["Excellent"]

    assert cellar.remove_bottle(bottle.id) is True
    assert bottle.id not in cellar.bottles


def test_persistence(tmp_path):
    cellar_file = tmp_path / "cellar.json"
    cellar = WineCellar(filepath=str(cellar_file))
    cellar.add_bottle("Wine A", 2019)

    # Reload from disk
    cellar2 = WineCellar(filepath=str(cellar_file))
    assert len(cellar2.list_bottles()) == 1


def test_edit_bottle(tmp_path):
    cellar_file = tmp_path / "cellar.json"
    cellar = WineCellar(filepath=str(cellar_file))
    bottle = cellar.add_bottle("Old Wine", 2000)

    assert cellar.edit_bottle(bottle.id, name="New Wine", year=2001) is True
    edited = cellar.bottles[bottle.id]
    assert edited.name == "New Wine"
    assert edited.year == 2001
    assert "New+Wine+2001" in edited.vivino_url

    assert cellar.edit_bottle(999, name="Nope") is False

