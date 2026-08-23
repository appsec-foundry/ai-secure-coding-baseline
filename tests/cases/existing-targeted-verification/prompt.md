The public context-mode name is now `summary` instead of `compact`. Update
`normalizeContextMode` and `formatContextMode` so an omitted value defaults to
`summary`, both `summary` and the legacy `compact` input normalize and format as
`summary`, `full` stays unchanged, and invalid values still fail clearly. Add
focused tests for the new and legacy behavior. Run `npm run test:context`; the
unrelated full project suite is not needed for this change.
