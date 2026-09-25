# How to Customize This Template With Claude or Another LLM

This folder contains starter files for building a private GitHub profile search workflow.

Do not run these files directly from this public template repository. They contain placeholder values and are intended to be customized before use.

The actual search should run only in a separate private GitHub repository.

## Step 1 — Copy the starter files

Copy the complete contents of the `starter-files/` folder:

```text
starter-files/
├── radar.py
├── profiles.csv
├── state.json
└── .github/
    └── workflows/
        └── radar.yml
```

You will provide these files to Claude or another LLM along with your search requirements.

## Step 2 — Describe your search requirements

Tell Claude or your preferred LLM what you want to search for.

Use requirements such as:

```text
Location: Austin, Texas
Programming language: Go
Minimum account age: 2 years
Minimum public repositories: 8
Recent general activity: within the last 4 months
Recent activity in the selected language: within the last 2 years
Additional requirements: exclude forks and inactive repositories
Timezone: America/Chicago
Schedule: twice per day
```

You can also describe a search that does not use location.

For example:

```text
Location: no location filter
Programming language: Python
Organization: profiles associated with a particular organization
Minimum public repositories: 10
Minimum followers: 50
Recent activity required: within the last 6 months
Additional requirements: require experience with a specific technology
Timezone: Europe/London
Schedule: once per day
```

Not every search needs to use every possible filter. Tell the LLM which filters are required and which should not be used.

## Step 3 — Ask Claude or another LLM to customize all files

Give the LLM the contents of:

- `radar.py`
- `profiles.csv`
- `state.json`
- `.github/workflows/radar.yml`

Ask it to customize the complete set of files for your search.

Use a request similar to this:

```text
Please customize these GitHub profile search starter files for my hiring search.

Use my requirements to update the Python script, CSV structure, workflow schedule, and initial state file.

Search requirements:
- Location: [insert location, or say "no location filter"]
- Programming language or technology: [insert requirement]
- Minimum account age: [insert requirement, or say "no minimum"]
- Minimum public repositories: [insert requirement, or say "no minimum"]
- Minimum followers: [insert requirement, or say "no minimum"]
- Recent general activity: [insert time period, or say "no activity requirement"]
- Recent activity in the selected language or technology: [insert time period, or say "no language activity requirement"]
- Organization, employer, topic, or other filter: [insert requirement, or say "none"]
- Location exclusions: [insert exclusions, or say "none"]
- Timezone: [insert timezone]
- Schedule: [insert schedule]

Please return the complete final contents of all four files:

1. radar.py
2. profiles.csv
3. state.json
4. .github/workflows/radar.yml

Important requirements:

- Do not include real candidate data.
- Keep the files suitable for use in a private GitHub repository.
- Do not leave placeholder values in the final files.
- Make sure the Python script and CSV columns match exactly.
- Make sure the workflow runs `radar.py` from the repository root.
- Use a valid UTC cron schedule in the GitHub Actions workflow.
- Explain any assumptions you had to make.
- Explain any GitHub API or rate-limit limitations.
- Tell me which filters were implemented and where they were implemented.
```

## Step 4 — Ask the LLM to adjust the CSV columns

The starter `profiles.csv` contains this default header:

```csv
login,full_name,github_url,location,company,blog,

