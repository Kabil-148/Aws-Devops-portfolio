# EC2 Auto Scaling + Launch Template

## Objective
Automatically create EC2 instances when CPU utilization increases.

## Architecture
CloudWatch → ASG → Launch Template → EC2 → Tomcat

## AWS Services
- Amazon EC2
- Launch Template
- Auto Scaling Group
- CloudWatch

## Implementation
1. Created Launch Template.
2. Added User Data for Java and Tomcat installation.
3. Created Auto Scaling Group.
4. Configured CPU-based scaling.
5. Generated CPU stress.
6. CPU exceeded 50%.
7. Alarm triggered.
8. ASG launched a new EC2 instance.
9. Verified Tomcat on the new instance.

## Result
Successfully demonstrated automated EC2 provisioning based on CPU utilization.
