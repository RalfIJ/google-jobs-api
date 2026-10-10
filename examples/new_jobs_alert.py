"""Show only the Google Jobs postings you haven't seen before. Run it once a day.

It remembers the jobs it has shown in seen_jobs.json. Set SLACK_WEBHOOK_URL to also post
the new jobs to a Slack channel (see https://api.slack.com/messaging/webhooks).

    pip install apify-client requests
    export APIFY_TOKEN=your-token        # Windows: set APIFY_TOKEN=your-token
    python examples/new_jobs_alert.py

To run it every morning, use cron, Windows Task Scheduler or a scheduled GitHub Action.
"""

import json
import os
from pathlib import Path

import requests
from apify_client import ApifyClient

QUERIES = ["python developer remote", "data engineer new york"]
SEEN_FILE = Path("seen_jobs.json")

seen = set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("ralfij/google-jobs-scraper").call(
    run_input={
        "queries": QUERIES,
        "maxJobsPerQuery": 50,
        "datePosted": "today",  # posted in the past 24 hours
        "includeDescription": False,
    }
)

lines = []
for job in client.dataset(run.default_dataset_id).iterate_items():
    if job["jobId"] in seen:
        continue
    seen.add(job["jobId"])
    link = job["applyOptions"][0]["url"] if job["applyOptions"] else job["googleJobUrl"]
    salary = f" | {job['salary']}" if job["salary"] else ""
    lines.append(f"{job['title']} at {job['companyName'] or '?'} ({job['location'] or '?'}){salary}\n{link}")

print(f"{len(lines)} new jobs\n")
print("\n\n".join(lines))

webhook = os.environ.get("SLACK_WEBHOOK_URL")
if webhook and lines:
    text = f"{len(lines)} new jobs on Google Jobs\n\n" + "\n\n".join(lines[:30])
    requests.post(webhook, json={"text": text}, timeout=30).raise_for_status()

SEEN_FILE.write_text(json.dumps(sorted(seen)))
