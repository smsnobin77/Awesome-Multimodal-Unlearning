from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def paper_dir() -> Path:
    path = ROOT.parent / "_paper"
    if not path.exists():
        pytest.skip("../_paper not found")
    return path


@pytest.fixture(scope="session")
def sections(paper_dir) -> Path:
    return paper_dir / "sections"
