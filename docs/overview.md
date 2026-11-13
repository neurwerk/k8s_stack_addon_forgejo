# Forgejo add-on

This add-on packages Forgejo with Keycloak sign-in, PostgreSQL, TLS, network isolation, and persistent repository storage.

## Integration

`release/manifest.yaml` defines prerequisites, packages, images, identity approvals, and credential delivery. Clients select the immutable source as `forgejo-addon` and supply their hostname, access approvals, and product settings. The add-on uses shared Base charts for database and identity provisioning.

The tooling package stages the native bootstrap payload; Forgejo executes it using its pinned application image. Tooling images are public and require no pull credentials. Native password login is disabled unless recovery login is explicitly enabled.

## Development

Run `make check BASE_REPO=/path/to/reviewed/base` with the Base revision selected in `.github/workflows/ci.yml`. Build tooling with `make tooling-build VERSION=<version> REVISION=<commit>`.

## Operations

Use shared `stack-setup` with the selected add-on definitions to prepare credentials. Apply namespace and secret delivery packages before database, identity, certificates, and application packages. Database, volume, and credential retention is the default; uninstalling workloads does not authorize data deletion.

Tooling releases use `tooling/v<version>`. Verify the published image digest and anonymous pulls before updating the manifest and chart pins. A new GHCR package requires its administrator to set visibility to Public.
