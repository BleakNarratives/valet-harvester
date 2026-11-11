# Failure modes observed in agent output

Real patterns from 18 months of coding-agent use. The building agent for
this repo must not exhibit any of them.

## Fabrication

- Echoing expected output as if it were a real test result.
- Writing a test that only checks compilation, then calling it tested.
- Using a template, placeholder, or example response as live data.
- Hitting a fake endpoint and presenting the response as real.
- `assert True` or equivalent, called verification.
- Claiming a key is valid without a real HTTP 200 from the provider.
- Claiming a UI launched without the child process actually running.
- Saying tested and it works with no command output pasted.

## Drift and scope creep

- Saying I will now do X, then doing Y.
- While I was in there, I also refactored Z without being asked.
- Re-architecting the spec instead of implementing it.
- Adding features not in the acceptance tests.
- Single-line strings longer than 120 chars (user cannot verify them).
- Shell heredocs (user cannot review before running).

## Silent failures

- Keys injected via env vars that the child ignores in favor of its own
  inline config (opencode does this).
- Hardcoded values passed as dynamic data.
- Fake endpoints used as real sources or targets.
- Templates used as payloads or query results.
- Echo/print switcharoos.
- Saved output or session dumps replayed as fresh runs.

## Proof standard

Every claim in the final report must cite the actual command and output
that proves it. If the output cannot be pasted, the claim is not made.
Good example: run `bin/valet bash -c env` and paste the output showing key
lengths. Bad example: say the valet works without pasting output.
