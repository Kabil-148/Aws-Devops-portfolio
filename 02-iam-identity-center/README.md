# AWS Organizations + IAM Identity Center

## Objective
Configure centralized AWS account access using IAM Identity Center.

## Architecture
Organizations → Identity Center → User → Permission Set → AWS Account → SSO

## AWS Services
- AWS Organizations
- IAM Identity Center
- IAM

## Implementation
1. Enabled AWS Organizations.
2. Created IAM Identity Center.
3. Created user.
4. Created Permission Set.
5. Assigned user to AWS account.
6. Logged in through SSO.

## Result
Successfully accessed the AWS account through IAM Identity Center SSO.
