# Amazon EBS Volume

## Objective
Attach and use an additional EBS volume for application storage.

## Architecture
EC2 → EBS → ext4 → /app → Application

## AWS Services
- Amazon EC2
- Amazon EBS

## Implementation
1. Created additional EBS volume.
2. Attached volume to EC2.
3. Created ext4 filesystem.
4. Mounted volume at `/app`.
5. Installed Java, Maven and Tomcat.
6. Ran Tomcat on port 8080.
7. Detached the volume.
8. Attached the same volume to another EC2 instance.

## Result
Successfully demonstrated persistent application storage using EBS.
