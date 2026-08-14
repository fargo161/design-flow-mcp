"""Build-context regression proof: ignored secret fixtures never enter the image."""

from __future__ import annotations

import io
import subprocess
import sys
import tarfile
from pathlib import Path
from uuid import uuid4


def run(*args: str) -> str:
    return subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout


def main() -> None:
    image = sys.argv[1] if len(sys.argv) > 1 else "design-flow-action-api:secret-check"
    root = Path(__file__).resolve().parents[1]
    marker = f"DESIGN_FLOW_BUILD_SECRET_{uuid4().hex}"
    fixture = root / ".env.secret-fixture"
    if fixture.exists():
        raise RuntimeError(f"Refusing to overwrite existing fixture: {fixture}")
    fixture.write_text(f"DESIGN_FLOW_API_KEY={marker}\n", encoding="utf-8")
    try:
        run("docker", "build", "-t", image, str(root))
        container_id = run("docker", "create", image).strip()
        try:
            archive = subprocess.run(
                ["docker", "export", container_id], check=True, capture_output=True
            ).stdout
            assert marker.encode() not in archive, "Secret fixture marker found in image filesystem"
            with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as filesystem:
                members = {Path(member.name).name for member in filesystem.getmembers()}
            assert fixture.name not in members, "Ignored fixture file found in image filesystem"
        finally:
            subprocess.run(
                ["docker", "rm", "-f", container_id], check=False, capture_output=True
            )
    finally:
        fixture.unlink(missing_ok=True)
    print("Docker secret exclusion validation passed")


if __name__ == "__main__":
    main()
