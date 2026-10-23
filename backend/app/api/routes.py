import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from sse_starlette.sse import EventSourceResponse

from app.api.models import StartExperimentRequest, ReviewDecisionRequest, StatsResponse
from app.security.target_client import DVWATargetClient
from app.storage.database import Database
from app.experiments.referee import RefereeEngine
from app.review.triage import TriageQueue

router = APIRouter()

# Global state instances
database = Database("cyberranger.db")
target_client = DVWATargetClient(base_url="http://127.0.0.1:8080")
triage_queue = TriageQueue(database)

active_referee: Optional[RefereeEngine] = None
active_run_task: Optional[asyncio.Task] = None
sse_subscribers: Dict[str, List[asyncio.Queue]] = {}


def get_or_create_queue(exp_id: str) -> asyncio.Queue:
    if exp_id not in sse_subscribers:
        sse_subscribers[exp_id] = []
    q: asyncio.Queue = asyncio.Queue()
    sse_subscribers[exp_id].append(q)
    return q


def remove_queue(exp_id: str, q: asyncio.Queue) -> None:
    if exp_id in sse_subscribers and q in sse_subscribers[exp_id]:
        sse_subscribers[exp_id].remove(q)


def broadcast_round_event(event_data: Dict[str, Any]) -> None:
    exp_id = event_data.get("experiment_id", "")
    if exp_id in sse_subscribers:
        for q in list(sse_subscribers[exp_id]):
            try:
                q.put_nowait(event_data)
            except Exception:
                pass


@router.get("/health")
def health_check() -> Dict[str, Any]:
    dvwa_healthy = target_client.check_health()
    return {
        "status": "online",
        "target_healthy": dvwa_healthy,
        "guard_active": not target_client.guard.is_stopped,
        "database": "sqlite_connected",
    }


@router.get("/status")
def system_status() -> Dict[str, Any]:
    global active_referee
    exp_info = None
    if active_referee:
        rounds = database.get_rounds(active_referee.exp_id)
        exp_info = {
            "id": active_referee.exp_id,
            "current_round": active_referee.current_round,
            "is_paused": active_referee.is_paused,
            "is_stopped": active_referee.is_stopped,
            "archive_occupied": active_referee.archive.total_occupied,
            "detector_version": active_referee.detector.version_tag,
        }
    return {
        "active_experiment": exp_info,
        "pending_triage_count": len(triage_queue.get_pending()),
    }


@router.post("/experiments/start")
def start_experiment(req: StartExperimentRequest, bg_tasks: BackgroundTasks) -> Dict[str, Any]:
    global active_referee, active_run_task

    # Stop any previously running referee
    if active_referee:
        active_referee.is_stopped = True

    exp_id = str(uuid.uuid4())[:8]
    database.create_experiment(
        exp_id=exp_id,
        name=req.name,
        total_rounds=req.total_rounds,
        seed=req.seed,
        config=req.model_dump(),
    )

    active_referee = RefereeEngine(
        exp_id=exp_id,
        target_client=target_client,
        db=database,
        seed=req.seed,
        cadence_rounds=req.cadence_rounds,
        enable_llm=req.enable_llm,
    )
    active_referee.register_event_listener(broadcast_round_event)

    return {
        "message": "Experiment initialized",
        "experiment_id": exp_id,
        "total_rounds": req.total_rounds,
        "seed": req.seed,
    }


@router.post("/experiments/{exp_id}/step")
def step_experiment(exp_id: str) -> Dict[str, Any]:
    global active_referee
    if not active_referee or active_referee.exp_id != exp_id:
        raise HTTPException(status_code=404, detail="Active experiment not found")
    if active_referee.is_stopped:
        raise HTTPException(status_code=400, detail="Experiment is stopped")

    result = active_referee.run_round()
    return result


async def _run_rounds_worker(referee: RefereeEngine, target_rounds: int) -> None:
    while referee.current_round < target_rounds and not referee.is_stopped:
        if referee.is_paused:
            await asyncio.sleep(0.5)
            continue
        referee.run_round()
        await asyncio.sleep(0.1)  # Yield for SSE streaming


@router.post("/experiments/{exp_id}/run")
async def run_all_rounds(exp_id: str, bg_tasks: BackgroundTasks) -> Dict[str, Any]:
    global active_referee, active_run_task
    if not active_referee or active_referee.exp_id != exp_id:
        raise HTTPException(status_code=404, detail="Active experiment not found")

    with database.get_connection() as conn:
        cursor = conn.execute("SELECT total_rounds FROM experiments WHERE id = ?", (exp_id,))
        row = cursor.fetchone()
        target_rounds = row["total_rounds"] if row else 20

    active_referee.is_paused = False
    active_run_task = asyncio.create_task(_run_rounds_worker(active_referee, target_rounds))
    return {"message": "Autonomous round sequence running", "target_rounds": target_rounds}


