# Free targets first. Anything that calls a model costs tokens and hours,
# so the expensive targets run the free self-check before spending anything.

.DEFAULT_GOAL := check
.PHONY: check coverage setup update status install install-claude install-codex \
        install-copilot dry-run test test-all clean-results help

# Both check and coverage run this suite, so it is listed once.
CHECK_TESTS = tests/selfcheck.py \
              tests/test_selfcheck.py \
              tests/test_run.py \
              examples/claude-code-gate/test_gate.py \
              scripts/test_spec_guard.py \
              scripts/test_show_baseline_version.py \
              scripts/test_install.py

## check       validate the suite itself: no model calls, seconds
check:
	@set -e; for t in $(CHECK_TESTS); do echo "python3 $$t"; python3 $$t; done

## coverage    statement coverage of the check suite; needs the coverage package
##             ARGS=--xml=coverage.xml also writes a report for CI upload
coverage:
	python3 scripts/coverage_report.py $(ARGS) $(CHECK_TESTS)

## setup       guided install and update; ARGS=--offline skips the release check
setup:
	python3 scripts/install.py --interactive $(ARGS)

## update      guided update; uses the same safe flow as setup
update: setup

## status      show installed baseline status; ARGS=--offline skips release check
status:
	python3 scripts/install.py --status $(ARGS)

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
