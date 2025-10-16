import os, subprocess, shlex
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI()
TOKEN = os.getenv("RUNNER_TOKEN", "dev-secret")
ALLOW = {"python", "pytest", "node", "npm", "echo"}

class RunReq(BaseModel):
    exe: str
    args: str = ""
    cwd: str | None = None
    timeout: int = 60

def _auth(req: Request):
    if req.headers.get("X-Runner-Token") != TOKEN:
        raise HTTPException(401, "unauthorized")

@app.post("/run")
async def run(req: Request, body: RunReq):
    _auth(req)
    if body.exe not in ALLOW:
        raise HTTPException(400, "command not allowed")

    cmd = f"{body.exe} {body.args}".strip()
    try:
        out = subprocess.run(
            cmd,
            shell=True,
            cwd=body.cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=body.timeout,
        )
        return {
            "cmd": cmd,
            "code": out.returncode,
            "stdout": out.stdout[-4000:],
            "stderr": out.stderr[-4000:],
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(408, "timeout")

@app.get("/")
def ping():
    return {"ok": True}