@router.post("/experiments/{exp_id}/pause")
def pause_experiment(exp_id: str) -> Dict[str, Any]:
    global active_referee
    if not active_referee or active_referee.exp_id != exp_id:
        raise HTTPException(status_code=404, detail="Active experiment not found")
    active_referee.is_paused = True
    return {"message": "Experiment paused"}


@router.post("/experiments/{exp_id}/resume")
def resume_experiment(exp_id: str) -> Dict[str, Any]:
    global active_referee
    if not active_referee or active_referee.exp_id != exp_id:
        raise HTTPException(status_code=404, detail="Active experiment not found")
    active_referee.is_paused = False
    return {"message": "Experiment resumed"}


@router.post("/experiments/{exp_id}/stop")
def stop_experiment(exp_id: str) -> Dict[str, Any]:
    global active_referee, active_run_task
    if not active_referee or active_referee.exp_id != exp_id:
        raise HTTPException(status_code=404, detail="Active experiment not found")
    active_referee.is_stopped = True
    if active_run_task and not active_run_task.done():
        active_run_task.cancel()
    database.update_experiment_status(exp_id, "stopped", active_referee.current_round)
    return {"message": "Experiment stopped"}


@router.get("/experiments/{exp_id}/rounds")
def get_experiment_rounds(exp_id: str) -> List[Dict[str, Any]]:
    return database.get_rounds(exp_id)


@router.get("/experiments/{exp_id}/stats")
def get_experiment_stats(exp_id: str) -> StatsResponse:
    global active_referee
    rounds = database.get_rounds(exp_id)
    n = len(rounds)

    total_compromises = sum(1 for r in rounds if r["target_compromised"] == 1)
    total_blocked = sum(1 for r in rounds if r["detector_outcome"] == "Blocked")
    total_clean = sum(1 for r in rounds if r["detector_outcome"] == "Clean")

    # Detection rate: blocked / (compromises + blocked) or n
    det_rate = (total_blocked / n) if n > 0 else 0.0
    evasion_rate = (sum(1 for r in rounds if r["detector_outcome"] == "Evaded") / n) if n > 0 else 0.0

    detector_ver = active_referee.detector.version_tag if active_referee else "rules-v1.4+rf-untrained"
    archive_occ = active_referee.archive.total_occupied if active_referee else 0
    archive_cap = active_referee.archive.total_capacity if active_referee else 128
    archive_cov = active_referee.archive.coverage_ratio * 100 if active_referee else 0.0
    bandit_st = active_referee.bandit.get_stats() if active_referee else {}
    pending_cnt = len(triage_queue.get_pending(exp_id))

    return StatsResponse(
        current_round=n,
        total_rounds=20,
        status="running" if active_referee and not active_referee.is_stopped else "idle",
        detector_version=detector_ver,
        detection_rate=round(det_rate * 100, 1),
        evasion_rate=round(evasion_rate * 100, 1),
        total_compromises=total_compromises,
        total_blocked=total_blocked,
        total_clean=total_clean,
        active_rules_count=len(active_referee.detector.rule_engine.rules) if active_referee else 12,
        archive_occupied=archive_occ,
        archive_capacity=archive_cap,
        archive_coverage=round(archive_cov, 1),
        bandit_stats=bandit_st,
        pending_reviews_count=pending_cnt,
    )


@router.get("/triage/pending")
def get_pending_triage(exp_id: Optional[str] = None) -> List[Dict[str, Any]]:
    return triage_queue.get_pending(exp_id)


@router.post("/triage/{review_id}/review")
def review_triage_item(review_id: int, req: ReviewDecisionRequest) -> Dict[str, Any]:
    triage_queue.review_item(review_id, decision=req.decision, note=req.note)
    return {"message": f"Review recorded: {req.decision}", "id": review_id}


@router.get("/events/{exp_id}")
async def sse_event_stream(exp_id: str, request: Request) -> EventSourceResponse:
    q = get_or_create_queue(exp_id)

    async def event_generator():
        try:
            # Emit initial connection handshake
            yield {"event": "connected", "data": json.dumps({"experiment_id": exp_id})}

            while True:
                if await request.is_disconnected():
                    break
                try:
                    event_data = await asyncio.wait_for(q.get(), timeout=2.0)
                    yield {
                        "event": "round_complete",
                        "id": str(event_data.get("round_number", "")),
                        "data": json.dumps(event_data),
                    }
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield {"event": "ping", "data": "keep-alive"}
        finally:
            remove_queue(exp_id, q)

    return EventSourceResponse(event_generator())


@router.get("/experiments/{exp_id}/export")
def export_experiment(exp_id: str) -> Dict[str, Any]:
    rounds = database.get_rounds(exp_id)
    triage = database.get_triage_items(exp_id)
    return {
        "experiment_id": exp_id,
        "rounds_count": len(rounds),
        "rounds": rounds,
        "triage_reviews": triage,
    }
