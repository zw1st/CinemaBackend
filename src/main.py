import uvicorn
from fastapi import FastAPI

from src.routes import auth, users

app = FastAPI(title="Cinema API")

app.include_router(auth.router)
app.include_router(users.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
