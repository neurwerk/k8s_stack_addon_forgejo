"""Required setup integration preserves prepared outputs and password custody."""

import base64
import hashlib
import json
import secrets
from pathlib import Path
from unittest.mock import Mock

import pytest
from k8s_stack_tooling.addons import load_manifest
from openbao_stack_setup import client as client_module
from openbao_stack_setup import declarative

ROOT = Path(__file__).resolve().parents[2]


def test_prepared_output_retry_readers_and_handover_identity():
    addon = load_manifest(ROOT / "release/manifest.yaml")
    name = addon.metadata.name
    setups = {name: addon.spec.setup}
    definitions = {
        name: hashlib.sha256((ROOT / "release/manifest.yaml").read_bytes()).hexdigest()
    }
    snapshots = {}
    client = Mock(spec=client_module.OpenBaoClient)
    client.read_secret.side_effect = snapshots.get

    def encode(value):
        return base64.urlsafe_b64encode(value).decode().rstrip("=")

    # This tests the native-output format boundary, not native generation or JWT authenticity.
    token = ".".join(
        (
            encode(json.dumps({"alg": "HS256"}).encode()),
            encode(json.dumps({"nbf": 1}).encode()),
            encode(b"x" * 32),
        )
    )
    prepared = {name: {"internal-token": token}}

    def plan():
        return declarative.plan_credentials(
            client,
            setups,
            definitions=definitions,
            prepared=prepared,
        )

    with pytest.raises(client_module.OpenBaoError):
        plan()
    snapshots["addons/forgejo/admin"] = client_module.SecretRecord(
        values={"adminPassword": secrets.token_urlsafe(32)},
        version=1,
    )
    first = plan().writes[0]
    snapshots[first.path] = client_module.SecretRecord(values=first.values, version=1)
    resumed = plan()
    assert first.path not in {write.path for write in resumed.writes}
    for write in resumed.writes:
        snapshots[write.path] = client_module.SecretRecord(values=write.values, version=1)
    assert not plan().writes
    assert snapshots["addons/forgejo/runtime"].values["internalToken"] == token
    readers = {
        reader.role: set(reader.records) for reader in declarative.compose_readers(setups)
    }
    assert readers["auth-keycloak"] == {"addons/forgejo/oidc"}
    assert readers["infra-postgres-operations"] == {"addons/forgejo/database"}
    assert readers["addon-forgejo-runtime"] == set(snapshots)
    assert "forgejo" not in readers
    handover = declarative.handover_definitions(setups, definitions)
    assert handover[0].definition == definitions[name]
    snapshots["addons/forgejo/runtime"].values["secretKey"] = "invalid"
    with pytest.raises(client_module.OpenBaoError):
        plan()
    client.write_secret.assert_not_called()
