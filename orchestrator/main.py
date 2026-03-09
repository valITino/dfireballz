"""DFIReballz Orchestrator — FastAPI case management API."""

import os
from contextlib import asynccontextmanager
from uuid import UUID

import redis.asyncio as redis
from case_manager import CaseManager
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from playbook_runner import PlaybookRunner
from pydantic import BaseModel
from report_generator import ReportGenerator

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"postgresql://{os.environ.get('POSTGRES_USER', 'dfireballz')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'changeme')}@db:5432/"
    f"{os.environ.get('POSTGRES_DB', 'dfireballz')}",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — setup and teardown."""
    app.state.redis = redis.from_url(REDIS_URL, decode_responses=True)
    app.state.case_manager = CaseManager(DATABASE_URL)
    await app.state.case_manager.init()
    app.state.playbook_runner = PlaybookRunner(app.state.case_manager)
    app.state.report_generator = ReportGenerator(app.state.case_manager)
    yield
    await app.state.redis.close()
    await app.state.case_manager.close()


app = FastAPI(
    title="DFIReballz Orchestrator",
    description="Digital Forensics & Cybercrime Investigation Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ─────────────────────────────────────────


class CaseCreate(BaseModel):
    title: str
    case_type: str = "other"
    description: str | None = None
    classification: str = "confidential"
    investigator: str | None = None


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    classification: str | None = None
    investigator: str | None = None


class IOCCreate(BaseModel):
    ioc_type: str
    value: str
    confidence: int = 50
    source: str | None = None
    mitre_technique: str | None = None
    notes: str | None = None


class PlaybookRun(BaseModel):
    playbook_name: str
    evidence_id: str | None = None


# ─── Health ──────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Service health check."""
    health_status = {"status": "healthy", "services": {}}
    try:
        await app.state.redis.ping()
        health_status["services"]["redis"] = "up"
    except Exception:
        health_status["services"]["redis"] = "down"
    try:
        await app.state.case_manager.health_check()
        health_status["services"]["database"] = "up"
    except Exception:
        health_status["services"]["database"] = "down"
    return health_status


# ─── Cases ───────────────────────────────────────────────────────────


@app.post("/cases")
async def create_case(case: CaseCreate):
    """Create a new investigation case."""
    return await app.state.case_manager.create_case(case.model_dump())


@app.get("/cases")
async def list_cases(status: str | None = None, case_type: str | None = None):
    """List all cases, optionally filtered."""
    return await app.state.case_manager.list_cases(status=status, case_type=case_type)


@app.get("/cases/{case_id}")
async def get_case(case_id: UUID):
    """Get case details."""
    case = await app.state.case_manager.get_case(str(case_id))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.put("/cases/{case_id}")
async def update_case(case_id: UUID, updates: CaseUpdate):
    """Update case details."""
    result = await app.state.case_manager.update_case(
        str(case_id), updates.model_dump(exclude_none=True)
    )
    if not result:
        raise HTTPException(status_code=404, detail="Case not found")
    return result


# ─── Evidence ────────────────────────────────────────────────────────


@app.post("/cases/{case_id}/evidence")
async def upload_evidence(case_id: UUID, file: UploadFile = File(...)):  # noqa: B008
    """Upload evidence file — auto-hashes and creates CoC entry."""
    return await app.state.case_manager.add_evidence(str(case_id), file)


@app.get("/cases/{case_id}/evidence")
async def list_evidence(case_id: UUID):
    """List all evidence for a case."""
    return await app.state.case_manager.list_evidence(str(case_id))


# ─── IOCs ────────────────────────────────────────────────────────────


@app.get("/cases/{case_id}/iocs")
async def list_iocs(case_id: UUID):
    """List IOCs for a case."""
    return await app.state.case_manager.list_iocs(str(case_id))


@app.post("/cases/{case_id}/iocs")
async def add_ioc(case_id: UUID, ioc: IOCCreate):
    """Add an IOC manually."""
    return await app.state.case_manager.add_ioc(str(case_id), ioc.model_dump())


# ─── Findings ────────────────────────────────────────────────────────


