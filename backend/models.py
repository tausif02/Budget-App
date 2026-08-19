# models.py
from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    amount_cents = Column(
        Integer,
        nullable=False,
    )

    category = Column(
        String,
        nullable=False,
    )

    merchant = Column(
        String,
        nullable=True,
    )

    description = Column(
        String,
        nullable=True,
    )

    purchase_date = Column(
        Date,
        nullable=False,
    )

    notes = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

    items = relationship(
        "ExpenseItem",
        back_populates="expense",
        cascade="all, delete-orphan",
    )


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    expense_id = Column(
        Integer,
        ForeignKey(
            "expenses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
        index=True,
    )

    quantity = Column(
        Float,
        nullable=False,
        default=1.0,
    )

    unit = Column(
        String,
        nullable=False,
        default="each",
    )

    unit_price_cents = Column(
        Integer,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

    expense = relationship(
        "Expense",
        back_populates="items",
    )


class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    month = Column(
        String(7),
        unique=True,
        nullable=False,
        index=True,
    )

    amount_cents = Column(
        Integer,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )


class ItemNameAlias(Base):
    __tablename__ = "item_name_aliases"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    raw_name = Column(
        String,
        nullable=False,
    )

    normalized_raw_name = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    canonical_name = Column(
        String,
        nullable=False,
    )

    normalized_canonical_name = Column(
        String,
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
    )
