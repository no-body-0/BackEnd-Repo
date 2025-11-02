import os
import subprocess
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from github import Github

app = FastAPI()

# ===== CORS (Frontend Access) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can later restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== GitHub Setup =====
GITHUB_TOKEN = os.getenv("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")
GITHUB_REPO = os.getenv("no-body-0/code-storage")

# ====== Run Code Endpoint ======
@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    filename = f"code_{uuid.uuid4().hex[:8]}.py"

    # Save temporarily
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


# ====== Share Code Endpoint ======
@app.post("/share")
async def share_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    share_id = uuid.uuid4().hex[:8]
    filename = f"shared/{share_id}.py"

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        repo.create_file(filename, "Share new code", code)
        share_url = f"https://no-body-0.github.io/FrontEnd-Reop/?id={share_id}"
        return {"share_url": share_url, "id": share_id}
    except Exception as e:
        return {"error": str(e)}


# ====== Load Code Endpoint ======
@app.get("/load")
async def load_code(id: str):
    filename = f"shared/{id}.py"

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file = repo.get_contents(filename)
        code = file.decoded_content.decode()
        return {"code": code}
    except Exception as e:
        return {"error": f"Code not found or {e}"}
