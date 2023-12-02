from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from models import CronJob
from typing import List
from database import get_db, write_db, CRONJOBS_JSON
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")

from fastapi import Form

@router.post("/cronjobs/", response_model=CronJob)
def create_cronjob(crontab: str = Form(...), job: str = Form(...), enabled: bool = Form(False), db=Depends(get_db)):
    cronjob = CronJob(id=len(db)+1, crontab=crontab, job=job, enabled=enabled, last_run=None, last_status=None)
    db.append(cronjob)
    write_db(db)
    return cronjob


@router.get("/cronjobs/", response_model=List[CronJob])
def read_cronjobs(db=Depends(get_db)):
    return db

@router.get("/cronjobs/{cronjob_id}", response_model=CronJob)
def read_cronjob(cronjob_id: int, db=Depends(get_db)):
    if cronjob_id < 0 or cronjob_id >= len(db):
        raise HTTPException(status_code=404, detail="CronJob not found")
    return db[cronjob_id]

@router.put("/cronjobs/{cronjob_id}", response_model=CronJob)
def update_cronjob(cronjob_id: int, cronjob: CronJob, db=Depends(get_db)):
    if cronjob_id < 0 or cronjob_id >= len(db):
        raise HTTPException(status_code=404, detail="CronJob not found")
    db[cronjob_id] = cronjob
    write_db(db)
    return cronjob

@router.delete("/cronjobs/{cronjob_id}", response_model=CronJob)
def delete_cronjob(cronjob_id: int, db=Depends(get_db)):
    cronjob = next((x for x in db if x.id == cronjob_id), None)
    if cronjob is None:
        raise HTTPException(status_code=404, detail="CronJob not found")
    db.remove(cronjob)
    write_db(db)
    return cronjob

@router.get("/", response_class=HTMLResponse)
async def jobs_page(request: Request):
    with open(CRONJOBS_JSON) as f:
        data = json.load(f)
    jobs = [CronJob(**job) for job in data]
    return templates.TemplateResponse("jobs.html", {"request": request, "jobs": jobs})
