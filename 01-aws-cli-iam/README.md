# AWS CLI + IAM Authentication

## Objective
Configure AWS CLI and authenticate with AWS using IAM credentials.

## Architecture
Local Machine → AWS CLI → IAM Credentials → AWS

## AWS Services
- IAM
- AWS CLI
- AWS STS

## Implementation
1. Installed AWS CLI.
2. Created IAM user and access keys.
3. Configured AWS CLI using `aws configure`.
4. Verified identity using `aws sts get-caller-identity`.

## Result
Successfully authenticated to AWS through the AWS CLI.
