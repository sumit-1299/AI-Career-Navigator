# Live jobs: selected Greenhouse employer boards

The Career Navigator retrieves selected public employer postings directly from
Greenhouse at request time.

The application does not maintain an operational vacancy cache.

## Architecture

```text
Greenhouse public board
        ↓
Live provider fetch
        ↓
Validation + normalization
        ↓
Live job response
        ↓
Browser