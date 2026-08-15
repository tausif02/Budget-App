# models.py
from sqlalchemy import Column, Integer, String, Date, DateTime
from datetime import datetime

from database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)

    amount_cents = Column(Integer, nullable=False)

    category = Column(String, nullable=False)

    merchant = Column(String, nullable=True)

    description = Column(String, nullable=True)

    purchase_date = Column(Date, nullable=False)

    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.now)


class MonthlyBudget(Base):
    __tablename__ = "monthly_budgets"

    id = Column(Integer, primary_key=True, index=True)

    month = Column(
        String(7),
        unique=True,
        nullable=False,
        index=True
    )

    amount_cents = Column(Integer, nullable=False)

    created_at = Column(
        DateTime,
        default=datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )
