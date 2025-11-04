from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import tempfile
import os

app = FastAPI()

# Allow frontend from any domain (GitHub Pages)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeRequest(BaseModel):
    language: str
    code: str

@app.post("/run")
async def run_code(req: CodeRequest):
    if req.language != "python":
        return {"output": "⚠️ Live input currently supported only for Python."}

    # Create a temp file for the Python code
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as temp:
        temp.write(req.code)
        temp_filename = temp.name

    try:
        # Start an interactive subprocess
        proc = subprocess.Popen(
            ["python3", "-i", temp_filename],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        output = ""
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            output += line
        stderr = proc.stderr.read()
        output += stderr
        return {"output": output}
    except Exception as e:
        return {"output": f"Error: {e}"}
    finally:
        os.remove(temp_filename)
