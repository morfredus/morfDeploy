"""Les bibliotheques de compilation sont reconnues sous MSYS2 (0.22.0).

Cas d'origine : sous Windows, `morf build` affichait « no package for this platform » pour
openssl / libssh2 / nlohmann-json, faute de gestionnaire reconnu. MSYS2 est maintenant detecte
depuis le compilateur du PATH (UCRT64, ou MINGW64 deprecie) et les paquets sont VERIFIES.

Run: python tests/test_msys2_builddeps.py   (also collected by pytest)
"""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from morfdeploy import builddeps, sysdeps  # noqa: E402


def _fake_msys2(root: Path, env: str):
    (root / env / "bin").mkdir(parents=True)
    (root / "usr" / "bin").mkdir(parents=True)
    (root / "usr" / "bin" / "pacman.exe").write_bytes(b"")
    return str(root / env / "bin" / "g++.exe")


def _detect(cxx):
    """detect_build_package_manager() comme sous Windows, compilateur impose."""
    real = (sysdeps.platform.system, sysdeps.shutil.which, sysdeps.detect_package_manager)
    sysdeps.platform.system = lambda: "Windows"
    sysdeps.shutil.which = lambda name: cxx if name == "g++" else None
    sysdeps.detect_package_manager = lambda: (None, None)
    try:
        return sysdeps.detect_build_package_manager()
    finally:
        sysdeps.platform.system, sysdeps.shutil.which, sysdeps.detect_package_manager = real


def test_ucrt64_is_recognised_and_packages_follow_the_environment():
    with tempfile.TemporaryDirectory() as d:
        family, manager = _detect(_fake_msys2(Path(d), "ucrt64"))
        assert (family, manager) == ("msys2-ucrt64", "pacman")
        assert builddeps.packages_for("openssl", family) == ["mingw-w64-ucrt-x86_64-openssl"]
        assert builddeps.packages_for("nlohmann-json", family) == ["mingw-w64-ucrt-x86_64-nlohmann-json"]
        # pacman est appele par son chemin complet (absent du PATH de PowerShell).
        assert sysdeps.install_command("pacman", ["x"])[0].endswith("pacman.exe")


def test_mingw64_keeps_its_own_package_prefix():
    with tempfile.TemporaryDirectory() as d:
        family, _ = _detect(_fake_msys2(Path(d), "mingw64"))
        assert family == "msys2-mingw64"
        assert builddeps.packages_for("libssh2", family) == ["mingw-w64-x86_64-libssh2"]


def test_official_qt_toolchain_stays_unsupported():
    # Un g++ hors MSYS2 (C:/Qt/Tools/...) : pas de gestionnaire, comme avant.
    assert _detect("C:/Qt/Tools/mingw1310_64/bin/g++.exe") == (None, None)


def test_runtime_detection_is_untouched_on_windows():
    # Les dependances d'EXECUTION ne voient toujours pas MSYS2 (voir detect_build_package_manager).
    real = sysdeps.platform.system
    sysdeps.platform.system = lambda: "Windows"
    try:
        assert sysdeps.detect_package_manager() == (None, None)
    finally:
        sysdeps.platform.system = real


def test_missing_package_is_reported_by_resolve():
    dep = SimpleNamespace(id="zlib", required=True)
    status = builddeps.resolve([dep], "msys2-ucrt64", "pacman")[0]
    assert status.packages == ("mingw-w64-ucrt-x86_64-zlib",)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
