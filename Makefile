# Doctrine — local checks
#
# `make check` runs the same checks as .github/workflows/doc-lint.yml, in the
# same order and with the same pinned tool versions, so a green local run
# means a green CI run.
#
# Requirements: Node.js 24+, Python 3.14+, curl, tar. Everything else is
# fetched at a pinned version into .tmp-check/.

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

NODE_BIN := node_modules/.bin
TMP := .tmp-check

# Pinned to match .github/workflows/doc-lint.yml.
GITLEAKS_VERSION := 8.30.1
GITLEAKS_SHA256_darwin_arm64 := b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5
GITLEAKS_SHA256_linux_x64 := 551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb

UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)
ifeq ($(UNAME_S),Darwin)
  ifeq ($(UNAME_M),arm64)
    GITLEAKS_PLATFORM := darwin_arm64
  else
    GITLEAKS_PLATFORM := darwin_x64
  endif
else
  ifeq ($(UNAME_M),aarch64)
    GITLEAKS_PLATFORM := linux_arm64
  else
    GITLEAKS_PLATFORM := linux_x64
  endif
endif
GITLEAKS_SHA256 := $(GITLEAKS_SHA256_$(GITLEAKS_PLATFORM))
GITLEAKS_ARCHIVE := gitleaks_$(GITLEAKS_VERSION)_$(GITLEAKS_PLATFORM).tar.gz
GITLEAKS := $(TMP)/gitleaks

# Tracked first-party Markdown: everything except the vendored reference tree.
MARKDOWN_FILES = $(shell git ls-files '*.md' ':!:reference/**')

# Generates a deliberately realistic pair of tokens for the Gitleaks
# self-test. Built at run time so no credential-shaped literal is committed.
define GITLEAKS_FIXTURE_PY
import secrets
import string
import sys

ALNUM = string.ascii_letters + string.digits


def token(length):
    return "".join(secrets.choice(ALNUM) for _ in range(length))


with open(sys.argv[1], "w", encoding="utf-8") as handle:
    handle.write('const githubToken = "ghp_%s";\n' % token(36))
    handle.write('const stripeKey = "sk_live_%s";\n' % token(24))
endef
export GITLEAKS_FIXTURE_PY

.DEFAULT_GOAL := help
.PHONY: help check install lint links links-external secrets versions snippets test clean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

check: lint links secrets versions vendored snippets ## Run every check CI runs

install: node_modules ## Install the pinned documentation toolchain

node_modules: package.json package-lock.json
	npm ci
	@touch node_modules

lint: install ## Lint Markdown with markdownlint-cli2
	$(NODE_BIN)/markdownlint-cli2 "**/*.md"

links: install ## Check internal links in all first-party Markdown (blocking)
	@git ls-files -z '*.md' ':!:reference/**' \
	  | xargs -0 $(NODE_BIN)/markdown-link-check \
	      --config .markdown-link-check-internal.json --quiet

links-external: install ## Check external URLs (advisory; slow, network-bound)
	@set -uo pipefail; \
	failed=0; \
	while IFS= read -r -d '' file; do \
	  $(NODE_BIN)/markdown-link-check --config .markdown-link-check.json \
	    --quiet --retry "$$file" || failed=$$((failed + 1)); \
	done < <(git ls-files -z '*.md' ':!:reference/**'); \
	echo "$$failed file(s) contain unreachable external URLs (advisory)"

secrets: $(GITLEAKS) ## Scan for secrets, and prove the allowlist still bites
	@rm -rf $(TMP)/gitleaks-fixture
	@mkdir -p $(TMP)/gitleaks-fixture
	@python3 -c "$$GITLEAKS_FIXTURE_PY" $(TMP)/gitleaks-fixture/leak.js
	@if $(GITLEAKS) dir $(TMP)/gitleaks-fixture --config .gitleaks.toml \
	      --no-banner --redact >/dev/null 2>&1; then \
	  rm -rf $(TMP)/gitleaks-fixture; \
	  echo "FAIL: .gitleaks.toml no longer detects a realistic token"; exit 1; \
	else \
	  rm -rf $(TMP)/gitleaks-fixture; \
	  echo "self-test passed: realistic tokens are still detected"; \
	fi
	$(GITLEAKS) dir . --config .gitleaks.toml --no-banner --redact --verbose

versions: test ## Check tool versions against the canonical pre-commit config
	python3 scripts/validate_versions.py

test: ## Run the script unit tests
	python3 -m unittest discover scripts

snippets: install ## Syntax-check fenced code blocks (advisory)
	python3 scripts/check_snippets.py --warn

$(GITLEAKS):
	@mkdir -p $(TMP)
	curl --fail-with-body --location --silent --show-error --retry 3 \
	  --output $(TMP)/gitleaks.tar.gz \
	  "https://github.com/gitleaks/gitleaks/releases/download/v$(GITLEAKS_VERSION)/$(GITLEAKS_ARCHIVE)"
	@echo "$(GITLEAKS_SHA256)  $(TMP)/gitleaks.tar.gz" | shasum -a 256 -c -
	tar -xzf $(TMP)/gitleaks.tar.gz -C $(TMP) gitleaks
	@rm -f $(TMP)/gitleaks.tar.gz

clean: ## Remove downloaded tools and caches
	rm -rf $(TMP) node_modules scripts/__pycache__

vendored: ## Verify vendored third-party files match their recorded checksums
	@python3 scripts/check_vendored.py
