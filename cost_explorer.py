import boto3
import csv
import requests

THRESHOLD = 1.00

ce = boto3.client("ce", region_name="us-east-1")

response = ce.get_cost_and_usage(
    TimePeriod={"Start": "2026-09-01", "End": "2026-10-01"},
    Granularity="MONTHLY",
    Metrics=["UnblendedCost"],
    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}]
)

total = 0

with open("aws_costs.csv", "w", newline="", encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["Service", "Amount", "Unit"])

    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            unit = group["Metrics"]["UnblendedCost"]["Unit"]

            writer.writerow([service, f"{amount:.2f}", unit])
            total += amount

    writer.writerow(["TOTAL", f"{total:.2f}", "USD"])

print(f"File is generated : aws_costs.csv")
print(f"Total AWS cost: ${total:.2f}")

if total > THRESHOLD:
    response = requests.post(
        "https://hooks.slack.com/services/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",
        json={"text": f"AWS cost exceeded $2! Total: ${total:.2f}"},
        timeout=15
    )
    print("Slack notification sent!")
else:
    print("Cost is within the limit. No notification sent.")