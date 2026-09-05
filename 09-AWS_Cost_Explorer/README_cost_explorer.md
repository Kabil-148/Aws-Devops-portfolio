# AWS Cost Explorer Billing Report Generator

A Python script that pulls real AWS billing data from the AWS Cost Explorer API and generates a formatted PDF report covering a date range you choose.

## What is AWS Cost Explorer?

AWS Cost Explorer is AWS's built-in service for analyzing what you're spending and where it's going. It breaks down billing data by service, by day, by account, and by many other dimensions, and exposes that data through both the AWS Console and a programmatic API. This project uses that API (via Boto3) instead of the Console, so the same report can be generated on demand, on a schedule, or shared as a file — without anyone needing Console access.

## Why it's required

Cloud costs are easy to lose track of. Services like Lambda, KMS, data transfer, and "EC2 - Other" bill in small, easy-to-miss increments that only become visible once you look at a real breakdown — as seen in this project's own sample report, where AWS Key Management Service and Tax made up over 80% of total spend for the period, not EC2 itself.

Regularly generating a billing report — rather than only checking in when a bill looks unexpectedly high — is how teams catch cost creep early, attribute spend to the right service, and keep a paper trail for budgeting or compliance.

## The 5 things this report gives you

| # | Feature | Definition | Why we use it |
|---|---------|------------|----------------|
| 1 | Billing period | The exact start and end date the report covers. | Makes every report unambiguous about what time window the numbers represent. |
| 2 | Total AWS cost | The single summed cost across every service for the period. | Gives you the headline number before digging into detail. |
| 3 | Service-wise breakdown | Cost per individual AWS service (EC2, S3, RDS, KMS, Tax, etc.), sorted by spend. | Shows exactly where money is going, not just how much was spent overall. |
| 4 | Daily breakdown | Cost for each individual day in the range. | Reveals spikes or trends — e.g. a jump starting on a specific date — that a single total would hide. |
| 5 | Currency | The currency the amounts are reported in. | Prevents ambiguity when reports are shared across teams or regions. |

Together, these turn a single dollar figure on your AWS bill into an auditable, service-level, day-by-day account of what happened.

## Prerequisites

- Python 3.10+
- An AWS account with billing/cost activity in the period you want to query
- An IAM user or role with the `ce:GetCostAndUsage` permission
- AWS credentials configured on your machine (`aws configure`, environment variables, or a named profile)
- `boto3` and `reportlab` installed (`pip install -r requirements.txt`)

## ⚠️ Before you run this — read this first

This script **never stores AWS credentials in code**. It relies entirely on Boto3's standard credential chain, so nothing sensitive should ever end up in this repository. Before running it:

- Confirm you can already authenticate to AWS locally (`aws sts get-caller-identity` should return your account details).
- Confirm your IAM identity has `ce:GetCostAndUsage` — without it, every call fails with an AccessDenied error, not a code bug.
- Note that Cost Explorer bills a small fee per API call (roughly $0.01/request), and this script makes two calls per run.

## Usage

```bash
# Interactive mode — prompts for a start and end date
python aws_billing_report.py

# Pass dates directly
python aws_billing_report.py --start 2026-08-05 --end 2026-09-05

# Use a named AWS profile and a custom output filename
python aws_billing_report.py --start 2026-08-05 --end 2026-09-05 --profile myprofile --output report.pdf
```

The script prints a console summary, then saves a PDF named like:

```
aws_billing_report_2026-08-05_to_2026-09-05.pdf
```

## What the script does, step by step

1. **Set up inputs** — collects the billing date range (prompted or via flags) and resolves AWS credentials through Boto3, without any hardcoded secrets.
2. **Call Cost Explorer API** — makes two `get_cost_and_usage` calls: one grouped by `SERVICE` at monthly granularity (for the total and service breakdown), one at daily granularity (for the day-by-day trend).
3. **Aggregate results** — loops through `NextPageToken` for any paginated responses, summing costs and currency across pages so long date ranges are handled correctly.
4. **Build the report** — prints the total, service table, and daily table to the console, then hands the same data to `reportlab` to lay out a multi-page PDF.

## After running

- Open the generated PDF and confirm the billing period and currency match what you expected.
- If a service you know you're using shows $0.00, check whether it's simply under Cost Explorer's rounding threshold rather than assuming the report is wrong.
- Re-run any time with a new date range — there's no setup to repeat.

## Notes

- Cost Explorer is a global service always addressed via `us-east-1`, regardless of your default AWS region.
- Billing data can lag up to 24 hours, so very recent days may show as $0 or incomplete.
- The end date you provide is treated as inclusive — the script adjusts internally for Cost Explorer's exclusive `End` field.
- Never commit AWS credentials or generated PDF reports (they contain real cost data) to this repository — see `.gitignore`.

## License

Add a license of your choice (e.g. MIT) if you plan to share this publicly.
