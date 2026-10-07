# Live Tech Job Search

The job search is now a **tech-only live retrieval layer**. The application does not keep a shared cache of live vacancies. A listing is fetched from its public employer/provider feed when the user searches, opens a role, or compares a role.

## Public provider feeds

### Greenhouse
- Canonical
- Razorpay

### Ashby
- Notion
- Vercel
- Linear
- Ramp

Ashby documents a public Job Postings API at `https://api.ashbyhq.com/posting-api/job-board/{JOB_BOARD_NAME}` and returns published postings with fields such as title, location, job URL, employment type, workplace type and description. The public board name is the final part of the employer's Ashby hosted job-board URL.

### Lever
- Dun & Bradstreet (`dnb`)
- Spreetail (`spreetail`)
- Zūm (`ridezum`)

Lever documents a publicly accessible Postings API for published job postings. The prototype uses the public v0 JSON feed for each configured company board.

## Tech-only policy

The search layer uses transparent heuristics over the job title, description, department and team. It explicitly excludes obvious nontechnical families such as sales, recruiting, finance, marketing, HR, legal, customer support and similar functions. A technical job may still be rejected when its title clearly belongs to an excluded business function.

This is a prototype filtering policy, not a perfect occupational classifier. The UI therefore describes it as **technology-focused vacancies** rather than making a claim that every posting is perfectly classified.

## Location and search

Users can filter by:
- keyword / role / technology
- location
- technology tag
- work mode
- experience level
- employer/source

Location filters include secondary locations when a provider supplies them.

## Comparison snapshots

When a candidate compares a live posting, the exact job title, description, provider identifier, source URL, provider timestamp, content hash, location and classification metadata are saved in the immutable JobComparison snapshot. The live provider feed itself is not persisted as a shared cache.

The research workflow remains:

`Find tech job → location → align evidence → identify gaps → practical task → assessment → re-align → apply`

## Operational notes

The provider list is deliberately explicit. This makes source health visible in the UI and avoids pretending that an unavailable provider is still live. Providers can be expanded later by adding another adapter and source configuration rather than changing the comparison model.
