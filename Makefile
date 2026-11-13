SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := check
TOOLING ?= uv run --locked --project tooling
TOOLING_IMAGE := ghcr.io/neurwerk/k8s-stack-addon-forgejo-tooling
CHART_DIRS := $(sort $(shell find charts -name Chart.yaml -exec dirname {} \;))

.PHONY: check tooling-check tooling-build
tooling-check:
	$(TOOLING) ruff check --config tooling/pyproject.toml tooling
	$(TOOLING) ruff format --check --config tooling/pyproject.toml tooling
	$(TOOLING) ty check --project tooling
	BASE_REPO="$(BASE_REPO)" $(TOOLING) pytest tooling/tests

tooling-build:
	@test -n "$(VERSION)" -a -n "$(REVISION)" || { echo 'Set VERSION and REVISION for image metadata'; exit 1; }
	docker build --build-arg VERSION="$(VERSION)" --build-arg REVISION="$(REVISION)" -t "$(TOOLING_IMAGE):$(VERSION)" tooling

check: tooling-check
	@test -n "$(BASE_REPO)" || { echo 'Set BASE_REPO to the exact selected Base checkout'; exit 1; }
	$(TOOLING) forgejo-validate "$(CURDIR)"
	$(TOOLING) addon-check "$(CURDIR)" --base "$(BASE_REPO)"
	@for chart in $(CHART_DIRS); do \
		helm lint --strict "$$chart" --values tests/validation/helm-lint-values.yaml; \
		helm template test "$$chart" --values tests/validation/helm-lint-values.yaml | kubeconform -strict -summary -ignore-missing-schemas; \
	done
	@packages="$$($(TOOLING) forgejo-validate "$(CURDIR)" --list-packages)"; \
	for package in $$packages; do \
		kustomize build --load-restrictor LoadRestrictionsNone "$$package" | kubeconform -strict -summary -ignore-missing-schemas; \
	done
	@BASE_REPO="$(BASE_REPO)" PYTHONPATH=tests/charts $(TOOLING) python -m unittest discover -s tests/charts -p 'test_*.py'
