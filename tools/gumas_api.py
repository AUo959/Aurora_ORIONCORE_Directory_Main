#!/usr/bin/env python3
"""GUMAS Simulation Engine — FastAPI Server.

Exposes the GUMAS v3.0 advanced simulation engine as a REST API
for on-demand scenario runs, step-by-step execution, event injection,
and state queries.

Usage:
    python tools/gumas_api.py                     # localhost:8000
    python tools/gumas_api.py --host 0.0.0.0      # all interfaces
    python tools/gumas_api.py --port 9000          # custom port
    uvicorn tools.gumas_api:app --reload           # dev mode
"""

from __future__ import annotations

import sys
import threading
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Wire up engine imports
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SIM_DIR = _REPO_ROOT / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS"
_FORGE_DIR = _REPO_ROOT / "GUMAS_SIM_2.5" / "FORGE__GUMAS_v3.0__2026-02-19"

for _path in (str(_SIM_DIR), str(_FORGE_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from engine_advanced import GUMASAdvancedEngine  # noqa: E402
from models import EventType, SimulationEvent  # noqa: E402

# ── App ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GUMAS Simulation API",
    description="REST interface for the GUMAS v3.0 geopolitical simulation engine.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Session store ────────────────────────────────────────────────────────

_sessions: Dict[str, GUMASAdvancedEngine] = {}
_lock = threading.Lock()

MAX_SESSIONS = 10


def _get_engine(session_id: str) -> GUMASAdvancedEngine:
    with _lock:
        engine = _sessions.get(session_id)
    if engine is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return engine


# ── Request / Response models ────────────────────────────────────────────

class InitRequest(BaseModel):
    seed: int = Field(default=42, description="RNG seed for reproducibility.")
    scenario_id: str = Field(default="gumas_canonical_v1", description="Scenario to load.")

class InitResponse(BaseModel):
    session_id: str
    seed: int
    scenario_id: str
    turn: int
    factions: List[str]

class RunRequest(BaseModel):
    n_turns: int = Field(default=1, ge=1, le=100, description="Number of turns to simulate.")

class InjectEventRequest(BaseModel):
    event_type: str = Field(..., description="One of the EventType enum values.")
    source_faction: Optional[str] = None
    target_faction: Optional[str] = None
    severity: float = Field(default=0.5, ge=0.0, le=1.0)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str = ""

class MetricsResponse(BaseModel):
    turn: int
    stability_index: float
    risk_index: float
    summary: str

class FactionOverview(BaseModel):
    faction_id: str
    name: str
    military_strength: float
    economic_strength: float
    technology_level: float
    population_stability: float
    reputation: float

class SessionInfo(BaseModel):
    session_id: str
    turn: int
    seed: int
    faction_count: int


# ── Endpoints ────────────────────────────────────────────────────────────

@app.get("/api/v1/sessions", response_model=List[SessionInfo])
def list_sessions():
    """List all active simulation sessions."""
    result = []
    with _lock:
        for sid, engine in _sessions.items():
            state = engine.get_state()
            result.append(SessionInfo(
                session_id=sid,
                turn=state.turn,
                seed=state.seed,
                faction_count=len(state.factions),
            ))
    return result


@app.post("/api/v1/sessions", response_model=InitResponse, status_code=201)
def create_session(req: InitRequest):
    """Initialize a new simulation session."""
    with _lock:
        if len(_sessions) >= MAX_SESSIONS:
            raise HTTPException(
                status_code=429,
                detail=f"Maximum {MAX_SESSIONS} concurrent sessions. Delete an existing session first.",
            )
        session_id = uuid.uuid4().hex[:12]
        engine = GUMASAdvancedEngine(seed=req.seed)
        state = engine.init_scenario(scenario_id=req.scenario_id)
        _sessions[session_id] = engine

    return InitResponse(
        session_id=session_id,
        seed=req.seed,
        scenario_id=req.scenario_id,
        turn=state.turn,
        factions=sorted(state.factions.keys()),
    )


@app.delete("/api/v1/sessions/{session_id}", status_code=204)
def delete_session(session_id: str):
    """Destroy a simulation session."""
    with _lock:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
        del _sessions[session_id]


@app.post("/api/v1/sessions/{session_id}/step")
def step(session_id: str):
    """Advance the simulation by one turn."""
    engine = _get_engine(session_id)
    result = engine.step()
    return result.to_dict()


@app.post("/api/v1/sessions/{session_id}/run")
def run(session_id: str, req: RunRequest):
    """Advance the simulation by N turns."""
    engine = _get_engine(session_id)
    results = engine.run(req.n_turns)
    return {
        "turns_executed": len(results),
        "results": [r.to_dict() for r in results],
    }


@app.get("/api/v1/sessions/{session_id}/state")
def get_state(session_id: str, include_history: bool = False):
    """Get the current simulation state."""
    engine = _get_engine(session_id)
    state = engine.get_state()
    return state.to_dict(include_history=include_history)


@app.get("/api/v1/sessions/{session_id}/v3-state")
def get_v3_state(session_id: str):
    """Get the v3 extension state (population, tech, negotiation, intel, rebellion)."""
    engine = _get_engine(session_id)
    v3 = engine.get_v3_state()
    if v3 is None:
        raise HTTPException(status_code=404, detail="V3 state not initialized.")
    return v3.to_dict()


@app.get("/api/v1/sessions/{session_id}/metrics", response_model=MetricsResponse)
def get_metrics(session_id: str):
    """Get the latest stability/risk metrics."""
    engine = _get_engine(session_id)
    history = engine.get_advanced_history()
    if not history:
        state = engine.get_state()
        return MetricsResponse(
            turn=state.turn,
            stability_index=1.0,
            risk_index=0.0,
            summary="No turns executed yet.",
        )
    latest = history[-1]
    return MetricsResponse(
        turn=latest.turn,
        stability_index=latest.stability_index,
        risk_index=latest.risk_index,
        summary=latest.summary,
    )


@app.get("/api/v1/sessions/{session_id}/factions", response_model=List[FactionOverview])
def list_factions(session_id: str):
    """List all factions with key attributes."""
    engine = _get_engine(session_id)
    state = engine.get_state()
    result = []
    for fid, faction in sorted(state.factions.items()):
        result.append(FactionOverview(
            faction_id=fid,
            name=faction.name,
            military_strength=faction.military_strength,
            economic_strength=faction.economic_strength,
            technology_level=faction.technology_level,
            population_stability=faction.population_stability,
            reputation=faction.reputation,
        ))
    return result


@app.get("/api/v1/sessions/{session_id}/factions/{faction_id}")
def get_faction(session_id: str, faction_id: str):
    """Get detailed state for a specific faction."""
    engine = _get_engine(session_id)
    state = engine.get_state()
    faction = state.factions.get(faction_id)
    if faction is None:
        raise HTTPException(status_code=404, detail=f"Faction '{faction_id}' not found.")
    leader = state.leaders.get(faction_id)
    result = asdict(faction)
    result["faction_type"] = faction.faction_type.value
    if leader:
        leader_dict = asdict(leader)
        leader_dict["dominant_bias"] = leader.dominant_bias.value
        leader_dict["secondary_biases"] = [b.value for b in leader.secondary_biases]
        result["leader"] = leader_dict
    return result


@app.post("/api/v1/sessions/{session_id}/events")
def inject_event(session_id: str, req: InjectEventRequest):
    """Inject an external event into the simulation."""
    engine = _get_engine(session_id)
    state = engine.get_state()

    try:
        event_type = EventType(req.event_type)
    except ValueError:
        valid = [e.value for e in EventType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type '{req.event_type}'. Valid types: {valid}",
        )

    if req.source_faction and req.source_faction not in state.factions:
        raise HTTPException(status_code=400, detail=f"Unknown source_faction '{req.source_faction}'.")
    if req.target_faction and req.target_faction not in state.factions:
        raise HTTPException(status_code=400, detail=f"Unknown target_faction '{req.target_faction}'.")

    event = SimulationEvent(
        event_id=f"api_{uuid.uuid4().hex[:8]}",
        event_type=event_type,
        turn=state.turn,
        source_faction=req.source_faction,
        target_faction=req.target_faction,
        severity=req.severity,
        parameters=req.parameters,
        description=req.description,
    )
    engine.inject_event(event)
    return {"status": "queued", "event_id": event.event_id, "scheduled_turn": state.turn + 1}


@app.get("/api/v1/sessions/{session_id}/history")
def get_history(session_id: str, limit: int = 10, offset: int = 0):
    """Get simulation history with pagination."""
    engine = _get_engine(session_id)
    history = engine.get_advanced_history()
    total = len(history)
    page = history[offset:offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [r.to_dict() for r in page],
    }


@app.get("/api/v1/sessions/{session_id}/conflicts")
def get_conflicts(session_id: str):
    """Get all active and historical conflicts."""
    engine = _get_engine(session_id)
    state = engine.get_state()
    return {
        cid: {
            **asdict(conflict),
            "phase": conflict.phase.value,
        }
        for cid, conflict in state.conflicts.items()
    }


@app.get("/api/v1/sessions/{session_id}/treaties")
def get_treaties(session_id: str):
    """Get all treaties."""
    engine = _get_engine(session_id)
    state = engine.get_state()
    return {
        tid: {
            **asdict(treaty),
            "phase": treaty.phase.value,
        }
        for tid, treaty in state.treaties.items()
    }


@app.get("/api/v1/event-types")
def list_event_types():
    """List all available event types for injection."""
    return [{"value": e.value, "name": e.name} for e in EventType]


@app.get("/health")
def health():
    """Health check."""
    with _lock:
        session_count = len(_sessions)
    return {"status": "ok", "active_sessions": session_count}


# ── CLI entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="GUMAS Simulation API Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
