"""Search Google Jobs and save the results to a CSV file.

    pip install apify-client
    export APIFY_TOKEN=your-token        # Windows: set APIFY_TOKEN=your-token
    python examples/search_jobs.py
"""

import csv
import os

from apify_client import ApifyClient

QUERY = "data analyst chicago"  # what you would type into Google, including the location

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("ralfij/google-jobs-scraper").call(
    run_input={
        "queries": [QUERY],
        "maxJobsPerQuery": 50,
        "datePosted": "week",  # any, today, week or month
        "country": "us",
    }
)
jobs = list(client.dataset(run.default_dataset_id).iterate_items())

for job in jobs[:15]:
    print(f"{job['title'][:45]:<45}  {(job['companyName'] or '')[:25]:<25}  {job['salary'] or '-'}")
print(f"\n{len(jobs)} jobs found")

with open("jobs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["title", "company", "location", "posted_date", "schedule", "salary_min", "salary_max", "currency", "period", "apply_url"])
    for job in jobs:
        apply_url = job["applyOptions"][0]["url"] if job["applyOptions"] else job["googleJobUrl"]
        writer.writerow([
            job["title"], job["companyName"], job["location"], job["postedDate"], job["scheduleType"],
            job["salaryMin"], job["salaryMax"], job["salaryCurrency"], job["salaryPeriod"], apply_url,
        ])
print("Saved jobs.csv")
