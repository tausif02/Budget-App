# schemas.py
from datetime import date

from pydantic import BaseModel, Field


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


class ExpenseItemCreate(BaseModel):
    name: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit: str = Field(
        default="each",
        min_length=1,
    )
    unit_price_cents: int = Field(gt=0)


class ExpenseItemUpdate(BaseModel):
    name: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1)
    unit_price_cents: int = Field(gt=0)


class ExpenseItemResponse(ExpenseItemCreate):
    id: int
    expense_id: int

    class Config:
        from_attributes = True


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


class ItemPriceHistoryResponse(BaseModel):
    item_id: int
    expense_id: int
    name: str
    quantity: float
    unit: str
    unit_price_cents: int
    merchant: str | None
    purchase_date: date


class ItemPriceSummaryResponse(BaseModel):
    name: str
    unit: str
    purchase_count: int
    latest_unit_price_cents: int
    previous_unit_price_cents: int | None
    price_change_cents: int | None
    price_change_percent: float | None
    latest_merchant: str | None
    latest_purchase_date: date
