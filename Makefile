# Free targets first. Anything that calls a model costs tokens and hours,
# so the expensive targets run the free self-check before spending anything.

.DEFAULT_GOAL := check
.PHONY: check install install-claude install-codex install-copilot \
        dry-run test test-all clean-results help

## check       validate the suite itself: no model calls, seconds
check:
	python3 tests/selfcheck.py
	python3 tests/test_selfcheck.py
	python3 examples/claude-code-gate/test_gate.py
	python3 scripts/test_spec_guard.py
	python3 scripts/test_install.py

## install     link the baseline where every supported tool reads it
##             ARGS=--user installs for this machine instead of the project
install:
	python3 scripts/install.py $(ARGS)

## install-claude, install-codex, install-copilot  one tool only
install-claude install-codex install-copilot:
	python3 scripts/install.py $(@:install-%=%) $(ARGS)

## dry-run     print the run matrix without spending anything
dry-run:
	python3 tests/run.py --dry-run $(ARGS)

## test        every case, both arms, Claude — the single full run
test: check
	python3 tests/run.py $(ARGS)

## test-all    same across Claude and Codex; sequential, because Codex
##             resumes sessions process-wide and multi-turn cases would collide
test-all: check
	python3 tests/run.py --tools claude,codex --parallel 1 $(ARGS)

## clean-results  delete previous reports
clean-results:
	rm -rf tests/results

## help        this list
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //'
