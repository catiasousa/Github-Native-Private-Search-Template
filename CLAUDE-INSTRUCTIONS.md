# How to Customize This Template With Claude

This folder contains starter files for a GitHub profile search automation.

Do not run these files as-is. They contain placeholder values.

## Step 1 — Copy the starter files

Copy the entire contents of the `starter-files/` folder.

## Step 2 — Give Claude your search requirements

Paste the contents of `radar.py` and `radar.yml` into Claude, along with a description of your search, for example:

```text
Location: Austin, Texas
Programming language: Go
Minimum account age: 2 years
Minimum public repos: 8
Recent activity required: within the last 4 months
Timezone: America/Chicago
Schedule: twice per day
```

## Step 3 — Ask Claude to update the files

Ask Claude to:

- Replace the placeholder `LOCATIONS` list with your locations.
- Replace `SEARCH_LANGUAGE` with your programming language.
- Adjust `MIN_ACCOUNT_AGE_YEARS`, `MIN_PUBLIC_REPOS`, `ACTIVE_WITHIN_DAYS`, and `LANGUAGE_WITHIN_DAYS` to match your requirements.
- Replace the `timezone` value in the workflow file.
- Adjust the `cron` schedule if needed.

## Step 4 — Create your own private repository

1. Create a new **private** GitHub repository.
2. Add Claude's updated `radar.py` to the repository root.
3. Add Claude's updated `radar.yml` to `.github/workflows/radar.yml`.
4. Add an empty `profiles.csv` with only the header row.
5. Add an empty `state.json` containing `{"checked": {}}`.
6. Commit everything to the default branch.

## Step 5 — Run it once manually

1. Open your private repository's **Actions** tab.
2. Select the workflow.
3. Click **Run workflow**.
4. Confirm the run succeeds.

## Step 6 — Let it run on schedule

Once the manual run succeeds, the workflow will run automatically according to the schedule you configured.

## Important

- Never run these files directly from this public template repository.
- Keep your adapted files in a private repository.
- Review GitHub's API rate limits and Actions usage documented in `README.md`.
