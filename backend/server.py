from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess, tempfile, os, uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Backend running successfully"}

@app.post("/run")
async def run_code(request: Request):
    data = await request.json()
    code = data.get("code", "")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
        tmp.write(code.encode("utf-8"))
        tmp.flush()
        try:
            result = subprocess.run(
                ["python", tmp.name],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout or result.stderr
        except subprocess.TimeoutExpired:
            output = "Execution timed out"
    os.unlink(tmp.name)
    return {"output": output}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
