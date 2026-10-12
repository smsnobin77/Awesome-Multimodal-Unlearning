"""Write data/paper_text.txt, the paper's text that CI checks the planner quotes against.

    uv run --group import scripts/snapshot_paper.py --paper-dir ../_paper
"""

import argparse
from pathlib import Path

from latex import paper_text

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-dir", type=Path, default=ROOT.parent / "_paper")
    args = ap.parse_args()
    out = ROOT / "data" / "paper_text.txt"
    out.write_text(paper_text(args.paper_dir / "sections"))
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
