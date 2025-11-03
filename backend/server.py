import os
import subprocess
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from github import Github

app = FastAPI()

# === CORS Settings ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === GitHub Configuration ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")


# ============================
# ✅ Run Python Code Endpoint
# ============================
@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    stdin = data.get("stdin", "") or ""  # get input text from frontend
    filename = f"temp_{uuid.uuid4().hex[:8]}.py"

    # Write user code to a temporary file
    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        # Run code with user-provided input
        result = subprocess.run(
            ["python3", filename],
            input=stdin.encode(),        # feed input properly
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10                   # prevent infinite loops
        )

        output = (result.stdout + result.stderr).decode()

    except subprocess.TimeoutExpired:
        output = "❌ Error: Code execution timed out."
    except Exception as e:
        output = f"⚠️ Runtime error: {str(e)}"

    # Remove temporary file after execution
    try:
        os.remove(filename)
    except:
        pass

    return {"output": output}


# ============================
# ✅ Share Code Endpoint
# ============================
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


# ============================
# ✅ Load Shared Code Endpoint
# ============================
@app.get("/code/{code_id}")
async def get_code(code_id: str):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        file_content = repo.get_contents(f"codes/{code_id}")
        return {"code": file_content.decoded_content.decode()}
    except Exception as e:
        return {"error": str(e)}
