from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta
import database
import models
import schemas
import auth
from config import settings
from pdf_generator import generate_statement_pdf
app = FastAPI(title="StatementFlow 2.0")
templates = Jinja2Templates(directory="templates")

# Создание таблиц
models.Base.metadata.create_all(bind=database.engine)

# === Auth Routes ===
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    user = await auth.authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.UserResponse)
async def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(database.get_db)
):
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    
    hashed_password = auth.get_password_hash(user_data.password)
    new_user = models.User(username=user_data.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# === Statement Routes ===
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    statements = db.query(models.Statement).filter(
        models.Statement.user_id == current_user.id
    ).order_by(models.Statement.created_at.desc()).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "statements": statements,
        "current_user": current_user
    })

@app.get("/statements", response_model=List[schemas.StatementResponse])
async def get_statements(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    return db.query(models.Statement).filter(
        models.Statement.user_id == current_user.id
    ).all()

@app.post("/statements", response_model=schemas.StatementResponse)
async def create_statement(
    statement: schemas.StatementCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_statement = models.Statement(
        **statement.dict(),
        user_id=current_user.id,
        status=models.StatementStatus(statement.status.value)
    )
    db.add(db_statement)
    db.commit()
    db.refresh(db_statement)
    return db_statement

@app.get("/statements/{statement_id}", response_model=schemas.StatementResponse)
async def get_statement(
    statement_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    statement = db.query(models.Statement).filter(
        models.Statement.id == statement_id,
        models.Statement.user_id == current_user.id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    return statement

@app.put("/statements/{statement_id}", response_model=schemas.StatementResponse)
async def update_statement(
    statement_id: int,
    statement_update: schemas.StatementUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_statement = db.query(models.Statement).filter(
        models.Statement.id == statement_id,
        models.Statement.user_id == current_user.id
    ).first()
    if not db_statement:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    
    update_data = statement_update.dict(exclude_unset=True)
    if 'status' in update_data:
        update_data['status'] = models.StatementStatus(update_data['status'].value)
        update_data['status_updated_at'] = database.func.now()
    
    for key, value in update_data.items():
        setattr(db_statement, key, value)
    
    db.commit()
    db.refresh(db_statement)
    return db_statement

@app.delete("/statements/{statement_id}")
async def delete_statement(
    statement_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_statement = db.query(models.Statement).filter(
        models.Statement.id == statement_id,
        models.Statement.user_id == current_user.id
    ).first()
    if not db_statement:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    
    db.delete(db_statement)
    db.commit()
    return {"message": "Заявление удалено"}

@app.get("/statements/{statement_id}/pdf")
async def download_pdf(
    statement_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    statement = db.query(models.Statement).filter(
        models.Statement.id == statement_id,
        models.Statement.user_id == current_user.id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    
    pdf_bytes = generate_statement_pdf(statement)
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=statement_{statement_id}.pdf"}
    )

@app.get("/statements/{statement_id}/print", response_class=HTMLResponse)
async def print_view(
    request: Request,
    statement_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    statement = db.query(models.Statement).filter(
        models.Statement.id == statement_id,
        models.Statement.user_id == current_user.id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    
    return templates.TemplateResponse("print_view.html", {
        "request": request,
        "statement": statement
    })

# === Status Update Route ===
@app.patch("/statements/{statement_id}/status")
async def update_status(
    statement_id: int,
    new_status: schemas.StatementStatusEnum,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_statement = db.query(models.Statement).filter(
        models.Statement.id == statement_id,
        models.Statement.user_id == current_user.id
    ).first()
    if not db_statement:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    
    db_statement.status = models.StatementStatus(new_status.value)
    db_statement.status_updated_at = database.func.now()
    db.commit()
    db.refresh(db_statement)
    return db_statement