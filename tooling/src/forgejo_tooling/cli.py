"""Thin Forgejo commands using the shared parser and payload staging helper."""

import argparse
from importlib.resources import as_file, files
from pathlib import Path

from k8s_stack_tooling.addons import ContractError, load_manifest
from k8s_stack_tooling.api.payloads import DEFAULT_DESTINATION, PayloadError, stage_payloads


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Forgejo definitions")
    parser.add_argument("root", type=Path)
    parser.add_argument("--list-packages", action="store_true")
    args = parser.parse_args(argv)
    try:
        addon = load_manifest(args.root / "release/manifest.yaml")
        if addon.metadata.name != "forgejo":
            raise ContractError("expected the Forgejo add-on")
    except ContractError as exc:
        parser.exit(1, f"{exc}\n")
    if args.list_packages:
        for package in addon.spec.packages:
            print(package.path)
    else:
        print("Forgejo definition schema is valid")
    return 0


def stage_bootstrap(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage the native bootstrap payload")
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args(argv)
    try:
        with as_file(files("forgejo_tooling").joinpath("payloads")) as source:
            stage_payloads(source, ["bootstrap.sh"], destination=args.destination)
    except (OSError, PayloadError):
        parser.exit(1, "Could not stage the bootstrap payload\n")
    return 0
