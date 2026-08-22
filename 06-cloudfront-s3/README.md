# CloudFront + S3

## Objective
Deliver a static website through CloudFront using S3 as the origin.

## Architecture
User → CloudFront → OAC → S3

## AWS Services
- Amazon S3
- Amazon CloudFront
- Origin Access Control

## Implementation
1. Created S3 bucket.
2. Uploaded `index.html`.
3. Created CloudFront distribution.
4. Configured S3 as origin.
5. Enabled OAC.
6. Set `index.html` as default root object.
7. Updated website content.
8. Observed CloudFront cached version.
9. Created invalidation.
10. Verified updated content.

## Result
Successfully served an S3 website through CloudFront and demonstrated cache invalidation.
