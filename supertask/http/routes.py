# ruff: noqa: B008
import logging
import typing as t
from pathlib import Path

import fastapi.responses
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from supertask.model import CronJob, Settings
from supertask.provision.database import JsonResource

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def get_json_resource(settings: Settings = Depends()) -> JsonResource:
    """
    FastAPI Dependency to provide a JsonResource instance to the request handlers.
    """
    from supertask.provision.database import JsonResource

    if settings.pre_seed_jobs is None:
        msg = "No web UI without pre-seed file"
        logger.error(msg)
        raise fastapi.exceptions.HTTPException(status_code=400, detail=msg)
    return JsonResource(filepath=settings.pre_seed_jobs)


@router.get("/", response_class=HTMLResponse)
async def jobs_page(request: Request, json_resource: JsonResource = Depends(get_json_resource)):
    jobs = json_resource.read_index()
    path = Path(__file__).parent / "templates"
    tmpl = Jinja2Templates(path)
    return tmpl.TemplateResponse("jobs.html", {"request": request, "jobs": jobs})


@router.post("/cronjobs/", response_model=CronJob)
def create_cronjob(
    name: str = Form(...),
    crontab: str = Form(...),
    enabled: bool = Form(False),
    json_resource: JsonResource = Depends(get_json_resource),
):
    db = json_resource.read()
    cronjob = CronJob(id=len(db) + 1, name=name, trigger_cron=crontab, enabled=enabled, last_run=None, last_status=None)
    db.append(cronjob)
    json_resource.write(db)
    return cronjob


@router.get("/cronjobs/", response_model=t.List[CronJob])
def read_cronjobs(json_resource: JsonResource = Depends(get_json_resource)):
    db = json_resource.read()
    return db


@router.get("/cronjobs/{cronjob_id}", response_model=CronJob)
def read_cronjob(cronjob_id: int, json_resource: JsonResource = Depends(get_json_resource)):
    db = json_resource.read()
    if cronjob_id < 0 or cronjob_id >= len(db):
        raise HTTPException(status_code=404, detail="CronJob not found")
    return db[cronjob_id]


@router.put("/cronjobs/{cronjob_id}", response_model=CronJob)
def update_cronjob(cronjob_id: int, cronjob: CronJob, json_resource: JsonResource = Depends(get_json_resource)):
    db = json_resource.read()
    if cronjob_id < 0 or cronjob_id >= len(db):
        raise HTTPException(status_code=404, detail="CronJob not found")
    db[cronjob_id] = cronjob
    json_resource.write(db)
    return cronjob


@router.delete("/cronjobs/{cronjob_id}", response_model=CronJob)
def delete_cronjob(cronjob_id: int, json_resource: JsonResource = Depends(get_json_resource)):
    db = json_resource.read()
    cronjob = next((x for x in db if x.id == cronjob_id), None)
    if cronjob is None:
        raise HTTPException(status_code=404, detail="CronJob not found")
    db.remove(cronjob)
    json_resource.write(db)
    return cronjob
