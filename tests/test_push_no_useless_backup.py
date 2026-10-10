"""`config push` ne sauvegarde ni ne remplace un fichier deja identique (0.21.2).

Cas d'origine : pi4fred, 2026-10-10, cinq morfsystem.json.bak-* strictement identiques
au fichier actif, un par update.

Run: python tests/test_push_no_useless_backup.py   (also collected by pytest)
"""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from morfdeploy.core import Deployer  # noqa: E402


def _push(text_src, text_dest):
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "svc.json").write_text(text_src)
        dest = root / "etc" / "svc.json"
        dest.parent.mkdir()
        dest.write_text(text_dest)
        cfg = SimpleNamespace(source="svc.json", resolved_dest=lambda _d: dest)
        dep = Deployer.__new__(Deployer)
        dep.manifest = SimpleNamespace(repo_root=root, configs=[cfg])
        changed = dep._push_configs(root / "etc")
        return changed, sorted(p.name for p in dest.parent.iterdir()), dest.read_text()


def test_identical_file_is_left_alone():
    changed, files, _ = _push("{}", "{}")
    assert not changed and files == ["svc.json"]


def test_different_file_is_backed_up_and_replaced():
    changed, files, content = _push('{"a": 1}', "{}")
    assert changed and content == '{"a": 1}'
    assert len(files) == 2 and any(".bak-" in f for f in files)


if __name__ == "__main__":
    test_identical_file_is_left_alone()
    test_different_file_is_backed_up_and_replaced()
    print("ok")
