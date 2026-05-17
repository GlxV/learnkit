from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.infrastructure.update.update_installer import UpdateInstallError, install_update


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LearnKit external updater")
    parser.add_argument("--package", required=True, dest="package_path")
    parser.add_argument("--install-dir", required=True)
    parser.add_argument("--app-exe", required=True)
    parser.add_argument("--pid", type=int, default=0)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--restart", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        install_update(
            package_path=Path(args.package_path),
            install_dir=Path(args.install_dir),
            expected_sha256=args.expected_sha256,
            app_exe=Path(args.app_exe),
            pid=args.pid or None,
            restart=args.restart,
        )
    except UpdateInstallError as exc:
        print(f"LearnKit update failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
