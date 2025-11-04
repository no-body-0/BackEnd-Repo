# server.py
import asyncio
import tempfile
import os
import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# CORS — tighten to your frontend domain in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# persistent DB file
DB_PATH = "compiler_data.db"

def ensure_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()

ensure_db()

# -------------------------
# WebSocket interactive Python runner
# -------------------------
@app.websocket("/runlive")
async def runlive(ws: WebSocket):
    await ws.accept()
    try:
        code = await ws.receive_text()
    except WebSocketDisconnect:
        return

    # write code to temporary file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w")
    tmp.write(code)
    tmp.flush()
    tmp_path = tmp.name
    tmp.close()

    # run python unbuffered for live output
    proc = await asyncio.create_subprocess_exec(
        "python3", "-u", tmp_path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def forward(stream):
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                try:
                    await ws.send_text(line.decode(errors="ignore"))
                except WebSocketDisconnect:
                    break
        except Exception:
            pass

    stdout_task = asyncio.create_task(forward(proc.stdout))
    stderr_task = asyncio.create_task(forward(proc.stderr))

    try:
        while True:
            try:
                msg = await ws.receive_text()
            except WebSocketDisconnect:
                break

            if msg == "___TERMINATE___":
                break

            # write to stdin of process
            if proc.stdin:
                proc.stdin.write((msg + "\n").encode())
                await proc.stdin.drain()

            # if process finished, break
            if proc.returncode is not None:
                break
    finally:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            await stdout_task
            await stderr_task
        except Exception:
            pass
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        try:
            await ws.close()
        except Exception:
            pass

# -------------------------
# SQL endpoint — persistent SQLite DB
# -------------------------
class SQLRequest(BaseModel):
    query: str

@app.post("/sql")
async def run_sql(req: SQLRequest):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(req.query)
        if req.query.strip().lower().startswith("select"):
            rows = cur.fetchall()
            results = [dict(row) for row in rows]
            columns = rows[0].keys() if rows else []
            conn.commit()
            return {"status": "ok", "columns": list(columns), "rows": results}
        else:
            conn.commit()
            return {"status": "ok", "message": "Query executed."}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=10000)
