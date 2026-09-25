# GitHub Search Template

A public starter template for building a private GitHub Actions workflow that searches public GitHub profiles by your chosen parameters (location, programming language, account age, repository activity and other custom filters)

This repository is not a live search. It is a safe template that recruiters can copy, adapt with Claude (or your LLM of choice) and move into their own private repository for their own hiring search.

The goal is simple: keep the public template generic and safe, while letting each recruiter customize the search for their own market, stack and hiring criteria.

## How this works

1. Open the `starter-files/` folder in this repository.
2. Copy its contents.
3. Follow the instructions in `CLAUDE-INSTRUCTIONS.md` to have Claude adapt the files to your own location, programming language, and filters.
4. Create a new **private** repository for your own search.
5. Add Claude's customized files to that private repository.
6. Run the workflow once manually to confirm it works.
7. Let the schedule take over from there.

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

The workflow file is intentionally placed inside `starter-files/.github/workflows/` rather than at the repository root. This prevents it from running automatically inside this public template repository.

## Why use a private repository for your search

- Your search criteria may reflect confidential hiring plans.
- Any profiles found should be reviewed privately, not published publicly.
- A private repository keeps your results and configuration secure while this template remains public and reusable.

## What you can customize

- Locations (city, region, state, or country)
- Programming language
- Minimum account age
- Minimum number of public repositories
- Required recent activity window
- Any other parameters that meet your ideal profile candidate
- Recheck interval for already-processed profiles
- Timezone
- Run schedule

## Responsible use

This template processes only publicly available GitHub profile information.

Before using it:

- Follow GitHub's Terms of Service and API usage requirements.
- Follow applicable privacy and data-protection laws.
- Collect only the information necessary for your purpose.
- Treat automated results as a starting point for human review, not a final decision.
- Define a reasonable data-retention period.
- Respect any request to correct or remove information.

## License

This template is provided under the MIT License. See `LICENSE` for details.
