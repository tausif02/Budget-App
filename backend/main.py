# main.py
import re
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


def normalize_item_name(value: str) -> str:
    normalized_value = value.casefold().strip()

    normalized_value = re.sub(
        r"[\W_]+",
        " ",
        normalized_value
    )

    normalized_value = re.sub(
        r"\s+",
        " ",
        normalized_value
    )

    return normalized_value.strip()


def get_item_alias_map(
    db: Session
) -> dict[str, models.ItemNameAlias]:
    aliases = db.query(models.ItemNameAlias).all()

    return {
        alias.normalized_raw_name: alias
        for alias in aliases
    }


def resolve_item_name(
    item_name: str,
    alias_map: dict[str, models.ItemNameAlias]
) -> tuple[str, str]:
    display_name = item_name.strip()
    normalized_name = normalize_item_name(display_name)
    visited_names = set()

    while (
        normalized_name in alias_map
        and normalized_name not in visited_names
    ):
        visited_names.add(normalized_name)

        item_alias = alias_map[normalized_name]

        display_name = item_alias.canonical_name
        normalized_name = (
            item_alias.normalized_canonical_name
        )

    return display_name, normalized_name


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


@app.put(
    "/items/name-aliases",
    response_model=schemas.ItemNameAliasResponse
)
def upsert_item_name_alias(
    alias_data: schemas.ItemNameAliasUpsert,
    db: Session = Depends(get_db)
):
    raw_name = alias_data.raw_name.strip()
    canonical_name = alias_data.canonical_name.strip()

    normalized_raw_name = normalize_item_name(raw_name)
    normalized_canonical_name = normalize_item_name(
        canonical_name
    )

    if not normalized_raw_name:
        raise HTTPException(
            status_code=400,
            detail="Raw item name cannot be empty"
        )

    if not normalized_canonical_name:
        raise HTTPException(
            status_code=400,
            detail="Canonical item name cannot be empty"
        )

    item_alias = (
        db.query(models.ItemNameAlias)
        .filter(
            models.ItemNameAlias.normalized_raw_name
            == normalized_raw_name
        )
        .first()
    )

    if item_alias is None:
        item_alias = models.ItemNameAlias(
            raw_name=raw_name,
            normalized_raw_name=normalized_raw_name,
            canonical_name=canonical_name,
            normalized_canonical_name=(
                normalized_canonical_name
            )
        )

        db.add(item_alias)
    else:
        item_alias.raw_name = raw_name
        item_alias.canonical_name = canonical_name
        item_alias.normalized_canonical_name = (
            normalized_canonical_name
        )

    db.commit()
    db.refresh(item_alias)

    return item_alias


@app.get(
    "/items/name-aliases",
    response_model=list[schemas.ItemNameAliasResponse]
)
def get_item_name_aliases(
    db: Session = Depends(get_db)
):
    aliases = (
        db.query(models.ItemNameAlias)
        .order_by(
            models.ItemNameAlias.canonical_name.asc(),
            models.ItemNameAlias.raw_name.asc()
        )
        .all()
    )

    return aliases


@app.delete("/items/name-aliases/{alias_id}")
def delete_item_name_alias(
    alias_id: int,
    db: Session = Depends(get_db)
):
    item_alias = (
        db.query(models.ItemNameAlias)
        .filter(models.ItemNameAlias.id == alias_id)
        .first()
    )

    if item_alias is None:
        raise HTTPException(
            status_code=404,
            detail="Item-name alias not found"
        )

    db.delete(item_alias)
    db.commit()

    return {"message": "Item-name alias deleted"}


@app.get(
    "/items/price-summaries",
    response_model=list[schemas.ItemPriceSummaryResponse]
)
@app.get(
    "/items/price-summaries",
    response_model=list[schemas.ItemPriceSummaryResponse]
)
def get_item_price_summaries(
    db: Session = Depends(get_db)
):
    alias_map = get_item_alias_map(db)

    results = (
        db.query(models.ExpenseItem, models.Expense)
        .join(
            models.Expense,
            models.Expense.id == models.ExpenseItem.expense_id
        )
        .order_by(
            models.Expense.purchase_date.desc(),
            models.ExpenseItem.id.desc()
        )
        .all()
    )

    grouped_purchases = {}

    for item, expense in results:
        canonical_name, normalized_name = resolve_item_name(
            item.name,
            alias_map
        )

        normalized_unit = normalize_item_name(item.unit)
        group_key = (normalized_name, normalized_unit)

        if group_key not in grouped_purchases:
            grouped_purchases[group_key] = {
                "name": canonical_name,
                "unit": item.unit.strip(),
                "purchases": [],
            }

        grouped_purchases[group_key]["purchases"].append(
            (item, expense)
        )

    summaries = []

    for group in grouped_purchases.values():
        purchases = group["purchases"]

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
                "name": group["name"],
                "unit": group["unit"],
                "purchase_count": len(purchases),
                "latest_unit_price_cents": (
                    latest_item.unit_price_cents
                ),
                "previous_unit_price_cents": previous_price_cents,
                "price_change_cents": price_change_cents,
                "price_change_percent": price_change_percent,
                "latest_merchant": latest_expense.merchant,
                "latest_purchase_date": (
                    latest_expense.purchase_date
                ),
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
    unit: str | None = Query(
        default=None,
        min_length=1
    ),
    db: Session = Depends(get_db)
):
    alias_map = get_item_alias_map(db)

    _, requested_normalized_name = resolve_item_name(
        name,
        alias_map
    )

    requested_normalized_unit = (
        normalize_item_name(unit)
        if unit is not None
        else None
    )

    results = (
        db.query(models.ExpenseItem, models.Expense)
        .join(
            models.Expense,
            models.Expense.id == models.ExpenseItem.expense_id
        )
        .order_by(
            models.Expense.purchase_date.desc(),
            models.ExpenseItem.id.desc()
        )
        .all()
    )

    history = []

    for item, expense in results:
        canonical_name, normalized_name = resolve_item_name(
            item.name,
            alias_map
        )

        normalized_unit = normalize_item_name(item.unit)

        if normalized_name != requested_normalized_name:
            continue

        if (
            requested_normalized_unit is not None
            and normalized_unit != requested_normalized_unit
        ):
            continue

        history.append(
            {
                "item_id": item.id,
                "expense_id": expense.id,
                "name": canonical_name,
                "quantity": item.quantity,
                "unit": item.unit,
                "unit_price_cents": item.unit_price_cents,
                "merchant": expense.merchant,
                "purchase_date": expense.purchase_date,
            }
        )

    return history


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
