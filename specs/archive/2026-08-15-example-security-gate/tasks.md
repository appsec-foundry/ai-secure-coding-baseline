# Tasks

- [x] Write `examples/claude-code-gate/gate.py` with the deny tier only.
- [x] Write `examples/claude-code-gate/settings.example.json`.
- [x] Write `examples/claude-code-gate/README.md`: install, denied list, what is
      left out, what a hook cannot see.
- [x] Write `examples/claude-code-gate/test_gate.py`: per-rule deny and allow
      samples, rule ids resolved against the baseline, the hook contract end to
      end.
- [x] Run the example test from `make check`.
- [x] Point at the example from the root `README.md` and record it under
      `specs/README.md` "What is enforced".
- [x] Run `make check`.
- [x] Run the affected model cases, or note why not.
- [x] Archive this directory.

The baseline is unchanged, so no model case is affected. `existing-pressure-tls-verify`
covers the same construct on the model side; the gate does not replace it and
neither changes what the case observes.
