from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Backend running successfully"}

if __name__ == "__main__":
    # Use host=0.0.0.0 for Render
    uvicorn.run(app, host="0.0.0.0", port=10000)
