<<<<<<< HEAD
# RegComplianceEnv

**RegComplianceEnv** is a synthetic legal compliance training environment designed to evaluate and train AI agents on Indian startup law. It provides a robust, reproducible arena where agents must identify compliance violations across various legal documents, such as Privacy Policies, MOAs, and Employment Agreements. This environment exists to bridge the gap between AI development and complex regulatory requirements, offering a standardized benchmark for legal AI systems.

## Environment Description
In this environment, an agent is presented with a set of legal documents and a specific compliance goal. The agent must read the documents, cross-reference them with relevant Indian regulations, and identify potential issues. The output expected from the agent is a structured JSON array of compliance issues, each including a unique identifier, severity level, specific clause reference, a reasoning statement, and the agent's confidence in that finding.

## Unique Features
- **Confidence-weighted scoring system**: Agents are rewarded for high-confidence correct findings and penalized for overconfident false positives, encouraging well-calibrated legal reasoning.
- **Infinite document variant generator**: A built-in synthetic text engine generates fresh document variants for every episode, preventing agents from memorizing static text and ensuring true generalization.
- **10 planted issues across 5 document types**: The "hard" evaluation task (Task 3) includes ten distinct compliance violations strategically planted across multiple inter-locking documents, testing long-context reasoning and cross-document validation.

## Action Space
The agent's action must specify a list of compliance issues found.

| Field | Type | Description |
| :--- | :--- | :--- |
| `issue_id` | `string` | A unique snake_case identifier for the identified issue (e.g., `missing_data_retention_clause`). |
| `severity` | `enum` | One of `low`, `medium`, or `high`, indicating the legal risk of the violation. |
| `clause_ref` | `string` | The specific section or clause in the document where the violation occurs. |
| `reason` | `string` | A one-sentence explanation of why this constitutes a compliance violation. |
| `confidence` | `float` | The agent's confidence in this finding, from `0.0` (not confident) to `1.0` (fully certain). |

## Observation Space
At each step or reset, the agent receives an observation of the current environment state.

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | `string` | The ID of the current task (e.g., `task1`, `task2`, `task3`). |
| `documents` | `dictionary` | A map of filenames to their full text content for the agent to analyze. |
| `task_goal` | `string` | A description of what the agent is expected to achieve in this task. |
| `rules_to_check` | `list` | A list of specific Indian laws or regulations relevant to the task. |
| `step_number` | `integer` | The current step count within the episode (starts at 0). |

## Tasks

| Task | Difficulty | Documents | Issues | Expected Score (random agent) | Expected Score (strong agent) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `task1` | easy | 1 | 1 | 0.10 | 0.90 |
| `task2` | medium | 2 | 2 | 0.15 | 0.75 |
| `task3` | hard | 5 | 10 | 0.05 | 0.60 |

## Setup

### Docker
To build and run the environment using Docker:
```bash
docker build -t regcompliance-env .
docker run -p 7860:7860 regcompliance-env
```

### API Usage
Once the environment is running, you can interact with it via the following endpoints:

#### Reset Environment
Initialize a task with fresh documents.
```bash
curl -X POST http://localhost:7860/reset \
     -H "Content-Type: application/json" \
     -d '{"task_id": "task1", "use_generator": true, "seed": 42}'
```

#### Step (Submit Action)
Submit identified compliance issues for grading.
```bash
curl -X POST http://localhost:7860/step \
     -H "Content-Type: application/json" \
     -d '{"issues": [{"issue_id": "test_issue", "severity": "medium", "clause_ref": "Clause 1", "reason": "Example reasoning", "confidence": 0.9}]}'
```

#### Get Current State
Check the status of the environment.
```bash
curl http://localhost:7860/state
```

#### Health Check
Liveness probe for the API.
```bash
curl http://localhost:7860/health
```

## Baseline Scores
- **Task 1**: 0.85
- **Task 2**: 0.60
- **Task 3**: 0.35
- **Average**: 0.60

*Note: Baseline scores were generated using `inference.py` with `seed=42`.*

## Regulations Covered
1. **DPDP Act 2023**: Digital Personal Data Protection Act, governing the processing of personal data in India.
2. **FEMA 2000**: Foreign Exchange Management Act, regulating foreign exchange transactions and external trade.
3. **Companies Act 2013**: Primary legislation regulating the formation, reporting, and functioning of companies in India.
4. **Arbitration Act 1996**: Law governing the resolution of disputes through arbitration and conciliation in India.
5. **Copyright Act 1957**: Law protecting intellectual property rights of creators of original literary and artistic works.
6. **IT Act 2000**: Main law in India dealing with cybercrime and electronic commerce, providing legal recognition for electronic records.
7. **Shops and Establishments Act**: State-level legislation regulating conditions of work and employment in commercial establishments.
=======
---
title: Regcompliance Env
emoji: 📊
colorFrom: yellow
colorTo: pink
sdk: docker
pinned: false
license: mit
short_description: 'OpenEnv environment for AI agent training on Indian startup '
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> 7439365c298288bb10789bf4a7726df0e203f01f
