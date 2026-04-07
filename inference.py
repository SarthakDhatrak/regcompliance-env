import os
import json
import time
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from openai import OpenAI

# ---------------------------------------------------------------------------
# Config & Constants
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN     = os.getenv("HF_TOKEN")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "https://sarthakdhatrak-regcompliance-env.hf.space")
API_BASE     = ENV_BASE_URL
SLEEP_TIME   = 5  # seconds between tasks

TASKS = [
    {"id": "task1", "name": "Task 1 (easy)", "total": 1},
    {"id": "task2", "name": "Task 2 (medium)", "total": 2},
    {"id": "task3", "name": "Task 3 (hard)", "total": 10},
]

PROMPT_TEMPLATE = (
    "You are a legal compliance expert specializing in Indian startup law. "
    "Your task: {task_goal}. Check against these regulations: {rules_to_check}. "
    "Read the following documents carefully: {documents}. "
    "Respond ONLY with a valid JSON array of compliance issues you find. "
    "Each issue must have these exact fields: issue_id (snake_case string describing the issue), "
    "severity (exactly one of: low, medium, high), clause_ref (the section where you found it), "
    "reason (one sentence explanation), confidence (your confidence from 0.0 to 1.0). "
    "If you find no issues, respond with an empty array []. Do not include any text outside the JSON array."
)

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def get_env(key: str) -> str:
    """Read environment variable or exit if missing."""
    val = os.environ.get(key)
    if not val:
        print(f"Error: Environment variable {key} is required.", flush=True)
        sys.exit(1)
    return val

def api_post(endpoint: str, data: dict) -> dict:
    """Send a POST request to the local environment server."""
    url = f"{API_BASE}{endpoint}"
    req_body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=req_body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"API Error ({url}): {e}", flush=True)
        return {}

def format_docs(docs: Dict[str, str]) -> str:
    """Format dictionary of documents into a single string."""
    formatted = []
    for name, content in docs.items():
        formatted.append(f"--- DOCUMENT: {name} ---\n{content}\n")
    return "\n".join(formatted)

def parse_llm_json(text: str) -> List[Dict[str, Any]]:
    """Parse JSON array from LLM response strings, handling common issues."""
    text = text.strip()
    # Simple heuristic to extract JSON array if model included extra text
    if "[" in text and "]" in text:
        start = text.find("[")
        end = text.rfind("]") + 1
        text = text[start:end]
    
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        return []

# ---------------------------------------------------------------------------
# Main Inference Logic
# ---------------------------------------------------------------------------

def main():
    # 1. Setup — use module-level defaults; token is optional for open models
    api_url    = API_BASE_URL
    model_name = MODEL_NAME
    api_key    = HF_TOKEN or "dummy-token"

    print(f"ENV  base : {ENV_BASE_URL}", flush=True)
    print(f"LLM  base : {api_url}", flush=True)
    print(f"Model     : {model_name}", flush=True)

    client = OpenAI(base_url=api_url, api_key=api_key)
    
    task_results = []

    print(f"Starting inference with model: {model_name}", flush=True)
    print("-" * 40, flush=True)

    for task_meta in TASKS:
        task_id = task_meta["id"]
        task_name = task_meta["name"]
        
        print(f"Running {task_name}...", flush=True)
        print(f"[START] task={task_id}", flush=True)
        
        score = 0.0

        # 2. Reset Environment
        obs = api_post("/reset", {"task_id": task_id, "use_generator": True, "seed": 42})
        if not obs:
            print(f"Failed to reset task {task_id}. Skipping.", flush=True)
            task_results.append({"name": task_name, "score": 0.0, "found": 0, "total": task_meta["total"], "fp": 0})
            print(f"[END] task={task_id} score={score} steps=1", flush=True)
            continue

        # 3. Build Prompt
        prompt = PROMPT_TEMPLATE.format(
            task_goal=obs["task_goal"],
            rules_to_check=", ".join(obs["rules_to_check"]),
            documents=format_docs(obs["documents"])
        )

        # 4. Call LLM
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            llm_text = response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}", flush=True)
            llm_text = "[]"

        # 5. Parse Response
        issues = parse_llm_json(llm_text)
        
        # 6. Step (Submit Action)
        # Action model expects {"issues": [...]}
        step_result = api_post("/step", {"issues": issues})
        
        if step_result:
            reward = step_result["reward"]
            score = reward["score"]
            print(f"  Score: {score:.2f}", flush=True)
            print(f"[STEP] step=1 reward={score}", flush=True)
            print(f"  Feedback: {reward['feedback']}", flush=True)
            
            task_results.append({
                "name": task_name,
                "score": reward["score"],
                "found": reward["issues_found"],
                "total": task_meta["total"],
                "fp": reward["false_positives"]
            })
        else:
            task_results.append({"name": task_name, "score": 0.0, "found": 0, "total": task_meta["total"], "fp": 0})

        print(f"[END] task={task_id} score={score} steps=1", flush=True)

        # 7. Cooldown
        time.sleep(SLEEP_TIME)

    # 8. Summary Table
    print("\n" + "="*60, flush=True)
    scores = []
    for res in task_results:
        print(f"{res['name']}: score {res['score']:.2f} | found {res['found']}/{res['total']} issues | false positives: {res['fp']}", flush=True)
        scores.append(res["score"])
    
    avg_score = sum(scores) / len(scores) if scores else 0.0
    print(f"Average score: {avg_score:.2f}", flush=True)
    print("="*60, flush=True)

if __name__ == "__main__":
    main()
    sys.exit(0)
