# Tasks

- [x] IDENT-PREFIX-001: rename the rule group IDs, the risk heading, and the
      baseline ID in `secure-coding-baseline.md` to `AISCB` and
      `aiscb-0.1.10`.
- [x] IDENT-PREFIX-001: follow the rename in `specs/requirements.md`, the rule
      index in `README.md`, `tests/README.md`, the `checks.json` of every
      affected case, and the fixtures in `tests/test_selfcheck.py`.
- [x] IDENT-PREFIX-001: set `OFFICIAL_NAME` in `scripts/install.py` to `aiscb`
      and check the release-tag rule that derives from it. Installed file names
      keep their old spelling, because renaming one orphans an existing
      installation; `tests/results/` keeps what the models actually answered.
- [x] IDENT-SOURCE-001: add the source and license line after the baseline ID.
- [x] IDENT-SOURCE-001: recompute size and token count of the baseline with the
      `o200k_base` encoding and update both values and the stated budget in
      `README.md`: 20.2 KB, 4,018 tokens, budget 4,100.
- [x] Run `make check`.
- [x] Run the model cases this change affects, or record here why not. Not run:
      the change relabels rule IDs and adds a metadata line, so no rule text
      changed for a model to behave differently on, and the full matrix costs
      hours and real tokens. The deterministic checks cover that every case and
      catalog entry names a defined ID.
- [ ] Publish a release carrying `aiscb-0.1.10`, without which the installer's
      online check falls back to the bundled copy.
