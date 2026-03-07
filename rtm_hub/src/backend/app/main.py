from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse

from . import models, schemas, crud
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RTM Hub API",
    description="API для управления требованиями и матрицей трассируемости",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/requirements", response_model=schemas.Requirement, status_code=201)
def create_requirement(req: schemas.RequirementCreate, db: Session = Depends(get_db)):
    return crud.create_requirement(db=db, req=req)

@app.get("/api/v1/requirements", response_model=List[schemas.Requirement])
def read_requirements(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return crud.get_requirements(db=db, skip=skip, limit=limit, 
                                  status=status, priority=priority, search=search)

@app.get("/api/v1/requirements/{req_id}", response_model=schemas.Requirement)
def read_requirement(req_id: str, db: Session = Depends(get_db)):
    db_req = crud.get_requirement_by_id(db=db, req_id=req_id)
    if db_req is None:
        raise HTTPException(status_code=404, detail="Требование не найдено")
    return db_req

@app.put("/api/v1/requirements/{req_id}", response_model=schemas.Requirement)
def update_requirement(req_id: str, req: schemas.RequirementUpdate, db: Session = Depends(get_db)):
    db_req = crud.get_requirement_by_id(db=db, req_id=req_id)
    if db_req is None:
        raise HTTPException(status_code=404, detail="Требование не найдено")
    
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_req, key, value)
    
    db.commit()
    db.refresh(db_req)
    return db_req

@app.post("/api/v1/requirements/{req_id}/links", response_model=schemas.TraceabilityLink)
def create_link(req_id: str, link: schemas.TraceabilityLinkCreate, db: Session = Depends(get_db)):
    db_req = crud.get_requirement_by_id(db=db, req_id=req_id)
    if db_req is None:
        raise HTTPException(status_code=404, detail="Требование не найдено")
    return crud.create_traceability_link(db=db, from_req_id=db_req.id, link=link)

@app.get("/api/v1/rtm/export")
def export_rtm(db: Session = Depends(get_db)):
    rtm_data = crud.get_rtm_matrix(db=db)
    df = pd.DataFrame(rtm_data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='RTM')
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=rtm_export.xlsx"}
    )

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}