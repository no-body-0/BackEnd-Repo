import os
import subprocess
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from github import Github
import uuid
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load GitHub token and repo
GITHUB_TOKEN = os.getenv("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")
GITHUB_REPO = os.getenv("no-body-0/code-storage")

g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    code_id = uuid.uuid4().hex[:8]
    filename = f"codes/{code_id}.py"

    # Save to GitHub
    try:
        repo.create_file(filename, f"Add {code_id}", code)
        share_url = f"https://no-body-0.github.io/FrontEnd-Reop/?id={code_id}"
    except Exception as e:
        share_url = f"[GitHub save failed: {e}]"

    # Execute locally
    with open("temp.py", "w") as f:
        f.write(code)
    try:
        result = subprocess.run(["python", "temp.py"], capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = "Error: Code execution timed out."
    finally:
        os.remove("temp.py")

    return {"output": output, "share_url": share_url}

@app.get("/code/{code_id}")
async def get_code(code_id: str):
    try:
        contents = repo.get_contents(f"codes/{code_id}.py")
        code = base64.b64decode(contents.content).decode("utf-8")
        return {"code": code}
    except Exception:
        return {"error": "Code not found"}
