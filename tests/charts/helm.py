"""Offline Helm helpers for Forgejo charts."""

import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LINT_VALUES = ROOT / "tests/validation/helm-lint-values.yaml"


def render(chart, values=None, *, namespace="catalog-test", release="catalog-test",
           value_files=(LINT_VALUES,), extra_args=(), check=True):
    command = ["helm", "template", release, str(ROOT / "charts" / chart), "--namespace", namespace]
    for path in value_files:
        command.extend(("--values", str(path)))
    result = subprocess.run([*command, "--values", "-", *extra_args],
                            input=json.dumps(values or {}), capture_output=True, text=True)
    if check and result.returncode:
        raise AssertionError(result.stderr + result.stdout)
    return result


def documents(result):
    return [doc for doc in yaml.safe_load_all(result.stdout) if doc]


def env_value(result, name):
    for doc in documents(result):
        pod = doc.get("spec", {}).get("template", {}).get("spec", {})
        for container in pod.get("containers", []) + pod.get("initContainers", []):
            for item in container.get("env", []):
                if item["name"] == name:
                    return item["value"]
    raise AssertionError(f"missing environment variable {name}")
