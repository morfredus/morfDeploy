"""Check of configmerge, on the real case that motivated 0.21.0.

Run: python tests/test_configmerge.py   (also collected by pytest)

morfAnalytics on pi4fred, 2026-09-29: the installed config still carried
`altitude_m` (retired in 0.63.0) and lacked the `discovery` / `morfsync_url`
keys added inside existing modules, because update only merged top-level keys
and never removed anything.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from morfdeploy.configmerge import merge_config  # noqa: E402

REFERENCE = {
    "_comment": "new doc",
    "http_port": 8799,
    "modules": [
        {"id": "analytics-1", "type": "analytics", "source_url": "",
         "_comment_morfsync": "doc", "morfsync_url": ""},
        {"id": "photo-1", "type": "photo", "discovery": {"enabled": True}},
        {"id": "github-1", "type": "github"},   # not installed: must NOT appear
    ],
}

INSTALLED = {
    "_comment": "old doc",
    "http_port": 9000,                           # user value: kept
    "my_own_key": 1,                             # unknown, not declared: kept, reported
    "modules": [
        {"id": "analytics-1", "type": "analytics", "source_url": "http://meteohub.local",
         "_comment_altitude": "old doc", "altitude_m": 8},
        {"id": "photo-1", "type": "photo"},
    ],
}


def run(removed_keys=("modules[].altitude_m",)):
    with tempfile.TemporaryDirectory() as tmp:
        ref, inst = Path(tmp, "x.example.json"), Path(tmp, "x.json")
        ref.write_text(json.dumps(REFERENCE), encoding="utf-8")
        inst.write_text(json.dumps(INSTALLED), encoding="utf-8")
        report = merge_config(ref, inst, removed_keys=removed_keys)
        result = json.loads(inst.read_text(encoding="utf-8"))
        backups = list(Path(tmp).glob("x.json.bak-*"))
        return report, result, backups


def test_real_case():
    report, cfg, backups = run()
    analytics, photo = cfg["modules"]
    # Retired key deleted, its comment dropped (the reference no longer has it).
    assert "altitude_m" not in analytics and "_comment_altitude" not in analytics
    assert report.removed == ["modules[analytics-1].altitude_m"]
    # New keys reach modules the user already has.
    assert analytics["morfsync_url"] == "" and photo["discovery"] == {"enabled": True}
    # User values kept; comments follow the reference.
    assert analytics["source_url"] == "http://meteohub.local"
    assert cfg["http_port"] == 9000 and cfg["_comment"] == "new doc"
    # A module the user does not have is never switched on.
    assert [m["id"] for m in cfg["modules"]] == ["analytics-1", "photo-1"]
    # Unknown, undeclared key: kept and reported, never guessed away.
    assert cfg["my_own_key"] == 1 and report.obsolete == ["my_own_key"]
    assert report.changed and len(backups) == 1


def test_undeclared_retired_key_is_only_reported():
    report, cfg, _ = run(removed_keys=())
    assert cfg["modules"][0]["altitude_m"] == 8
    assert "modules[analytics-1].altitude_m" in report.obsolete


def test_up_to_date_file_is_not_rewritten():
    report, cfg, _ = run()
    with tempfile.TemporaryDirectory() as tmp:
        ref, inst = Path(tmp, "x.example.json"), Path(tmp, "x.json")
        ref.write_text(json.dumps(REFERENCE), encoding="utf-8")
        inst.write_text(json.dumps(cfg), encoding="utf-8")
        again = merge_config(ref, inst, removed_keys=("modules[].altitude_m",))
        assert not again.changed and not list(Path(tmp).glob("x.json.bak-*"))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  : {name}")
