# Requirements

## BASELINE-VERSION-001 Use Semantic Versioning

Source: the user's explicit request in this conversation to use SemVer for the
baseline identifier.

The version component of a baseline identifier must use Semantic Versioning.
The current baseline must identify itself as `aisec-0.1.0`; prerelease and
build metadata remain available for candidate releases and derived baselines.

Acceptance: the normative baseline declares `aisec-0.1.0`, the README documents
the three-part format and matching examples, and the deterministic self-check
rejects malformed or mismatched identifiers.

## BASELINE-VERSION-002 Version every normative revision

Source: the version policy proposed in this conversation and explicitly
approved by the user.

Every change to the normative baseline text must increase its version by at
least a patch. During the `0.x` beta, additions, removals, and material changes
to rule behavior must increase the minor version; after `1.0.0`, incompatible
changes must increase the major version. Repository-only changes do not change
the baseline version.

Acceptance: the README states when patch, minor, and major components change
and distinguishes normative changes from repository-only changes.
