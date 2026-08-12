from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, SessionLocal
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "Budget API is running"}

@app.post("/expenses", response_model=schemas.ExpenseResponse)
def create_expense(
    expense: schemas.ExpenseCreate,
    db: Session = Depends(get_db)
):
    new_expense = models.Expense(
        amount_cents=expense.amount_cents,
        category=expense.category,
        merchant=expense.merchant,
        description=expense.description,
        purchase_date=expense.purchase_date,
        notes=expense.notes
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return new_expense


@app.get("/expenses", response_model=list[schemas.ExpenseResponse])
def get_expenses(db: Session = Depends(get_db)):
    expenses = (
        db.query(models.Expense)
        .order_by(models.Expense.purchase_date.desc())
        .all()
    )
    
    return expenses


@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):
    expense = (
        db.query(models.Expense)
        .filter(models.Expense.id == expense_id)
        .first()
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    db.delete(expense)
    db.commit()

    return {"message": "Expense deleted"}

@app.put("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def update_expense(
    expense_id: int,
    updated_expense: schemas.ExpenseUpdate,
    db: Session = Depends(get_db)
):
    expense = (
        db.query(models.Expense)
        .filter(models.Expense.id == expense_id)
        .first()
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    expense.amount_cents = updated_expense.amount_cents
    expense.category = updated_expense.category
    expense.merchant = updated_expense.merchant
    expense.description = updated_expense.description
    expense.purchase_date = updated_expense.purchase_date
    expense.notes = updated_expense.notes

    db.commit()
    db.refresh(expense)

    return expense

@app.get("/expenses/{expense_id}", response_model=schemas.ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):
    expense = (
        db.query(models.Expense)
        .filter(models.Expense.id == expense_id)
        .first()
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found"
        )

    return expense
