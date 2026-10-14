import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .digest_builder import build_digest
from .infrai_client import InfraiClient, InfraiError
from .models import DigestRequest, DigestResult, ScheduleRequest, ScheduleResult


app = FastAPI(title="Marketplace weekly digest")


@app.post("/digests/render", response_model=DigestResult)
def render_digest(request: DigestRequest) -> DigestResult:
    return build_digest(request)


@app.post("/tasks/weekly-marketplace-digest", response_model=DigestResult)
def run_weekly_digest() -> DigestResult:
    default_input = Path(__file__).parents[2] / "examples" / "weekly_digest.json"
    input_path = Path(os.environ.get("DIGEST_INPUT_PATH", default_input))
    request = DigestRequest.model_validate(json.loads(input_path.read_text()))
    result = build_digest(request)
    print(result.model_dump_json())
    return result


@app.post("/schedules", response_model=ScheduleResult)
def register_schedule(request: ScheduleRequest) -> ScheduleResult:
    try:
        data = InfraiClient().cron_create(
            cron_expr=request.cron_expr,
            task=request.task_url,
        )
    except InfraiError as exc:
        client_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=client_status, detail=exc.error) from exc

    return ScheduleResult(job_id=str(data["job_id"]))
