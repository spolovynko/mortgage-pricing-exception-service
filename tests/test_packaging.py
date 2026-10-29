"""Check installation independently of the repository working directory."""

import subprocess
import sys
from pathlib import Path


def test_installed_package_imports_outside_repository(tmp_path: Path) -> None:
    """A broken src-layout install must fail even if local imports would work."""
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import mortgage_pricing; "
            "from importlib.metadata import distribution; "
            "distribution('mortgage-pricing-exception-service')",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
