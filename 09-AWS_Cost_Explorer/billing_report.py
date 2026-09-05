#!/usr/bin/env python3
"""
AWS Billing Report Generator
============================

Retrieves AWS billing / cost data using the AWS Cost Explorer API (via Boto3)
for a user-specified date range, prints a summary to the console, and
generates a PDF report containing:

    1. Billing period
    2. Total AWS cost
    3. Service-wise cost breakdown
    4. Daily cost breakdown
    5. Currency

AWS credentials are NEVER hardcoded. Boto3 uses the standard credential
resolution chain, i.e. one of:
    - Environment variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN)
    - Shared credentials file (~/.aws/credentials)
    - AWS config file (~/.aws/config) with a named profile (--profile)
    - IAM role (EC2 instance profile / ECS task role / Lambda execution role)
    - AWS SSO

Requirements:
    pip install boto3 reportlab

Usage:
    python aws_billing_report.py
    python aws_billing_report.py --start 2025-01-01 --end 2025-01-31
    python aws_billing_report.py --profile myprofile --output my_report.pdf

Notes:
    - The AWS Cost Explorer API is only available in the us-east-1 region
      (it is a global service billed from that endpoint), and the calling
      IAM principal needs the "ce:GetCostAndUsage" permission.
    - Cost Explorer charges $0.01 per API request, so avoid calling this
      in a tight loop.
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# --------------------------------------------------------------------------- #
# Date handling
# --------------------------------------------------------------------------- #

DATE_FMT = "%Y-%m-%d"


def parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, DATE_FMT)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected format: YYYY-MM-DD"
        )


def prompt_for_dates() -> tuple[str, str]:
    """Interactively ask the user for a start and end date."""
    print("Enter the billing period.")
    while True:
        start_raw = input("Start date (YYYY-MM-DD): ").strip()
        end_raw = input("End date   (YYYY-MM-DD): ").strip()
        try:
            start_dt = parse_date(start_raw)
            end_dt = parse_date(end_raw)
        except argparse.ArgumentTypeError as exc:
            print(f"  ! {exc}\n")
            continue

        if end_dt <= start_dt:
            print("  ! End date must be after start date.\n")
            continue

        return start_dt.strftime(DATE_FMT), end_dt.strftime(DATE_FMT)


def ce_end_date_exclusive(end_date: str) -> str:
    """
    Cost Explorer treats the 'End' field as EXCLUSIVE.
    Users naturally think of the end date as inclusive (e.g. "Jan 1 to Jan 31"
    should include all of Jan 31), so we add one day internally before
    calling the API.
    """
    dt = datetime.strptime(end_date, DATE_FMT) + timedelta(days=1)
    return dt.strftime(DATE_FMT)


# --------------------------------------------------------------------------- #
# Cost Explorer calls
# --------------------------------------------------------------------------- #

def get_ce_client(profile: str | None):
    """
    Build a Cost Explorer client using the standard Boto3 credential chain.
    No secrets are ever read from source code — only from the environment,
    shared credentials file, config file, or an attached IAM role.
    """
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    # Cost Explorer is a global service, always addressed via us-east-1.
    return session.client("ce", region_name="us-east-1")


def fetch_total_and_service_costs(client, start: str, end_exclusive: str):
    """Returns (total_cost, currency, {service_name: cost})."""
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end_exclusive},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    service_costs = defaultdict(float)
    currency = "USD"
    total = 0.0

    for period in response.get("ResultsByTime", []):
        for group in period.get("Groups", []):
            service_name = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            currency = group["Metrics"]["UnblendedCost"]["Unit"]
            service_costs[service_name] += amount
            total += amount

    return total, currency, dict(service_costs)


def fetch_daily_costs(client, start: str, end_exclusive: str):
    """Returns ({date_str: cost}, currency)."""
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end_exclusive},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )

    daily_costs = {}
    currency = "USD"

    for period in response.get("ResultsByTime", []):
        day = period["TimePeriod"]["Start"]
        amount = float(period["Total"]["UnblendedCost"]["Amount"])
        currency = period["Total"]["UnblendedCost"]["Unit"]
        daily_costs[day] = amount

    return daily_costs, currency


def paginate_all(client, start: str, end_exclusive: str):
    """
    Handles pagination via NextPageToken for both calls, merging results.
    Cost Explorer rarely paginates for small date ranges, but this makes
    the tool robust for longer periods / accounts with many services.
    """
    def _paged_group_by():
        service_costs = defaultdict(float)
        total = 0.0
        currency = "USD"
        token = None
        while True:
            kwargs = dict(
                TimePeriod={"Start": start, "End": end_exclusive},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
            if token:
                kwargs["NextPageToken"] = token
            resp = client.get_cost_and_usage(**kwargs)
            for period in resp.get("ResultsByTime", []):
                for group in period.get("Groups", []):
                    name = group["Keys"][0]
                    amt = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    currency = group["Metrics"]["UnblendedCost"]["Unit"]
                    service_costs[name] += amt
                    total += amt
            token = resp.get("NextPageToken")
            if not token:
                break
        return total, currency, dict(service_costs)

    def _paged_daily():
        daily_costs = {}
        currency = "USD"
        token = None
        while True:
            kwargs = dict(
                TimePeriod={"Start": start, "End": end_exclusive},
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
            )
            if token:
                kwargs["NextPageToken"] = token
            resp = client.get_cost_and_usage(**kwargs)
            for period in resp.get("ResultsByTime", []):
                day = period["TimePeriod"]["Start"]
                amt = float(period["Total"]["UnblendedCost"]["Amount"])
                currency = period["Total"]["UnblendedCost"]["Unit"]
                daily_costs[day] = amt
            token = resp.get("NextPageToken")
            if not token:
                break
        return daily_costs, currency

    total, currency, service_costs = _paged_group_by()
    daily_costs, currency2 = _paged_daily()
    return total, (currency2 or currency), service_costs, daily_costs


# --------------------------------------------------------------------------- #
# PDF generation
# --------------------------------------------------------------------------- #

def generate_pdf_report(
    output_path: str,
    start: str,
    end: str,
    total_cost: float,
    currency: str,
    service_costs: dict,
    daily_costs: dict,
):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], fontSize=20, spaceAfter=12
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"], spaceBefore=16, spaceAfter=8
    )
    normal = styles["Normal"]

    elements = []

    # --- Title & billing period -------------------------------------------------
    elements.append(Paragraph("AWS Billing Report", title_style))
    elements.append(
        Paragraph(f"<b>Billing Period:</b> {start} to {end}", normal)
    )
    elements.append(Paragraph(f"<b>Currency:</b> {currency}", normal))
    elements.append(
        Paragraph(
            f"<b>Report Generated:</b> "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            normal,
        )
    )
    elements.append(Spacer(1, 0.2 * inch))

    # --- Total cost ---------------------------------------------------------
    elements.append(Paragraph("Total AWS Cost", heading_style))
    total_table = Table(
        [["Total Cost", f"{total_cost:,.2f} {currency}"]],
        colWidths=[3 * inch, 3 * inch],
    )
    total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#232F3E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(total_table)

    # --- Service-wise breakdown ----------------------------------------------
    elements.append(Paragraph("Service-wise Cost Breakdown", heading_style))
    if service_costs:
        sorted_services = sorted(
            service_costs.items(), key=lambda kv: kv[1], reverse=True
        )
        service_data = [["Service", f"Cost ({currency})", "% of Total"]]
        for name, amount in sorted_services:
            pct = (amount / total_cost * 100) if total_cost else 0
            service_data.append([name, f"{amount:,.2f}", f"{pct:.1f}%"])

        service_table = Table(
            service_data, colWidths=[3.2 * inch, 1.8 * inch, 1.2 * inch]
        )
        service_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF9900")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        elements.append(service_table)
    else:
        elements.append(Paragraph("No service-level cost data found.", normal))

    elements.append(PageBreak())

    # --- Daily breakdown ------------------------------------------------------
    elements.append(Paragraph("Daily Cost Breakdown", heading_style))
    if daily_costs:
        daily_data = [["Date", f"Cost ({currency})"]]
        for day in sorted(daily_costs.keys()):
            daily_data.append([day, f"{daily_costs[day]:,.2f}"])

        daily_table = Table(daily_data, colWidths=[3 * inch, 3 * inch])
        daily_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#232F3E")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(daily_table)
    else:
        elements.append(Paragraph("No daily cost data found.", normal))

    doc.build(elements)


# --------------------------------------------------------------------------- #
# Console output
# --------------------------------------------------------------------------- #

def print_summary(start, end, total_cost, currency, service_costs, daily_costs):
    print("\n" + "=" * 60)
    print(f"AWS BILLING REPORT: {start} to {end}")
    print("=" * 60)
    print(f"Total Cost: {total_cost:,.2f} {currency}\n")

    print("Service-wise Cost Breakdown:")
    print("-" * 60)
    for name, amount in sorted(service_costs.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {name:<40} {amount:>10,.2f} {currency}")

    print("\nDaily Cost Breakdown:")
    print("-" * 60)
    for day in sorted(daily_costs.keys()):
        print(f"  {day:<12} {daily_costs[day]:>10,.2f} {currency}")
    print("=" * 60 + "\n")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Generate an AWS billing PDF report using Cost Explorer."
    )
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD), inclusive")
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Named AWS CLI profile to use (defaults to standard credential chain)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output PDF file path (default: aws_billing_report_<start>_<end>.pdf)",
    )
    args = parser.parse_args()

    # --- Resolve billing period ---
    if args.start and args.end:
        try:
            start_dt = parse_date(args.start)
            end_dt = parse_date(args.end)
        except argparse.ArgumentTypeError as exc:
            print(f"Error: {exc}")
            sys.exit(1)
        if end_dt <= start_dt:
            print("Error: --end must be after --start.")
            sys.exit(1)
        start, end = args.start, args.end
    else:
        start, end = prompt_for_dates()

    end_exclusive = ce_end_date_exclusive(end)
    output_path = args.output or f"aws_billing_report_{start}_to_{end}.pdf"

    # --- Call Cost Explorer ---
    try:
        client = get_ce_client(args.profile)
        total_cost, currency, service_costs, daily_costs = paginate_all(
            client, start, end_exclusive
        )
    except NoCredentialsError:
        print(
            "Error: No AWS credentials found. Configure credentials via "
            "environment variables, `aws configure`, an AWS profile (--profile), "
            "or an IAM role."
        )
        sys.exit(1)
    except (BotoCoreError, ClientError) as exc:
        print(f"Error calling AWS Cost Explorer API: {exc}")
        sys.exit(1)

    # --- Output ---
    print_summary(start, end, total_cost, currency, service_costs, daily_costs)

    try:
        generate_pdf_report(
            output_path, start, end, total_cost, currency, service_costs, daily_costs
        )
    except Exception as exc:
        print(f"Error generating PDF report: {exc}")
        sys.exit(1)

    print(f"PDF report saved to: {output_path}")


if __name__ == "__main__":
    main()
