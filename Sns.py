import shutil
import boto3

total, used, free = shutil.disk_usage("C:/")
percent = used / total * 100

if percent > 70:
    sns = boto3.client("sns", region_name="us-east-1")
    sns.publish(
        TopicArn="arn:aws:sns:us-east-1:146041105340:Disk_usage",
        Message= f"Disk is {percent:.1f}% full",
    )
    print("Alert sent")
else:
    print(f"Disk OK: {percent:.1f}%")
    print (used/ 1024**3)
    print(total/ 1024**3)