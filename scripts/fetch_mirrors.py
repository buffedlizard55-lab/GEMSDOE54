#!/usr/bin/env python3
"""Fetch every hash-pinned competition mirror and FAIL CLOSED on any digest mismatch.

Why this file exists
--------------------
The single blocker the previous sessions kept hitting was "data placement": drivendata.org
requires an authenticated login and is additionally **unreachable** from this sandbox.
`curl -L https://www.drivendata.org/...` returns ``curl: (35) OpenSSL SSL_connect:
SSL_ERROR_SYSCALL`` (exit 35) — verified 2026-10-08 in this checkout, see
``registry/irregularities.json`` IR-54-DATA-01.

The bytes are nevertheless obtainable: the group published them as **public GitHub blobs**
(`buffedlizard55-lab/GEMSDOE`, `.../GEMSDOE24`, `.../GEMSDOE27`) and pinned every one of them
with a SHA-256 in ``registry/data_manifest.json``.  A pinned public mirror is not organizer
authentication; what makes it *usable* is that every byte is checked.  A fetch that does not
verify is worthless, so this one verifies and exits non-zero on any mismatch.

Usage
-----
    python3 scripts/fetch_mirrors.py [--dest .cache/gems_data] [--group core,external,scored]
    python3 scripts/fetch_mirrors.py --list

Requires: ``gh`` authenticated for github.com (or GH_TOKEN in the environment).
DrivenData credentials are never used and drivendata.org is never contacted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "data_manifest.json"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def gh_raw(repo: str, ref: str, path: str, out: Path) -> None:
    """Download one blob through the GitHub API and write it to ``out``."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}",
             "-H", "Accept: application/vnd.github.raw"],
            stdout=fh, stderr=subprocess.PIPE,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"gh api failed for {repo}:{path}@{ref}: "
                           f"{proc.stderr.decode(errors='replace')[:400]}")


def fetch_one(spec: dict, dest: Path, reuse: bool = True) -> dict:
    target = dest / spec["dest"]
    if reuse and target.exists():
        got, n = sha256_of(target), target.stat().st_size
        if got == spec["sha256"] and n == spec["bytes"]:
            return {"id": spec["id"], "status": "cached-verified",
                    "bytes": n, "sha256": got, "dest": str(target)}
    if "parts" in spec:
        chunks = []
        for i, part in enumerate(spec["parts"]):
            c = dest / f".part-{spec['id']}-{i:03d}"
            gh_raw(spec["repo"], spec["ref"], part, c)
            chunks.append(c)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as out:
            for c in chunks:
                out.write(c.read_bytes())
        for c in chunks:
            c.unlink()
    else:
        gh_raw(spec["repo"], spec["ref"], spec["path"], target)

    got, n = sha256_of(target), target.stat().st_size
    ok = (got == spec["sha256"]) and (n == spec["bytes"])
    if not ok:
        target.unlink(missing_ok=True)
    return {"id": spec["id"], "status": "PASS" if ok else "FAIL",
            "bytes": n, "sha256": got, "dest": str(target),
            "expected_sha256": spec["sha256"], "expected_bytes": spec["bytes"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=os.environ.get("GEMS_DATA_DIR", str(ROOT / ".cache" / "gems_data")))
    ap.add_argument("--group", default="core,external,scored")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-reuse", action="store_true")
    args = ap.parse_args()

    spec = json.loads(MANIFEST.read_text())
    groups = [g for g in args.group.split(",") if g]
    wanted = [f for f in spec["files"] if f.get("group") in groups]

    if args.list:
        for f in wanted:
            print(f"{f['group']:9s} {f['id']:46s} {f['bytes']:>12,} bytes  {f['dest']}")
        print(f"{len(wanted)} files, {sum(f['bytes'] for f in wanted)/1e6:.1f} MB")
        return 0

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    fails, receipt = [], []
    for f in wanted:
        r = fetch_one(f, dest, reuse=not args.no_reuse)
        receipt.append(r)
        print(f"{r['status']:15s} {r['id']:46s} {r['bytes']:>12,} bytes  {r['sha256'][:16]}...")
        if r["status"] == "FAIL":
            fails.append(f["id"])

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "fetch_receipt.json").write_text(json.dumps(
        {"schema_version": 1, "dest": str(dest), "verified": len(wanted) - len(fails),
         "failed": fails, "files": receipt}, indent=1))

    print(json.dumps({"verified": len(wanted) - len(fails), "failed": fails}, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
