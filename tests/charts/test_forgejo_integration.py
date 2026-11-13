"""Optional package boundaries and Forgejo OIDC contracts."""

import json
import os
import subprocess
import unittest
from pathlib import Path

import yaml

from helm import ROOT, documents, env_value, render


def render_oidc(values):
    base = os.environ.get("BASE_REPO")
    if not base:
        raise unittest.SkipTest("BASE_REPO is required for shared OIDC rendering")
    settings = {**values, "enabled": values["forgejo"]["enabled"],
                "clientSecret": {"name": "forgejo-oidc-values", "key": "oidcClientSecret"}}
    return render(str(Path(base) / "charts/keycloak/addon-oidc"), settings,
                  namespace="auth-keycloak")


class ForgejoIntegrationTests(unittest.TestCase):
    def test_private_certificate_profiles_and_oidc(self):
        values = {"forgejo": {"enabled": True, "hostname": "forgejo.example.com"},
                  "externalGateway": {"enabled": False}}
        oidc = render_oidc(values)
        self.assertEqual(json.loads(env_value(oidc, "KC_REDIRECT_URIS")),
                         ["https://forgejo.example.com/user/oauth2/keycloak/callback"])
        self.assertEqual(env_value(oidc, "KC_GATEWAY_ROLE_SCOPE"), "[]")
        self.assertIn('key: "oidcClientSecret"', oidc.stdout)
        self.assertEqual(env_value(oidc, "KC_ROLE_CLAIM"), "forgejo_roles")
        self.assertEqual(json.loads(env_value(oidc, "KC_REALM_ROLE_SCOPE")),
                         ["forgejo-user", "forgejo-admin"])
        self.assertFalse([doc for doc in documents(oidc) if doc["kind"] == "Secret"])
        self.assertFalse(render_oidc({"forgejo": {"enabled": False}}).stdout.strip())

    def test_oidc_direct_delivery_and_consumers(self):
        producer = yaml.safe_load(
            (ROOT / "releases/forgejo/secret-sync/oidc.yaml").read_text())["spec"]
        self.assertNotIn("template", producer["target"])
        outputs = {entry["secretKey"]: entry["remoteRef"] for entry in producer["data"]}
        self.assertEqual(outputs, {"oidcClientSecret": {
            "key": "addons/forgejo/oidc", "property": "oidcClientSecret"}})
        values = {"forgejo": {"enabled": True, "hostname": "forgejo.example.com"}}
        job = next(doc for doc in documents(render_oidc(values))
                   if doc["kind"] == "Job")
        env = job["spec"]["template"]["spec"]["containers"][0]["env"]
        reference = next(item for item in env if item["name"] == "KC_CLIENT_SECRET")
        self.assertEqual(reference["valueFrom"]["secretKeyRef"], {
            "name": producer["target"]["name"], "key": "oidcClientSecret"})
        for path in (ROOT / "releases").rglob("*.yaml"):
            for doc in yaml.safe_load_all(path.read_text()):
                if doc and doc.get("kind") == "HelmRelease":
                    self.assertTrue(all(item["kind"] == "ConfigMap"
                                        for item in doc["spec"].get("valuesFrom", [])), path)

    def test_postgres_direct_delivery(self):
        result = subprocess.run([
            "kustomize", "build", "--load-restrictor", "LoadRestrictionsNone",
            str(ROOT / "releases/forgejo/secret-sync"),
        ], capture_output=True, text=True, check=True)
        postgres = [doc for doc in documents(result)
                    if doc["kind"] == "ExternalSecret"
                    and doc["metadata"]["name"] == "forgejo-postgres-password"]
        self.assertEqual(len(postgres), 1)
        self.assertEqual(postgres[0]["spec"]["data"], [{"secretKey": "password", "remoteRef": {
            "key": "addons/forgejo/database", "property": "dbPassword"}}])
        self.assertNotIn("values.yaml:", yaml.safe_dump(postgres[0], default_flow_style=False))
