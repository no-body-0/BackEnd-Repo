import os
import subprocess
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from github import Github

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    filename = f"temp_{uuid.uuid4().hex[:8]}.py"

    with open(filename, "w") as f:
        f.write(code)

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

    os.remove(filename)
    return {"output": output}


@app.post("/share")
async def share_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    code_id = f"code_{uuid.uuid4().hex[:8]}.py"

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        repo.create_file(f"codes/{code_id}", "Add shared code", code)
        return {"url": f"https://no-body-0.github.io/FrontEnd-Reop/?id={code_id}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/code/{code_id}")
async def get_code(code_id: str):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_content = repo.get_contents(f"codes/{code_id}")
        return {"code": file_content.decoded_content.decode()}
    except Exception as e:
        return {"error": str(e)}
