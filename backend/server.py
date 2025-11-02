# backend/server.py
import os
import requests
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")  # e.g. https://YOUR_GH_USERNAME.github.io/FRONTEND_REPO

@app.get("/login")
def login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope=repo"
    )

@app.get("/callback")
def callback(code: str):
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": code}
    r = requests.post(token_url, headers=headers, data=data)
    token = r.json().get("access_token")
    # redirect to frontend with token in URL fragment (safer than query)
    return RedirectResponse(f"{FRONTEND_URL}/?token={token}")

@app.get("/user")
def user_info(token: str):
    r = requests.get("https://api.github.com/user", headers={"Authorization": f"token {token}"})
    return JSONResponse(r.json())
