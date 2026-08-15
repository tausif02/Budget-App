# schemas.py
from pydantic import BaseModel, Field
from datetime import date


class ExpenseCreate(BaseModel):
    amount_cents: int = Field(gt=0)
    category: str = Field(min_length=1)
    merchant: str | None = None
    description: str | None = None
    purchase_date: date
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    amount_cents: int = Field(gt=0)
    category: str = Field(min_length=1)
    merchant: str | None = None
    description: str | None = None
    purchase_date: date
    notes: str | None = None


class ExpenseResponse(ExpenseCreate):
    id: int

    class Config:
        from_attributes = True


class MonthlyBudgetUpsert(BaseModel):
    amount_cents: int = Field(gt=0)


class MonthlyBudgetResponse(MonthlyBudgetUpsert):
    id: int
    month: str

    class Config:
        from_attributes = True
