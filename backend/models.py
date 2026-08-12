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
