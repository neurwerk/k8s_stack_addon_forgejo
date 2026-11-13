# neurwerk.base - Forgejo Add-on

Forgejo repository hosting with Keycloak sign-in, PostgreSQL, TLS, and persistent storage, packaged as an optional add-on to [neurwerk.base](https://base.neurwerk.com/).

## Stack

| Repository | Purpose |
| --- | --- |
| [Base](https://github.com/neurwerk/k8s_stack_base) | Shared platform charts and release packages. |
| [Studio](https://github.com/neurwerk/k8s_stack_studio) | Platform dashboard and API. |
| [Tooling](https://github.com/neurwerk/k8s_stack_tooling) | Setup automation, operational tools, and operations image. |
| [PII Engine](https://github.com/neurwerk/k8s_stack_pii_engine) | Personal-information detection and safety policies. |
| [Gateway Processor](https://github.com/neurwerk/k8s_stack_agentgateway_extproc) | Connects gateway traffic to the PII Engine. |
| [API Key Bridge](https://github.com/neurwerk/k8s_stack_keycloak_api_key_bridge) | Issues and validates API keys using Keycloak permissions. |
| [Keycloak Theme](https://github.com/neurwerk/k8s_stack_keycloak_theme) | Keycloak login and email themes. |

## Add-ons

Optional products are packaged separately from Base. See each repository's documentation and release manifest for availability and prerequisites.

| Repository | Purpose |
| --- | --- |
| [Dify](https://github.com/neurwerk/k8s_stack_addon_dify) | Dify deployment and API/web customizations. |
| [Forgejo](https://github.com/neurwerk/k8s_stack_addon_forgejo) | Forgejo deployment and platform integration. **(this repository)** |
| [LibreChat](https://github.com/neurwerk/k8s_stack_addon_librechat) | LibreChat deployment and platform integration. |
| [Open WebUI](https://github.com/neurwerk/k8s_stack_addon_open_webui) | Open WebUI deployment and platform integration. |
| [Pipecat](https://github.com/neurwerk/k8s_stack_addon_pipecat) | Self-hosted voice bots and browser UI with platform identity and AI gateway integration. |

## Examples

| Repository | Purpose |
| --- | --- |
| [Example Client](https://github.com/neurwerk/k8s_stack_client_example_com) | Example client settings and Flux deployment setup. |

## Documentation

See [Repository documentation](docs/overview.md) and the [release manifest](release/manifest.yaml).

## Contributing and support

Use [GitHub Issues](https://github.com/neurwerk/k8s_stack_addon_forgejo/issues) for reproducible bugs and focused feature requests; run `make check` before proposing changes.

## Security

Report vulnerabilities privately through [GitHub security advisories](https://github.com/neurwerk/k8s_stack_addon_forgejo/security/advisories/new).

## Licensing

Project-owned content uses the [MIT License](LICENSE). Forgejo itself retains its [upstream license](https://code.forgejo.org/forgejo/forgejo/src/branch/forgejo/LICENSE).
