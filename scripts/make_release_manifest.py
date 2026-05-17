from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create LearnKit update manifest.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--platform", default="windows")
    parser.add_argument("--release-url", required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    asset = args.asset.resolve()
    manifest = {
        "version": args.version,
        "platform": args.platform,
        "asset_name": asset.name,
        "sha256": sha256_file(asset),
        "release_url": args.release_url,
        "notes": args.notes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
