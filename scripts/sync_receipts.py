#!/usr/bin/env python3
"""Propagate the built artefact's SHA-256 and byte count into every document.

A published hash that has drifted from the file it describes is worse than no hash,
because it invites someone to upload the wrong bytes.  This script is the single
source of truth: it reads ``registry/<slug>.build.json`` and rewrites the hash, the
size and the dot count in the README, the Pages site and the JSON registries.

Run it after any rebuild; ``scripts/run_all.sh`` calls it.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "gems54-undercomplement-q200"


def main() -> int:
    receipt = json.loads((ROOT / "registry" / f"{SLUG}.build.json").read_text())
    sha = receipt["output"]["sha256"]
    size = receipt["output"]["bytes"]
    dots = receipt["counts"]["emitted_dots"]
    size_grouped = f"{size:,}"
    print(f"artefact: {SLUG}\n  sha256 = {sha}\n  bytes  = {size_grouped}\n  dots   = {dots:,}")

    edits: list[tuple[str, int]] = []

    def sub(path: Path, pattern: str, repl: str, *, expect: int | None = None) -> None:
        text = path.read_text(encoding="utf-8")
        new, n = re.subn(pattern, repl, text)
        if n == 0:
            raise SystemExit(f"FAILED: pattern not found in {path}: {pattern[:70]}")
        if expect is not None and n != expect:
            raise SystemExit(f"FAILED: {path}: matched {n} times, expected {expect}")
        path.write_text(new, encoding="utf-8")
        edits.append((str(path.relative_to(ROOT)), n))

    sha_re = r"(?<=SHA-256:\*\* `)[0-9a-f]{64}(?=`)"
    sub(ROOT / "README.md", sha_re, sha, expect=1)
    sub(ROOT / "README.md", r"(?<=\*\*Bytes:\*\* )[\d,]+", size_grouped, expect=1)
    sub(ROOT / "README.md", r"(?<=\*\*Positive cells:\*\* )[\d,]+", f"{dots:,}", expect=1)

    sub(ROOT / "docs/index.html", r"(?<=SHA-256</dt><dd class=\"hash\">)[0-9a-f]{64}", sha, expect=1)
    sub(ROOT / "docs/index.html", r"(?<=<dt>Size</dt><dd>)[\d,]+(?= bytes</dd>)", size_grouped, expect=1)
    sub(ROOT / "docs/index.html", r"(?<=<dt>Predictions</dt><dd>)[\d,]+(?= positive cells)",
        f"{dots:,}", expect=1)

    sub(ROOT / "registry/run_card.json", r"(?<=\"raster_sha256\": \")[0-9a-f]{64}", sha, expect=1)
    sub(ROOT / "registry/run_card.json", r"(?<=\"raster_bytes\": )\d+", str(size), expect=1)
    sub(ROOT / "registry/run_card.json", r"(?<=\"positive_cells\": )\d+", str(dots), expect=1)

    sub(ROOT / "registry/submissions.json", r"(?<=\"sha256\": \")[0-9a-f]{64}", sha, expect=1)
    sub(ROOT / "registry/submissions.json", r"(?<=\"positive_cells\": )\d+", str(dots), expect=1)

    for path, count in edits:
        print(f"  updated {path} ({count} substitution{'s' if count != 1 else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
