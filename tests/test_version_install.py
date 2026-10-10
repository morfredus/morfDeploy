"""install_files doit copier VERSION a cote du binaire (0.21.1).

Cas d'origine : pi4fred, 2026-10-10, /opt/morfanalytics/VERSION disait 0.36.1 alors que le
binaire installe etait en 0.69.x : seul le chemin .deb copiait VERSION.

Run: python tests/test_version_install.py   (also collected by pytest)
"""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from morfdeploy.core import Deployer  # noqa: E402


def test_version_is_installed_and_reported():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        repo, app = root / "repo", root / "opt" / "svc"
        repo.mkdir()
        (repo / "VERSION").write_text("1.2.3\n")
        binary = repo / "svc"
        binary.write_text("bin")
        # Deployer sans __init__ : on ne teste que install_files.
        dep = Deployer.__new__(Deployer)
        dep.manifest = SimpleNamespace(repo_root=repo, binary_name=lambda: "svc",
                                       helper_binary=None, configs=[])
        dep.backend = SimpleNamespace(install_runtime=lambda *a: None)
        written = dep.install_files(binary, app, root / "etc")
        assert (app / "VERSION").read_text() == "1.2.3\n"
        assert app / "VERSION" in written


if __name__ == "__main__":
    test_version_is_installed_and_reported()
    print("ok")
