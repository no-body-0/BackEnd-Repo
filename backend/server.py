from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio, subprocess, tempfile, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/runlive")
async def run_code_live(ws: WebSocket):
    await ws.accept()

    # Receive code from frontend
    code = await ws.receive_text()

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    # Start Python process
    process = await asyncio.create_subprocess_exec(
        "python3", "-i", tmp_path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    async def read_output(stream):
        while True:
            line = await stream.readline()
            if not line:
                break
            await ws.send_text(line.decode())

    # Start reading stdout/stderr
    asyncio.create_task(read_output(process.stdout))
    asyncio.create_task(read_output(process.stderr))

    try:
        # Listen for input from frontend
        while True:
            msg = await ws.receive_text()
            process.stdin.write((msg + "\n").encode())
            await process.stdin.drain()
    except:
        pass
    finally:
        process.kill()
        os.remove(tmp_path)
        await ws.close()
