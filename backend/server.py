import os
import subprocess
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from github import Github
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_TOKEN = os.getenv("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")
GITHUB_REPO = os.getenv("no-body-0/code-storage")

@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    filename = f"code_{uuid.uuid4().hex[:8]}.py"

    # Save code temporarily
    with open(filename, "w") as f:
        f.write(code)

    # Execute Python code safely
    try:
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = "Error: Code execution timed out."

    # Save to GitHub
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        repo.create_file(f"codes/{filename}", "Add new code", code)
    except Exception as e:
        output += f"\n[GitHub save failed: {e}]"

    # Delete temp file
    os.remove(filename)

    return {"output": output}
