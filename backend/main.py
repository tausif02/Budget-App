# main.py
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Path,
    Query,
    File,
    UploadFile,
)

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from document_extractor import extract_document_text
from receipt_parser import parse_receipt

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


@app.put(
    "/budgets/{budget_month}",
    response_model=schemas.MonthlyBudgetResponse
)
def upsert_monthly_budget(
    budget_data: schemas.MonthlyBudgetUpsert,
    budget_month: str = Path(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    ),
    db: Session = Depends(get_db)
):
    monthly_budget = (
        db.query(models.MonthlyBudget)
        .filter(models.MonthlyBudget.month == budget_month)
        .first()
    )

    if monthly_budget is None:
        monthly_budget = models.MonthlyBudget(
            month=budget_month,
            amount_cents=budget_data.amount_cents
        )

        db.add(monthly_budget)
    else:
        monthly_budget.amount_cents = budget_data.amount_cents

    db.commit()
    db.refresh(monthly_budget)

    return monthly_budget


@app.get(
    "/budgets/{budget_month}",
    response_model=schemas.MonthlyBudgetResponse
)
def get_monthly_budget(
    budget_month: str = Path(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    ),
    db: Session = Depends(get_db)
):
    monthly_budget = (
        db.query(models.MonthlyBudget)
        .filter(models.MonthlyBudget.month == budget_month)
        .first()
    )

    if monthly_budget is None:
        raise HTTPException(
            status_code=404,
            detail="Monthly budget not found"
        )

    return monthly_budget


