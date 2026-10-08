#!/usr/bin/env python3
"""Inventory every raster-like file in the GEMS-named sibling repositories.

Read-only. Uses the GitHub REST API through the authenticated ``gh`` CLI (api.github.com).
Output: a JSON inventory (default ``/tmp/sib/inventory.json``, scratch, outside the repository)
with, per repository, the default-branch commit and every ``.tif`` / ``.tiff`` / ``.zip`` blob
(path, size, git blob id). Blob ids allow an independent re-check on GitHub.

Run:  python scripts/inventory_siblings.py --out /tmp/sib/inventory.json --repos-json /tmp/repos.json
where ``/tmp/repos.json`` is produced by:
      gh repo list buffedlizard55-lab --limit 500 --json name,defaultBranchRef,isPrivate,createdAt,diskUsage,description
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

OWNER = "buffedlizard55-lab"
PATTERN = re.compile(r"GEMS", re.IGNORECASE)


def gh_json(args: list[str]):
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        return None, proc.stderr.strip()[:300]
    return json.loads(proc.stdout), None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repos-json", default="/tmp/repos.json")
    ap.add_argument("--out", default="/tmp/sib/inventory.json")
    args = ap.parse_args()

    with open(args.repos_json, encoding="utf-8") as fh:
        rows = json.load(fh)
    gems = sorted((r for r in rows if PATTERN.search(r["name"])), key=lambda r: r["name"].lower())
    out = []
    for r in gems:
        name = r["name"]
        branch = (r.get("defaultBranchRef") or {}).get("name") or "main"
        ref, err = gh_json([f"repos/{OWNER}/{name}/git/refs/heads/{branch}"])
        if ref is None:
            out.append({"repo": name, "branch": branch, "error": err})
            continue
        sha = ref["object"]["sha"]
        tree, err = gh_json([f"repos/{OWNER}/{name}/git/trees/{sha}?recursive=1"])
        if tree is None:
            out.append({"repo": name, "branch": branch, "commit": sha, "error": err})
            continue
        rasters = [
            {"path": e["path"], "size": e.get("size", 0), "blob": e["sha"]}
            for e in tree.get("tree", [])
            if e["type"] == "blob" and e["path"].lower().endswith((".tif", ".tiff", ".zip"))
        ]
        out.append({"repo": name, "branch": branch, "commit": sha,
                    "truncated": tree.get("truncated", False),
                    "n_tree_files": len(tree.get("tree", [])), "rasters": rasters})
        print(f"{name:<18} commit={sha[:10]} rasters={len(rasters)}", flush=True)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("TOTAL raster-like files:", sum(len(o.get("rasters", [])) for o in out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
