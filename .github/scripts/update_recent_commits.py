"""Update the recent public commits section in the profile README."""

import json
import os
import re
import urllib.request
from pathlib import Path

README = Path("README.md")
START_MARKER = "<!--RECENT_COMMITS:START-->"
END_MARKER = "<!--RECENT_COMMITS:END-->"
MAX_COMMITS = 5


def fetch_recent_commits():
    username = os.environ.get("GITHUB_REPOSITORY_OWNER", "joaosantos86")
    url = f"https://api.github.com/users/{username}/events/public?per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-readme-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        events = json.load(response)

    commits = []
    for event in events:
        if event["type"] != "PushEvent":
            continue

        repository = event["repo"]["name"]
        for commit in reversed(event["payload"].get("commits", [])):
            message = commit["message"].splitlines()[0]
            sha = commit["sha"]
            commit_url = f"https://github.com/{repository}/commit/{sha}"
            repository_url = f"https://github.com/{repository}"
            commits.append(
                f"- [`{sha[:7]}`]({commit_url}) {message} — "
                f"[{repository}]({repository_url})"
            )

            if len(commits) == MAX_COMMITS:
                return commits

    return commits


def update_readme():
    commits = fetch_recent_commits()
    activity = "\n".join(commits) if commits else "No recent public commits found."
    content = README.read_text(encoding="utf-8")
    pattern = re.compile(f"({re.escape(START_MARKER)}).*?({re.escape(END_MARKER)})", re.DOTALL)
    updated_content, replacements = pattern.subn(
        lambda match: f"{match[1]}\n{activity}\n{match[2]}", content
    )

    if replacements != 1:
        raise RuntimeError("The README must contain one recent commits section.")

    if updated_content != content:
        README.write_text(updated_content, encoding="utf-8")
        print("Recent commits updated.")
    else:
        print("Recent commits are already up to date.")


if __name__ == "__main__":
    update_readme()
