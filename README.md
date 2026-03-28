---
title: RegComplianceEnv
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
  - openenv
---

# RegComplianceEnv

An OpenEnv-compatible environment for training and evaluating AI agents on Indian startup legal compliance classification. Agents read synthetic legal documents and identify compliance violations across Indian startup law.

## Motivation

Indian startups face complex legal compliance requirements across multiple regulations — DPDP Act 2023, Companies Act 2013, FEMA 2000, and more. Legal review costs ₹5,000–₹50,000 per document. This environment trains AI agents to perform reliable, consistent compliance checks at scale.

## Unique Features

- Confidence-weighted scoring — agents express confidence per issue and get rewarded for calibration
- Infinite document generator — fresh synthetic documents every reset() so agents cannot memorise text
- 10 planted issues across 5 document types in the hard task
- Fuzzy issue matching — partial credit for semantically correct but differently named issues
- Covers 7 real Indian laws with deterministic grading

## Action Space

| Field | Type | Description |
|-------|------|-------------|
| issue_id | string | Snake case identifier for the compliance issue |
| severity | low / medium / high | Severity level of the issue |
| clause_ref | string | Section or clause where issue was found |
| reason | string | One sentence explanation |
| confidence | float 0.0-1.0 | Agent confidence in this finding |

## Observation Space

| Field | Type | Description |
|-------|------|-------------|
| task_id | string | Current task identifier |
| documents | dict | Filename to document text mapping |
| task_goal | string | Plain English task objective |
| rules_to_check | list | Relevant Indian laws to check against |
| step_number | int | Current step in episode |

## Tasks

| Task | Difficulty | Documents | Issues | Random Agent | Strong Agent |
|------|------------|-----------|--------|--------------|--------------|
| task1 | Easy | 1 | 1 | 0.10 | 0.90 |
| task2 | Medium | 2 | 2 | 0.15 | 0.75 |
| task3 | Hard | 5 | 10 | 0.05 | 0.60 |

## Baseline Scores

Model: meta-llama/Llama-3.3-70B-Instruct via HuggingFace Router
Seed: 42

| Task | Difficulty | Score | Issues Found | False Positives |
|------|------------|-------|--------------|-----------------|
| task1 | Easy | 0.46 | 1/1 | 4 |
| task2 | Medium | 0.64 | 2/2 | 2 |
| task3 | Hard | 0.43 | 6/10 | 1 |
| Average | | 0.51 | | |

## Regulations Covered

- DPDP Act 2023 — Digital Personal Data Protection, data retention, grievance officer
- Companies Act 2013 — Board quorum, equity vesting, corporate governance
- FEMA 2000 — Foreign investment, foreign director approvals
- Arbitration Act 1996 — Dispute resolution clauses
- Copyright Act 1957 — IP assignment in employment
- IT Act 2000 — Data processing rules, intermediary guidelines
- Shops and Establishments Act — Notice period limits

## Setup

### Docker

docker build -t regcompliance-env .
docker run -p 7860:7860 regcompliance-env

### API Usage

Reset environment:
POST /reset
{"task_id": "task1", "use_generator": true, "seed": 42}

Submit action:
POST /step
{"issues": [{"issue_id": "missing_data_retention_clause", "severity": "high", "clause_ref": "Section 3", "reason": "No retention period specified", "confidence": 0.95}]}

Check state:
GET /state

Health check:
GET /health

### Running Inference

export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
export HF_TOKEN=your_token_here
python inference.py

## Links

Space: https://huggingface.co/spaces/sarthakdhatrak/regcompliance-env
API: https://sarthakdhatrak-regcompliance-env.hf.space
Docs: https://sarthakdhatrak-regcompliance-env.hf.space/docs