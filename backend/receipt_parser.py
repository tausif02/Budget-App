# receipt_parser.py

import re
from datetime import datetime


TOTAL_PATTERN = re.compile(
    r"^\s*TOTAL\b.*?(\d+[.,]\d{2})\s*$",
    re.IGNORECASE
)

DATE_PATTERN = re.compile(
    r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2}|\d{4})\b"
)

PRICE_AT_END_PATTERN = re.compile(
    r"(\d+[.,]\d{2})\s*$"
)

NON_ITEM_WORDS = {
    "subtotal",
    "total",
    "tax",
    "change",
    "tender",
    "credit",
    "debit",
    "items sold",
}


def money_to_cents(value: str) -> int:
    normalized_value = value.replace(",", ".")

    return round(float(normalized_value) * 100)


def find_merchant(text: str) -> str:
    uppercase_text = text.upper()

    if "WALMART" in uppercase_text or "WAL*MART" in uppercase_text:
        return "Walmart"

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return "Unknown Merchant"

    return lines[0][:100].title()


def find_total_cents(text: str) -> int | None:
    lines = text.splitlines()

    for line in reversed(lines):
        match = TOTAL_PATTERN.search(line)

        if match:
            return money_to_cents(match.group(1))

    return None


def find_purchase_date(text: str) -> str | None:
    match = DATE_PATTERN.search(text)

    if not match:
        return None

    month, day, year = match.groups()

    date_format = "%m/%d/%Y" if len(year) == 4 else "%m/%d/%y"
    normalized_date = f"{month}/{day}/{year}"

    try:
        parsed_date = datetime.strptime(
            normalized_date,
            date_format
        )

        return parsed_date.date().isoformat()
    except ValueError:
        return None


def clean_item_name(line_without_price: str) -> str:
    item_name = re.sub(
        r"\b\d{8,14}\b",
        "",
        line_without_price
    )

    item_name = re.sub(
        r"\s+[A-Z]\s*$",
        "",
        item_name
    )

    item_name = re.sub(r"\s+", " ", item_name)

    return item_name.strip(" -")


def find_receipt_items(text: str) -> list[dict]:
    items = []

    for line in text.splitlines():
        normalized_line = line.strip()

        if not normalized_line:
            continue

        lowercase_line = normalized_line.lower()

        if any(
            excluded_word in lowercase_line
            for excluded_word in NON_ITEM_WORDS
        ):
            continue

        price_match = PRICE_AT_END_PATTERN.search(
            normalized_line
        )

        if not price_match:
            continue

        price_text = price_match.group(1)
        line_without_price = normalized_line[
            :price_match.start()
        ]

        item_name = clean_item_name(line_without_price)

        if not item_name:
            continue

        items.append({
            "name": item_name,
            "quantity": 1,
            "unit": "each",
            "unit_price_cents": money_to_cents(price_text),
        })

    return items


MONEY_PATTERN = re.compile(
    r"\$?\s*(\d+(?:,\d{3})*)[.,](\d{2})"
)


def amount_from_line(line: str) -> int | None:
    matches = MONEY_PATTERN.findall(line)

    if not matches:
        return None

    dollars, cents = matches[-1]

    return (
        int(dollars.replace(",", "")) * 100
        + int(cents)
    )


def extract_receipt_total(text: str) -> int:
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for label in ("TOTAL", "AMOUNT DUE", "BALANCE DUE"):
        for line in lines:
            if re.match(
                rf"^{re.escape(label)}\b",
                line,
                flags=re.IGNORECASE,
            ):
                amount_cents = amount_from_line(line)

                if amount_cents is not None:
                    return amount_cents

    for line in lines:
        if re.match(
            r"^SUBTOTAL\b",
            line,
            flags=re.IGNORECASE,
        ):
            amount_cents = amount_from_line(line)

            if amount_cents is not None:
                return amount_cents

    return 0


def parse_receipt(text: str) -> dict:
    items = find_receipt_items(text)
    amount_cents = extract_receipt_total(text)

    if amount_cents == 0 and items:
        amount_cents = sum(
            item.get("quantity", 1)
            * item["unit_price_cents"]
            for item in items
        )

    return {
        "merchant": find_merchant(text),
        "amount_cents": amount_cents,
        "purchase_date": find_purchase_date(text),
        "category": "Other",
        "description": "Imported from receipt",
        "notes": None,
        "items": items,
    }