@app.get("/cases/{case_id}/findings")
async def list_findings(case_id: UUID):
    """List findings for a case."""
    return await app.state.case_manager.list_findings(str(case_id))


# ─── Playbooks ───────────────────────────────────────────────────────


@app.get("/playbooks")
async def list_playbooks():
    """List available investigation playbooks."""
    return app.state.playbook_runner.list_playbooks()


@app.post("/cases/{case_id}/playbooks/run")
async def run_playbook(case_id: UUID, run: PlaybookRun):
    """Launch a playbook against a case."""
    return await app.state.playbook_runner.run(
        str(case_id), run.playbook_name, run.evidence_id
    )


@app.get("/cases/{case_id}/playbooks")
async def list_playbook_runs(case_id: UUID):
    """List playbook runs for a case."""
    return await app.state.case_manager.list_playbook_runs(str(case_id))


# ─── Reports ─────────────────────────────────────────────────────────


@app.get("/cases/{case_id}/report")
async def generate_report(case_id: UUID, format: str = "markdown"):
    """Generate investigation report."""
    return await app.state.report_generator.generate(str(case_id), format)


# ─── Settings ────────────────────────────────────────────────────────

# API keys that can be configured via the UI.
# Maps UI key name → environment variable name.
_API_KEY_ENV_MAP: dict[str, str] = {
    "virustotal": "VIRUSTOTAL_API_KEY",
    "shodan": "SHODAN_API_KEY",
    "abuseipdb": "ABUSEIPDB_API_KEY",
    "urlscan": "URLSCAN_API_KEY",
    "vulncheck": "VULNCHECK_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}


def _mask_key(key: str) -> str:
    """Mask an API key for safe display: show first 4 and last 4 chars."""
    if not key or len(key) < 10:
        return "••••••••" if key else ""
    return f"{key[:4]}{'•' * (len(key) - 8)}{key[-4:]}"


class SettingsUpdate(BaseModel):
    mcp_host: str | None = None
    api_keys: dict[str, str] | None = None


@app.get("/settings")
async def get_settings():
    """Return current settings including which API keys are configured."""
    api_keys_status: dict[str, dict[str, str | bool]] = {}
    for ui_name, env_var in _API_KEY_ENV_MAP.items():
        raw = os.environ.get(env_var, "")
        api_keys_status[ui_name] = {
            "configured": bool(raw),
            "masked_value": _mask_key(raw) if raw else "",
            "env_var": env_var,
        }

    return {
        "mcp_host": os.environ.get("MCP_HOST", "claude-code"),
        "api_keys": api_keys_status,
    }


@app.post("/settings")
async def update_settings(settings: SettingsUpdate):
    """Update API keys in the running environment.

    Note: This updates the current process environment. To persist across
    restarts, users should also update their .env file or re-run make setup.
    """
    updated_keys: list[str] = []

    if settings.api_keys:
        for ui_name, value in settings.api_keys.items():
            env_var = _API_KEY_ENV_MAP.get(ui_name)
            if env_var and value:
                os.environ[env_var] = value
                updated_keys.append(ui_name)

    return {
        "status": "ok",
        "updated_keys": updated_keys,
        "note": "Keys updated in running environment. Update .env to persist across restarts.",
    }


@app.get("/settings/mcp-status")
async def mcp_status():
    """Health check all MCP server containers."""
    import subprocess

    servers = [
        "dfireballz-kali-forensics-1",
        "dfireballz-winforensics-1",
        "dfireballz-osint-1",
        "dfireballz-threat-intel-1",
        "dfireballz-binary-analysis-1",
        "dfireballz-network-forensics-1",
        "dfireballz-filesystem-1",
    ]
    statuses = {}
    for server in servers:
        name = server.replace("dfireballz-", "").replace("-1", "")
        try:
            result = subprocess.run(
                ["docker", "exec", server, "echo", "ping"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
            )
            statuses[name] = {
                "status": "healthy" if result.returncode == 0 else "unhealthy",
                "response": result.stdout.strip(),
            }
        except Exception as e:
            statuses[name] = {"status": "unreachable", "error": str(e)}
    return statuses
