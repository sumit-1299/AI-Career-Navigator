# Final sprint fix

This bundle fixes the two real blockers shown during the 129-test run:

1. Password reset expiry comparison: SQLite can materialize timezone-aware DateTime columns as naive UTC datetimes. The reset route now normalizes expires_at to UTC before comparison.
2. Live multi-source tests: the jobs API requires JWT authentication, so the two tests now send the authenticated test headers.

Do not change the live-job authentication policy just to make these tests pass.
