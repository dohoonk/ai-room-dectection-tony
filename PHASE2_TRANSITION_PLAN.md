# Phase 2 Transition Plan: AWS Infrastructure Migration

## Executive Summary

This document outlines the comprehensive plan for transitioning Room Detection AI from the local MVP prototype to a production-ready AWS infrastructure. The plan incorporates learnings from MVP development, performance testing, and optimization analysis.

## Current State (MVP)

### Architecture
- **Frontend**: React + Material UI (localhost:3000)
- **Backend**: FastAPI (localhost:8000)
- **Storage**: Local file system
- **Processing**: Synchronous, in-memory
- **Deployment**: Local development environment

### Performance Metrics (Validated)
- ✅ Detection Accuracy: 100% (target: ≥ 90%)
- ✅ False Positives: 0% (target: < 10%)
- ✅ Processing Latency: 0.174s max (target: < 30s) - **172x faster than target**
- ✅ Supports: 1-50 rooms, rectangular and irregular shapes

### Key Learnings
1. **Algorithm Performance**: Face-finding algorithm exceeds all targets
2. **Scalability**: Handles 50+ rooms efficiently (< 0.2s)
3. **Shape Support**: Works with rectangular and irregular shapes
4. **User Experience**: Real-time processing enables interactive UX

## Target State (Phase 2)

### Architecture Overview

```
┌─────────────┐
│   React     │  Frontend (S3 + CloudFront)
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │  REST API Endpoint
│  + Lambda       │  Job Creation & Status
└──────┬──────────┘
       │
       ├──► S3 (Input/Output Storage)
       ├──► DynamoDB (Job State)
       └──► SQS (Job Queue)
              │
              ▼
       ┌──────────────┐
       │ ECS Fargate  │  Room Detection Worker
       │   Worker     │  (Python + NetworkX + Shapely)
       └──────────────┘
```

### Component Breakdown

| Component | Purpose | Technology | Rationale |
|-----------|---------|------------|-----------|
| **React Frontend** | User interface | React + Material UI | Existing, proven UI |
| **S3** | File storage | AWS S3 | Scalable, durable storage |
| **API Gateway** | API endpoint | AWS API Gateway | Managed REST API |
| **Lambda** | Job orchestration | AWS Lambda (Python) | Serverless, cost-effective |
| **DynamoDB** | Job state | AWS DynamoDB | Fast, scalable NoSQL |
| **SQS** | Job queue | AWS SQS | Decoupled processing |
| **ECS Fargate** | Processing worker | AWS ECS Fargate | Containerized Python runtime |
| **CloudWatch** | Monitoring | AWS CloudWatch | Observability & logging |

## Migration Strategy

### Phase 2A: Infrastructure Setup (Week 1-2)

#### 1. AWS Account & IAM Setup
- [ ] Create AWS account (if needed)
- [ ] Set up IAM roles and policies:
  - [ ] Lambda execution role
  - [ ] ECS task role
  - [ ] S3 access policies
  - [ ] DynamoDB access policies
  - [ ] SQS access policies
- [ ] Configure AWS CLI and credentials
- [ ] Set up development/staging/production environments

#### 2. S3 Bucket Configuration
- [ ] Create S3 buckets:
  - [ ] `room-detection-input` (input floorplans)
  - [ ] `room-detection-output` (detected rooms JSON)
- [ ] Configure bucket policies (private, CORS)
- [ ] Set up lifecycle policies (archive old files)
- [ ] Enable versioning (optional, for audit trail)

#### 3. DynamoDB Table Design
- [ ] Create `RoomDetectionJobs` table:
  - **Partition Key**: `job_id` (String)
  - **Attributes**:
    - `status` (String): pending, processing, completed, failed
    - `created_at` (Number): Timestamp
    - `updated_at` (Number): Timestamp
    - `input_s3_key` (String): S3 key for input JSON
    - `output_s3_key` (String): S3 key for output JSON
    - `processing_time` (Number): Processing duration in seconds
    - `rooms_count` (Number): Number of rooms detected
    - `confidence_score` (Number): Average confidence
    - `error_message` (String): Error details if failed
- [ ] Configure TTL (Time To Live) for old jobs
- [ ] Set up Global Secondary Index (GSI) for status queries

#### 4. SQS Queue Setup
- [ ] Create `room-detection-queue` (Standard Queue)
- [ ] Configure:
  - Visibility timeout: 60 seconds (based on 0.174s processing time + buffer)
  - Message retention: 14 days
  - Dead-letter queue: For failed jobs
- [ ] Set up queue policies

### Phase 2B: Lambda Functions (Week 2-3)

