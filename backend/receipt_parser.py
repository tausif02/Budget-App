# receipt_parser.py
import re
from datetime import datetime


DATE_PATTERN = re.compile(
    r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2}|\d{4})\b"
)

PRICE_AT_END_PATTERN = re.compile(
    r"(\d+[.,]\d{2})\s*$"
)

MONEY_PATTERN = re.compile(
    r"\$?\s*(\d+(?:,\d{3})*)[.,](\d{2})"
)

WEIGHT_DETAIL_PATTERN = re.compile(
    r"^\s*"
    r"(?P<quantity>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unit>lb|oz|kg|g)\s*@"
    r".*?/\s*\$?"
    r"(?P<unit_price>\d+[.,]\d{2})\s+"
    r"\$?(?P<total_price>\d+[.,]\d{2})"
    r"\s*$",
    re.IGNORECASE,
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
    "amount due",
    "balance due",
}


def money_to_cents(value: str) -> int:
    normalized_value = value.replace(",", ".")

    return round(float(normalized_value) * 100)


def normalize_quantity(value: str) -> float:
    return float(value.replace(",", "."))


def find_merchant(text: str) -> str:
    uppercase_text = text.upper()

    if (
        "WALMART" in uppercase_text
        or "WAL*MART" in uppercase_text
    ):
        return "Walmart"

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return "Unknown Merchant"

    return lines[0][:100].title()


def find_purchase_date(text: str) -> str | None:
    match = DATE_PATTERN.search(text)

    if not match:
        return None

    month, day, year = match.groups()

    date_format = (
        "%m/%d/%Y"
        if len(year) == 4
        else "%m/%d/%y"
    )

    normalized_date = f"{month}/{day}/{year}"

    try:
        parsed_date = datetime.strptime(
            normalized_date,
            date_format,
        )

        return parsed_date.date().isoformat()
    except ValueError:
        return None


def clean_item_name(line_without_price: str) -> str:
    item_name = re.sub(
        r"\b\d{8,14}\b",
        "",
        line_without_price,
    )

    item_name = re.sub(
        r"\s+[A-Z]\s*$",
        "",
        item_name,
    )

    item_name = re.sub(
        r"\s+",
        " ",
        item_name,
    )

    return item_name.strip(" -")


def is_non_item_line(line: str) -> bool:
    lowercase_line = line.lower()

    return any(
        excluded_word in lowercase_line
        for excluded_word in NON_ITEM_WORDS
    )


def parse_weight_detail(
    line: str
) -> dict | None:
    match = WEIGHT_DETAIL_PATTERN.match(line)

    if not match:
        return None

    quantity = normalize_quantity(
        match.group("quantity")
    )

    unit = match.group("unit").lower()

    unit_price_cents = money_to_cents(
        match.group("unit_price")
    )

    total_price_cents = money_to_cents(
        match.group("total_price")
    )

    expected_total_cents = round(
        quantity * unit_price_cents
    )

    price_difference = abs(
        expected_total_cents - total_price_cents
    )

    if price_difference > 2:
        unit_price_cents = round(
            total_price_cents / quantity
        )

    return {
        "quantity": quantity,
        "unit": unit,
        "unit_price_cents": unit_price_cents,
    }


def find_previous_item_name(
    lines: list[str],
    detail_index: int,
    used_name_indexes: set[int],
) -> tuple[int, str] | None:
    for candidate_index in range(
        detail_index - 1,
        -1,
        -1,
    ):
        if candidate_index in used_name_indexes:
            continue

        candidate_line = lines[candidate_index]

        if is_non_item_line(candidate_line):
            continue

        if DATE_PATTERN.search(candidate_line):
            continue

        if PRICE_AT_END_PATTERN.search(candidate_line):
            continue

        item_name = clean_item_name(candidate_line)

        if not item_name:
            continue

        return candidate_index, item_name

    return None


def find_receipt_items(text: str) -> list[dict]:
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]

    parsed_items = []
    used_name_indexes = set()
    weighted_detail_indexes = set()

    for line_index, line in enumerate(lines):
        weight_detail = parse_weight_detail(line)

        if weight_detail is None:
            continue

        previous_item = find_previous_item_name(
            lines=lines,
            detail_index=line_index,
            used_name_indexes=used_name_indexes,
        )

        if previous_item is None:
            continue

        name_index, item_name = previous_item

        used_name_indexes.add(name_index)
        weighted_detail_indexes.add(line_index)

        parsed_items.append(
            (
                name_index,
                {
                    "name": item_name,
                    "quantity": weight_detail["quantity"],
                    "unit": weight_detail["unit"],
                    "unit_price_cents": (
                        weight_detail["unit_price_cents"]
                    ),
                },
            )
        )

    for line_index, normalized_line in enumerate(lines):
        if line_index in used_name_indexes:
            continue

        if line_index in weighted_detail_indexes:
            continue

        if is_non_item_line(normalized_line):
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

        item_name = clean_item_name(
            line_without_price
        )

        if not item_name:
            continue

        parsed_items.append(
            (
                line_index,
                {
                    "name": item_name,
                    "quantity": 1,
                    "unit": "each",
                    "unit_price_cents": money_to_cents(
                        price_text
                    ),
                },
            )
        )

    parsed_items.sort(
        key=lambda parsed_item: parsed_item[0]
    )

    return [
        item
        for _, item in parsed_items
    ]


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

    for label in (
        "TOTAL",
        "AMOUNT DUE",
        "BALANCE DUE",
    ):
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
            round(
                item.get("quantity", 1)
                * item["unit_price_cents"]
            )
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
