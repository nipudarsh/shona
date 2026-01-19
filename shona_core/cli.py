from __future__ import annotations
import argparse, json
from shona_core.scan import run_scan
from shona_core.diff import diff_latest_two
from shona_core.risk import score_diff

def main():
    p = argparse.ArgumentParser(prog="shona")
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("scan")
    s.add_parser("diff")
    a = p.parse_args()

    if a.cmd == "scan":
        print(run_scan())
    else:
        d = diff_latest_two()
        r = score_diff(d)
        print(json.dumps({"diff": d, "risk": r}, indent=2))