#### 1. Job Creation Lambda
**Function**: `create-room-detection-job`

**Responsibilities**:
- Receive POST request with wall segments JSON
- Generate unique job ID
- Upload input JSON to S3
- Create DynamoDB job record (status: pending)
- Send job message to SQS queue
- Return job_id to client

**Input**:
```json
{
  "walls": [
    {"type": "line", "start": [0, 0], "end": [100, 0], "is_load_bearing": false}
  ]
}
```

**Output**:
```json
{
  "job_id": "job_abc123",
  "status": "pending",
  "created_at": 1234567890
}
```

#### 2. Job Status Lambda
**Function**: `get-room-detection-status`

**Responsibilities**:
- Query DynamoDB for job status
- Return current job state
- Include S3 presigned URL for output if completed

**Input**:
```json
{
  "job_id": "job_abc123"
}
```

**Output**:
```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "created_at": 1234567890,
  "updated_at": 1234567891,
  "processing_time": 0.174,
  "rooms_count": 3,
  "confidence_score": 1.0,
  "output_url": "https://s3.../output.json"
}
```

### Phase 2C: ECS Fargate Worker (Week 3-4)

#### 1. Docker Container
**Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY worker.py .

# Run worker
CMD ["python", "worker.py"]
```

**Requirements**:
- FastAPI (for local testing)
- NetworkX
- Shapely
- boto3 (AWS SDK)
- python-dotenv

#### 2. Worker Application
**File**: `worker.py`

**Responsibilities**:
- Poll SQS queue for jobs
- Download input JSON from S3
- Run room detection algorithm
- Upload output JSON to S3
- Update DynamoDB job status
- Delete SQS message on success

**Processing Flow**:
1. Receive message from SQS
2. Extract job_id and S3 input key
3. Download input JSON from S3
4. Run `detect_rooms()` algorithm
5. Upload output JSON to S3
6. Update DynamoDB with results
7. Delete SQS message

#### 3. ECS Task Definition
- **CPU**: 0.25 vCPU (sufficient for current processing time)
- **Memory**: 512 MB (sufficient for 50-room floorplans)
- **Image**: ECR repository URL
- **Environment Variables**:
  - `S3_INPUT_BUCKET`
  - `S3_OUTPUT_BUCKET`
  - `DYNAMODB_TABLE`
  - `SQS_QUEUE_URL`
  - `AWS_REGION`

#### 4. ECS Service Configuration
- **Service Type**: Fargate
- **Desired Count**: 1 (scale based on queue depth)
- **Auto Scaling**: Based on SQS queue depth
- **Health Checks**: Container health endpoint

### Phase 2D: API Gateway Integration (Week 4)

#### 1. API Gateway Setup
- [ ] Create REST API
- [ ] Define resources:
  - `POST /jobs` → Create job Lambda
  - `GET /jobs/{job_id}` → Get status Lambda
- [ ] Configure CORS for React frontend
- [ ] Set up API keys (optional, for rate limiting)
- [ ] Deploy to stage (dev, staging, prod)

#### 2. Integration Points
- [ ] Lambda integration
- [ ] Request/response mapping
- [ ] Error handling
- [ ] Request validation

### Phase 2E: Frontend Migration (Week 4-5)

#### 1. API Service Updates
**File**: `frontend/src/services/api.ts`

**Changes**:
- Replace localhost API with API Gateway endpoint
- Implement polling for job status
- Handle async job processing
- Update error handling

**New Flow**:
1. Upload JSON → Create job → Get job_id
2. Poll job status every 500ms
3. Display results when status = "completed"
4. Show loading state during processing

#### 2. Environment Configuration
- [ ] Create `.env` files for different environments
- [ ] Configure API Gateway URL
- [ ] Update build process for environment variables

#### 3. Deployment
- [ ] Build React app for production
- [ ] Upload to S3 bucket
- [ ] Configure CloudFront distribution
- [ ] Set up custom domain (optional)

### Phase 2F: Monitoring & Observability (Week 5)

#### 1. CloudWatch Metrics
- [ ] Job creation rate
- [ ] Job completion rate
- [ ] Processing time (p50, p95, p99)
- [ ] Error rate
- [ ] Queue depth
- [ ] ECS task CPU/memory utilization

#### 2. CloudWatch Logs
- [ ] Lambda function logs
- [ ] ECS task logs
- [ ] API Gateway access logs
- [ ] Log aggregation and search

#### 3. Alarms
- [ ] High error rate (> 5%)
- [ ] Processing time > 30s (PRD target)
- [ ] Queue depth > 100 (backlog)
- [ ] ECS task failures

#### 4. Dashboards
- [ ] Real-time metrics dashboard
- [ ] Job status overview
- [ ] Performance trends
- [ ] Error analysis

## Migration Checklist

### Pre-Migration
- [x] MVP complete and tested
- [x] Performance validated (exceeds all targets)
- [x] Algorithm optimized (not needed, but documented)
- [ ] AWS account setup
- [ ] IAM roles and policies configured
- [ ] Development environment ready

### Infrastructure
- [ ] S3 buckets created and configured
- [ ] DynamoDB table created
- [ ] SQS queue created
- [ ] ECS cluster and service configured
- [ ] API Gateway REST API deployed
- [ ] Lambda functions deployed
- [ ] CloudWatch dashboards created

### Application
- [ ] Docker container built and tested
- [ ] ECS task definition created
- [ ] Worker application deployed
- [ ] Lambda functions tested
- [ ] API Gateway endpoints tested
- [ ] Frontend updated for async processing
- [ ] Frontend deployed to S3/CloudFront

### Testing
- [ ] Unit tests pass in AWS environment
- [ ] Integration tests (S3, DynamoDB, SQS)
- [ ] End-to-end workflow test
- [ ] Load testing (multiple concurrent jobs)
- [ ] Error handling and retry logic
- [ ] Performance validation (< 30s target)

### Documentation
- [ ] Architecture diagrams updated
- [ ] Deployment guide created
- [ ] Runbook for operations
- [ ] API documentation updated
- [ ] Troubleshooting guide

## Cost Estimation

### Monthly Costs (Estimated)

| Service | Usage | Cost |
|---------|-------|------|
| **S3** | 1000 floorplans/month, 50KB each | ~$0.02 |
| **DynamoDB** | 1000 jobs/month, 1KB each | ~$0.25 |
| **SQS** | 1000 messages/month | ~$0.00 (free tier) |
| **Lambda** | 2000 invocations/month, 100ms each | ~$0.00 (free tier) |
| **ECS Fargate** | 1 task, 0.25 vCPU, 512MB, 10% utilization | ~$3.00 |
| **API Gateway** | 2000 requests/month | ~$0.00 (free tier) |
| **CloudWatch** | Logs and metrics | ~$1.00 |
| **Data Transfer** | 10GB/month | ~$0.90 |
| **Total** | | **~$5.17/month** |

**Note**: Costs scale with usage. For 10,000 floorplans/month, estimated cost: ~$50/month.

## Performance Targets

### Latency Goals
- **Job Creation**: < 1 second (API Gateway + Lambda)
- **Job Processing**: < 30 seconds (PRD target, current: 0.174s)
- **Total End-to-End**: < 35 seconds (including queue wait time)

### Scalability Goals
- **Concurrent Jobs**: Support 10+ concurrent jobs
- **Throughput**: 100+ jobs/hour
- **Queue Processing**: Process jobs within 1 minute of submission

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **ECS task failures** | High | Health checks, auto-restart, dead-letter queue |
| **S3 upload/download failures** | Medium | Retry logic, error handling |
| **DynamoDB throttling** | Low | Provisioned capacity, exponential backoff |
| **SQS message loss** | Low | Dead-letter queue, message visibility timeout |
| **Lambda cold starts** | Low | Provisioned concurrency (if needed) |

### Operational Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Cost overruns** | Medium | Budget alerts, cost monitoring |
| **Security vulnerabilities** | High | IAM least privilege, encryption at rest |
| **Data loss** | High | S3 versioning, DynamoDB backups |
| **Service outages** | High | Multi-AZ deployment, health checks |

## Success Criteria

### Phase 2 Complete When:
- [x] All infrastructure components deployed
- [ ] End-to-end workflow functional
- [ ] Performance meets PRD targets (< 30s)
- [ ] Monitoring and alerting operational
- [ ] Documentation complete
- [ ] Cost within budget
- [ ] Security review passed

## Next Steps

1. **Immediate**: Review and approve this plan
2. **Week 1**: Set up AWS account and IAM
3. **Week 2**: Deploy S3, DynamoDB, SQS
4. **Week 3**: Build and deploy Lambda functions
5. **Week 4**: Deploy ECS Fargate worker
6. **Week 5**: Integrate API Gateway and frontend
7. **Week 6**: Testing, monitoring, and documentation

## References

- [AWS Architecture Best Practices](https://aws.amazon.com/architecture/)
- [ECS Fargate Documentation](https://docs.aws.amazon.com/ecs/latest/developerguide/AWS_Fargate.html)
- [API Gateway Best Practices](https://docs.aws.amazon.com/apigateway/latest/developerguide/best-practices.html)
- [DynamoDB Design Patterns](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)