@app.post(
    "/expenses/{expense_id}/items",
    response_model=schemas.ExpenseItemResponse
)
def create_expense_item(
    expense_id: int,
    item: schemas.ExpenseItemCreate,
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

    new_item = models.ExpenseItem(
        expense_id=expense_id,
        name=item.name,
        quantity=item.quantity,
        unit=item.unit,
        unit_price_cents=item.unit_price_cents
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@app.get(
    "/expenses/{expense_id}/items",
    response_model=list[schemas.ExpenseItemResponse]
)
def get_expense_items(
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

    items = (
        db.query(models.ExpenseItem)
        .filter(models.ExpenseItem.expense_id == expense_id)
        .order_by(models.ExpenseItem.id.asc())
        .all()
    )

    return items


@app.put(
    "/expenses/{expense_id}/items/{item_id}",
    response_model=schemas.ExpenseItemResponse
)
def update_expense_item(
    expense_id: int,
    item_id: int,
    updated_item: schemas.ExpenseItemUpdate,
    db: Session = Depends(get_db)
):
    item = (
        db.query(models.ExpenseItem)
        .filter(
            models.ExpenseItem.id == item_id,
            models.ExpenseItem.expense_id == expense_id
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Expense item not found"
        )

    item.name = updated_item.name.strip()
    item.quantity = updated_item.quantity
    item.unit = updated_item.unit
    item.unit_price_cents = updated_item.unit_price_cents

    db.commit()
    db.refresh(item)

    return item


@app.delete("/expenses/{expense_id}/items/{item_id}")
def delete_expense_item(
    expense_id: int,
    item_id: int,
    db: Session = Depends(get_db)
):
    item = (
        db.query(models.ExpenseItem)
        .filter(
            models.ExpenseItem.id == item_id,
            models.ExpenseItem.expense_id == expense_id
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Expense item not found"
        )

    db.delete(item)
    db.commit()

    return {"message": "Expense item deleted"}


@app.get(
    "/items/price-summaries",
    response_model=list[schemas.ItemPriceSummaryResponse]
)
def get_item_price_summaries(
    db: Session = Depends(get_db)
):
    results = (
        db.query(models.ExpenseItem, models.Expense)
        .join(
            models.Expense,
            models.Expense.id == models.ExpenseItem.expense_id
        )
        .order_by(
            func.lower(models.ExpenseItem.name).asc(),
            func.lower(models.ExpenseItem.unit).asc(),
            models.Expense.purchase_date.desc(),
            models.ExpenseItem.id.desc()
        )
        .all()
    )

    grouped_purchases = {}

    for item, expense in results:
        normalized_name = item.name.strip().lower()
        normalized_unit = item.unit.strip().lower()
        group_key = (normalized_name, normalized_unit)

        if group_key not in grouped_purchases:
            grouped_purchases[group_key] = []

        grouped_purchases[group_key].append((item, expense))

    summaries = []

    for purchases in grouped_purchases.values():
        latest_item, latest_expense = purchases[0]

        previous_item = (
            purchases[1][0]
            if len(purchases) > 1
            else None
        )

        previous_price_cents = (
            previous_item.unit_price_cents
            if previous_item is not None
            else None
        )

        price_change_cents = (
            latest_item.unit_price_cents - previous_price_cents
            if previous_price_cents is not None
            else None
        )

        price_change_percent = (
            round(
                (price_change_cents / previous_price_cents) * 100,
                1
            )
            if previous_price_cents is not None
            and previous_price_cents > 0
            else None
        )

        summaries.append(
            {
                "name": latest_item.name,
                "unit": latest_item.unit,
                "purchase_count": len(purchases),
                "latest_unit_price_cents": (
                    latest_item.unit_price_cents
                ),
                "previous_unit_price_cents": previous_price_cents,
                "price_change_cents": price_change_cents,
                "price_change_percent": price_change_percent,
                "latest_merchant": latest_expense.merchant,
                "latest_purchase_date": latest_expense.purchase_date
            }
        )

    return sorted(
        summaries,
        key=lambda summary: summary["latest_purchase_date"],
        reverse=True
    )


@app.get(
    "/items/price-history",
    response_model=list[schemas.ItemPriceHistoryResponse]
)
def get_item_price_history(
    name: str = Query(min_length=1),
    db: Session = Depends(get_db)
):
    normalized_name = name.strip().lower()

    results = (
        db.query(models.ExpenseItem, models.Expense)
        .join(
            models.Expense,
            models.Expense.id == models.ExpenseItem.expense_id
        )
        .filter(
            func.lower(models.ExpenseItem.name) == normalized_name
        )
        .order_by(
            models.Expense.purchase_date.desc(),
            models.ExpenseItem.id.desc()
        )
        .all()
    )

    return [
        {
            "item_id": item.id,
            "expense_id": expense.id,
            "name": item.name,
            "quantity": item.quantity,
            "unit": item.unit,
            "unit_price_cents": item.unit_price_cents,
            "merchant": expense.merchant,
            "purchase_date": expense.purchase_date
        }
        for item, expense in results
    ]


ALLOWED_DOCUMENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10 MB


@app.post("/imports/extract")
async def extract_uploaded_document(
    file: UploadFile = File(...)
):
    filename = file.filename

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must have a filename"
        )

    if file.content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only PDF, JPG, JPEG, and PNG files are supported"
        )

    try:
        # Reading one extra byte lets us detect an oversized file.
        file_bytes = await file.read(MAX_DOCUMENT_SIZE + 1)
    finally:
        await file.close()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty"
        )

    if len(file_bytes) > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The uploaded file cannot exceed 10 MB"
        )

    try:
        extracted_text = extract_document_text(
            filename=filename,
            file_bytes=file_bytes
        )
    except ValueError as error:
        raise HTTPException(
            status_code=415,
            detail=str(error)
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail="The document could not be read"
        ) from error

    if not extracted_text:
        raise HTTPException(
            status_code=422,
            detail="No readable text was found in the document"
        )

    suggested_transaction = parse_receipt(extracted_text)

    return {
        "filename": filename,
        "content_type": file.content_type,
        "character_count": len(extracted_text),
        "extracted_text": extracted_text,
        "suggested_transaction": suggested_transaction,
    }
