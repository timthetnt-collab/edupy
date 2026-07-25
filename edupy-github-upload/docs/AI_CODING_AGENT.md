# AI Coding Agent

This project includes a GitHub Actions workflow that can run an AI coding agent in the cloud. It can work even when your PC is off because GitHub runs the workflow on its own servers.

## What It Does

The agent:

1. Reads a coding task.
2. Sends the task and a compact project snapshot to OpenAI.
3. Writes the changed files returned by the model.
4. Runs the test suite.
5. Opens a pull request with the changes.

The agent does not push directly to `main`. It creates a pull request so you can review the changes before merging.

## Setup

1. Push this project to GitHub.
2. In GitHub, open the repository settings.
3. Go to **Secrets and variables** > **Actions**.
4. Add a repository secret named `OPENAI_API_KEY`.
5. Put your OpenAI API key in that secret.
6. Open the **Actions** tab and enable workflows if GitHub asks.

## Manual Use

1. Go to the repository on GitHub.
2. Open **Actions**.
3. Select **AI Coding Agent**.
4. Click **Run workflow**.
5. Enter the task, such as:

```text
Add a mute button to the settings screen.
```

The workflow will create a new pull request if it produces code changes.

## Issue Comment Use

On any GitHub issue, comment with:

```text
/agent Add a restart button to the game over screen.
```

The agent will run from that comment and open a pull request if it makes changes.

## Limits

- The agent only receives a compact snapshot of text files, so very large files may be truncated.
- It does not edit binary files, databases, saves, backups, or cache folders.
- It does not delete files.
- If tests fail, the pull request step will not run.

## Recommended Workflow

Use small, specific tasks. Good examples:

- `Fix the quit button so it closes the app cleanly.`
- `Add tests for the reward calculation.`
- `Rename the leaderboard title to Class Rankings.`

Avoid broad tasks like:

- `Rewrite the whole game.`
- `Make everything better.`
- `Fix all bugs.`
