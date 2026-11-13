"""Product integration; native bootstrap behavior remains in chart tests."""

import os
import stat
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest
import yaml
from k8s_stack_tooling.addons import (
    check,
    load_manifest,
    resolve_browser_identity,
)
from k8s_stack_tooling.addons.helm_images import validate_helm_images
from k8s_stack_tooling.addons.validation import render

from forgejo_tooling.cli import main, stage_bootstrap

ROOT = Path(__file__).resolve().parents[2]


def test_definition_uses_shared_parser_and_installable_metadata(capsys):
    assert main([str(ROOT)]) == 0
    assert "schema is valid" in capsys.readouterr().out
    check(ROOT)
    check(ROOT, installable=True)


def test_packaged_payload_stages_for_native_execution(tmp_path):
    assert stage_bootstrap(["--destination", str(tmp_path)]) == 0
    staged = tmp_path / "bootstrap.sh"
    assert (
        staged.read_bytes()
        == files("forgejo_tooling").joinpath("payloads/bootstrap.sh").read_bytes()
    )
    assert stat.S_IMODE(staged.stat().st_mode) == 0o444
    subprocess.run(["bash", "-n", str(staged)], check=True)


def test_actual_images_and_nonsecret_browser_settings():
    base_path = os.environ.get("BASE_REPO")
    if not base_path:
        pytest.fail("BASE_REPO is required for candidate composition")
    base = Path(base_path)
    addon = load_manifest(ROOT / "release/manifest.yaml")
    packages = {
        package.name: render(ROOT / package.path, root=ROOT) for package in addon.spec.packages
    }
    configmaps = {
        (item["metadata"]["namespace"], item["metadata"]["name"]): item
        for resources in packages.values()
        for item in resources
        if item["kind"] == "ConfigMap"
    }
    values = yaml.safe_load((ROOT / "tests/validation/helm-lint-values.yaml").read_text())
    for item in addon.spec.inputs:
        if item.kind != "ConfigMap":
            continue
        if item.name == "forgejo-oidc-settings":
            data = {"authentication": values["authentication"]}
        elif item.name == "forgejo-oidc-approval-values":
            data = {"clientApproval": values["clientApproval"]}
        elif item.name == "client-values":
            data = {
                k: v for k, v in values.items() if k not in {"authentication", "clientApproval"}
            }
        else:
            data = {}
        configmaps[(item.namespace, item.name)] = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"namespace": item.namespace, "name": item.name},
            "data": {"values.yaml": yaml.safe_dump(data)},
        }
    resolve_browser_identity(addon.spec.identities[0], values)
    validate_helm_images(
        addon,
        packages,
        sources={
            ("GitRepository", "flux-system", "k8s-stack"): base,
            ("GitRepository", "flux-system", "forgejo-addon"): ROOT,
        },
        configmaps=configmaps,
        kube_version="1.34.1",
        api_versions=(
            "gateway.networking.k8s.io/v1",
            "external-secrets.io/v1",
            "policy.cert-manager.io/v1alpha1",
        ),
    )


def test_browser_rejects_missing_approval(tmp_path):
    base = os.environ.get("BASE_REPO")
    if not base:
        pytest.fail("BASE_REPO is required for shared OIDC rendering")
    values = tmp_path / "unapproved.yaml"
    values.write_text(
        "enabled: true\nclientSecret:\n  name: forgejo-oidc-values\n"
        "  key: oidcClientSecret\nclientApproval:\n  redirectUris: []\n"
    )
    result = subprocess.run(
        [
            "helm",
            "template",
            "test",
            str(Path(base) / "charts/keycloak/addon-oidc"),
            "--namespace",
            "auth-keycloak",
            "-f",
            str(ROOT / "tests/validation/helm-lint-values.yaml"),
            "-f",
            str(values),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "approval" in result.stderr
