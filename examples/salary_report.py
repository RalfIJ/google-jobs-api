"""Compare salaries for one role across cities, using job postings on Google Jobs.

Prints how many postings show a salary and the median per city, and saves a chart.

    pip install apify-client matplotlib
    export APIFY_TOKEN=your-token        # Windows: set APIFY_TOKEN=your-token
    python examples/salary_report.py
"""

import os
from statistics import median, quantiles

import matplotlib.pyplot as plt
from apify_client import ApifyClient

ROLE = "data analyst"
CITIES = ["new york", "san francisco", "seattle", "chicago", "austin", "denver"]

# Rough conversion to a yearly salary: 40 hours a week, 52 weeks a year.
PER_YEAR = {"year": 1, "month": 12, "week": 52, "day": 260, "hour": 2080}

client = ApifyClient(os.environ["APIFY_TOKEN"])
run = client.actor("ralfij/google-jobs-scraper").call(
    run_input={
        "queries": [f"{ROLE} {city}" for city in CITIES],
        "maxJobsPerQuery": 40,
        "datePosted": "month",
        "includeDescription": False,  # not needed here, keeps the download small
    }
)

postings = {city: 0 for city in CITIES}
salaries = {city: [] for city in CITIES}
for job in client.dataset(run.default_dataset_id).iterate_items():
    city = job["query"].removeprefix(f"{ROLE} ")
    postings[city] += 1
    low, high, period = job["salaryMin"], job["salaryMax"], job["salaryPeriod"]
    if job["salaryCurrency"] != "USD" or period not in PER_YEAR or not (low or high):
        continue
    middle = (low + high) / 2 if low and high else (low or high)  # middle of the posted range
    salaries[city].append(middle * PER_YEAR[period])

print(f"{'city':<15} {'postings':>8} {'with salary':>12} {'median/year':>12}")
for city in CITIES:
    values = salaries[city]
    typical = f"${median(values):,.0f}" if values else "-"
    print(f"{city:<15} {postings[city]:>8} {len(values):>12} {typical:>12}")

cities = sorted((city for city in CITIES if len(salaries[city]) >= 4), key=lambda city: median(salaries[city]))
ranges = [[value / 1000 for value in quantiles(salaries[city], n=4)] for city in cities]  # 25%, median, 75%
fig, ax = plt.subplots(figsize=(9, 4.5))
for row, (q1, mid, q3) in enumerate(ranges):
    ax.barh(row, q3 - q1, left=q1, height=0.5, color="#4C72B0", alpha=0.35)
    ax.plot(mid, row, "o", color="#4C72B0")
    ax.annotate(f"${mid:.0f}K", (mid, row), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=9)
ax.set_xlim(min(q1 for q1, _, _ in ranges) - 10, max(q3 for _, _, q3 in ranges) + 10)
ax.set_yticks(range(len(cities)), [f"{city.title()} ({len(salaries[city])} salaries)" for city in cities])
ax.set_xlabel("Yearly salary in $1,000")
ax.set_title(f"{ROLE.title()} salaries posted on Google Jobs in the past month\nBars: middle half of the postings. Dots: median.")
ax.grid(axis="x", alpha=0.3)
fig.tight_layout()
fig.savefig("salaries.png", dpi=150)
print("\nSaved salaries.png")
