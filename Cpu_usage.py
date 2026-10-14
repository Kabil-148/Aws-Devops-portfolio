import time
import psutil
import boto3

sns = boto3.client("sns", region_name="us-east-1")
TOPIC_ARN = "arn:aws:sns:us-east-1:146041105340:Disk_usage"

start = 0   # start time
sent = False   # Email sent

while True:
    try:
        cpu = psutil.cpu_percent(interval=30)   
        print(f"CPU usage: {cpu:.1f}%")
        print(time.time())

        if cpu > 70:
            if start == 0:
                start = time.time() #seconds since 1970 (real clock time)
            if time.time() - start >= 300 and not sent:
                sns.publish(
                    TopicArn=TOPIC_ARN,
                    Subject="CPU Alert",
                    Message=f"CPU has been above 70% for 5 minutes (now {cpu:.1f}%)",
                )
                sent = True
                print("Alert sent")
        else:
            start = 0
            sent = False

    except Exception as e: #all error
        print("Error:", e)