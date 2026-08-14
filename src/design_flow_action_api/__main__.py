from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from .app import create_app
from .config import ActionAPIConfig


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run or export the Design Flow Action API")
    parser.add_argument("--export-openapi", nargs="?", const="openapi.json")
    args = parser.parse_args(argv)
    app = create_app()
    if args.export_openapi:
        target = Path(args.export_openapi)
        target.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
        print(target.resolve())
        return
    config = ActionAPIConfig.from_env()
    uvicorn.run(app, host=config.host, port=config.port, log_level="info")


if __name__ == "__main__":
    main()
