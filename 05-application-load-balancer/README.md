# Application Load Balancer

## Objective
Distribute web traffic across multiple EC2 instances.

## Architecture
Internet → ALB → Target Group → EC2 Instances

## AWS Services
- EC2
- Application Load Balancer
- Target Group
- Security Groups

## Implementation
1. Launched two EC2 instances in different AZs.
2. Installed Nginx.
3. Created target group.
4. Registered both EC2 instances.
5. Configured ALB.
6. Configured listener on port 80.
7. Configured security groups.
8. Tested ALB DNS.
9. Verified health checks.

## Result
Successfully distributed traffic across healthy EC2 instances.
