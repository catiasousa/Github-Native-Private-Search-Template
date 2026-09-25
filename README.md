# GitHub Search Template

A public starter template for building a private GitHub Actions workflow that searches public GitHub profiles using chosen parameters such as location, programming language, account age, repository activity, and other custom filters.

This repository is not a live search. It is a safe template that recruiters can copy, adapt with Claude or another LLM, and move into their own private repository for their own hiring search.

The goal is simple: keep the public template generic and safe while allowing each recruiter to customize the search for their own market, technology stack, and hiring criteria.

## How this works

1. Open the `starter-files/` folder in this repository.
2. Copy all of its contents.
3. Give the starter files and your search requirements to Claude or another LLM.
4. Ask the LLM to customize the search logic, filters, CSV columns, and workflow schedule.
5. Create a separate **private** GitHub repository for your search.
6. Move the customized files into the correct locations in that private repository.
7. Run the workflow once manually to confirm that it works.
8. Let the workflow run automatically according to its schedule.

## What's inside this template

```text
github-search-template/
├── README.md
├── CLAUDE-INSTRUCTIONS.md
├── LICENSE
└── starter-files/
    ├── radar.py
    ├── profiles.csv
    ├── state.json
    └── .github/
        └── workflows/
            └── radar.yml
```

The workflow file is intentionally placed inside:

```text
starter-files/.github/workflows/radar.yml
```

rather than at the root of this public repository. This prevents the public template from running as a live search.

When the files are moved into a private repository, the private repository must use this structure:

```text
your-private-search/
├── radar.py
├── profiles.csv
├── state.json
└── .github/
    └── workflows/
        └── radar.yml
```

The workflow must be located at `.github/workflows/radar.yml` in the private repository for GitHub Actions to recognize and run it.

## What you can customize

You can adapt the template for searches based on criteria such as:

- Location, region, country, or no location filter
- Programming language or technology
- Minimum account age
- Minimum number of public repositories
- Minimum follower count
- Recent repository activity
- Activity in a specific programming language
- Repository topics or organization
- Fork or non-fork repository requirements
- Location exclusions
- Recheck interval for previously processed profiles
- Timezone
- Run schedule
- CSV columns and recruiter tracking fields

Not every search needs to use every filter. For example, a recruiter may want to search by programming language and activity without filtering by location.

The LLM should update the search logic and the CSV structure together. The CSV header must match the data collected and written by `radar.py`.

## Why use a private repository for your search

- Search criteria may reflect confidential hiring plans.
- Matching profiles should be reviewed privately.
- Candidate-related notes and contact status should not be published.
- Search results and processing state should remain private.
- The public repository can remain generic and reusable.

The public template should contain:

- No real candidate profiles
- No search results
- No recruiter-specific hiring requirements
- No populated `state.json` data
- No active workflow at the repository root

## Responsible use

This template processes publicly available GitHub profile and repository information only.

Before using it:

- Follow GitHub's Terms of Service and API usage requirements.
- Respect applicable privacy and data-protection laws.
- Collect only the information necessary for your purpose.
- Keep the actual search and results in a private repository.
- Treat automated results as a starting point for human review, not as final hiring decisions.
- Define a reasonable data-retention period.
- Respect requests to correct or remove information.
- Review the generated code before running it.

## License

This template is provided under the MIT License. See `LICENSE` for details.
