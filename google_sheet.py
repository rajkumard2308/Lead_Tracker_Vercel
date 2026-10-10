from datetime import date, datetime, timedelta
import json
import os
import re

import gspread
from google.oauth2.service_account import Credentials

from config import SHEET_NAME, WORKSHEET_NAME, HEADERS, HEADER_ALIASES, DATE_FIELDS, EXPECTED_COLUMNS, SCOPES


def _get_service_account_info():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

    if raw:
        try:
            # Standard JSON format
            info = json.loads(raw)
        except json.JSONDecodeError:
            # Also accept Python-dict style credentials
            # such as {'type': 'service_account', ...}
            import ast

            try:
                info = ast.literal_eval(raw)
            except (ValueError, SyntaxError) as exc:
                raise ValueError(
                    "GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON "
                    "or a valid Python dictionary."
                ) from exc

    else:
        # Optional split-variable fallback for Vercel environments.
        info = {
            "type": os.environ.get("GOOGLE_TYPE", "service_account"),
            "project_id": os.environ.get("GOOGLE_PROJECT_ID", ""),
            "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID", ""),
            "private_key": os.environ.get("GOOGLE_PRIVATE_KEY", ""),
            "client_email": os.environ.get("GOOGLE_CLIENT_EMAIL", ""),
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
            "auth_uri": os.environ.get(
                "GOOGLE_AUTH_URI",
                "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": os.environ.get(
                "GOOGLE_TOKEN_URI",
                "https://oauth2.googleapis.com/token"
            ),
            "auth_provider_x509_cert_url": os.environ.get(
                "GOOGLE_AUTH_PROVIDER_X509_CERT_URL",
                "https://www.googleapis.com/oauth2/v1/certs"
            ),
            "client_x509_cert_url": os.environ.get(
                "GOOGLE_CLIENT_X509_CERT_URL",
                ""
            ),
            "universe_domain": os.environ.get(
                "GOOGLE_UNIVERSE_DOMAIN",
                "googleapis.com"
            ),
        }

    key = info.get("private_key", "")

    if "\\n" in key:
        key = key.replace("\\n", "\n")

    info["private_key"] = (
        key.strip() + "\n"
        if key.strip()
        else key
    )

    return info


def _get_client():
    credentials = Credentials.from_service_account_info(_get_service_account_info(), scopes=SCOPES)
    return gspread.authorize(credentials)


def get_worksheet():
    client = _get_client()
    spreadsheet = client.open(os.environ.get("GOOGLE_SHEET_NAME", SHEET_NAME))
    worksheet_name = os.environ.get("GOOGLE_WORKSHEET_NAME", WORKSHEET_NAME)
    try:
        ws = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=max(len(HEADERS), len(EXPECTED_COLUMNS)))
        ws.append_row(HEADERS, value_input_option="RAW")
    ensure_headers(ws)
    return ws


def _norm(header):
    return HEADER_ALIASES.get(str(header).strip().upper(), str(header).strip())


def ensure_headers(ws):
    current = ws.row_values(1)
    if not current:
        ws.update("A1", [HEADERS], value_input_option="RAW")
        return
    normalized = [_norm(h) for h in current]
    missing = [h for h in ["Booking Confirmation Date", "Follow Up Count", "Total Amount"] if h not in normalized]
    if not missing:
        return
    def column_letter(number):
        result = ""
        while number:
            number, remainder = divmod(number - 1, 26)
            result = chr(65 + remainder) + result
        return result
    start = len(current) + 1
    end = start + len(missing) - 1
    ws.update(f"{column_letter(start)}1:{column_letter(end)}1", [missing], value_input_option="RAW")


def _clean(value):
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%d-%m-%Y")
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "nat", "none", "null"} else text


def _parse_date_value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none", "null"}:
        return None
    try:
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            serial = float(text)
            if 20000 <= serial <= 70000:
                return (datetime(1899, 12, 30) + timedelta(days=serial)).date()
    except (ValueError, OverflowError):
        pass
    if " " in text:
        first = text.split(" ", 1)[0]
        if re.fullmatch(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}", first):
            text = first
    slash = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
    if slash:
        a, b = int(slash.group(1)), int(slash.group(2))
        formats = ("%d/%m/%Y", "%d/%m/%y") if not (b > 12 and a <= 12) else ("%m/%d/%Y", "%m/%d/%y")
        for fmt in formats:
            try: return datetime.strptime(text, fmt).date()
            except ValueError: pass
    for fmt in ("%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%y", "%d.%m.%y", "%d %B %Y", "%d %b %Y"):
        try: return datetime.strptime(text, fmt).date()
        except ValueError: pass
    return None


def _normalize_date_value(value):
    parsed = _parse_date_value(value)
    if parsed is not None:
        return parsed.strftime("%d-%m-%Y")
    text = "" if value is None else str(value).strip()
    return "" if text.lower() in {"", "nan", "nat", "none", "null"} else text


def normalize_phone(phone):
    if phone is None:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return digits


def _mapping(headers):
    return {_norm(header): index for index, header in enumerate(headers, start=1)}


def _get_sheet_values():
    ws = get_worksheet()
    return ws.get_all_values(value_render_option="UNFORMATTED_VALUE", date_time_render_option="SERIAL_NUMBER")


def _get_sheet_headers():
    values = _get_sheet_values()
    return list(values[0]) if values else []


def get_leads():
    values = _get_sheet_values()
    if not values or len(values) < 2:
        return []
    headers = [_norm(h) for h in values[0]]
    rows = []
    for row_number, row in enumerate(values[1:], start=2):
        row = row + [""] * max(0, len(headers) - len(row))
        record = {headers[i]: row[i] for i in range(len(headers))}
        if not any(str(v).strip() for v in record.values()):
            continue
        for field in DATE_FIELDS:
            if field in record:
                record[field] = _normalize_date_value(record[field])
        for col in EXPECTED_COLUMNS:
            record.setdefault(col, "")
        record["_sheet_row"] = row_number
        rows.append({c: record.get(c, "") for c in EXPECTED_COLUMNS} | {"_sheet_row": row_number})
    return rows


def _phone_exists(phone, exclude_row=None):
    normalized = normalize_phone(phone)
    if not normalized:
        return False
    values = _get_sheet_values()
    if not values:
        return False
    mapping = _mapping(values[0])
    phone_col = mapping.get("Number")
    if not phone_col:
        return False
    for sheet_row, row in enumerate(values[1:], start=2):
        if exclude_row is not None and sheet_row == int(exclude_row):
            continue
        if len(row) >= phone_col and normalize_phone(row[phone_col - 1]) == normalized:
            return True
    return False


def add_lead(lead):
    ws = get_worksheet()
    values = _get_sheet_values()
    headers = list(values[0]) if values else list(HEADERS)
    mapping = _mapping(headers)
    if _phone_exists(lead.get("Number", "")):
        raise ValueError("Phone number already exists. This customer is already present.")
    row = [""] * len(headers)
    for field, value in lead.items():
        if not field.startswith("__") and mapping.get(field):
            row[mapping[field] - 1] = _clean(value)
    ws.append_row(row, value_input_option="RAW")
    return True


def add_leads_bulk(leads):
    if not leads: return 0
    ws = get_worksheet()
    values = _get_sheet_values()
    headers = list(values[0]) if values else list(HEADERS)
    mapping = _mapping(headers)
    existing = set()
    phone_col = mapping.get("Number")
    if values and phone_col:
        for row in values[1:]:
            if len(row) >= phone_col:
                p = normalize_phone(row[phone_col - 1])
                if p: existing.add(p)
    rows, batch = [], set()
    for lead in leads:
        phone = normalize_phone(lead.get("Number", ""))
        if phone and (phone in existing or phone in batch):
            raise ValueError(f"Duplicate phone number found during bulk insert: {phone}")
        row = [""] * len(headers)
        for field, value in lead.items():
            if not field.startswith("__") and mapping.get(field):
                row[mapping[field] - 1] = _clean(value)
        rows.append(row)
        if phone: batch.add(phone)
    ws.append_rows(rows, value_input_option="RAW")
    return len(rows)


def update_lead(row_number, updates):
    ws = get_worksheet()
    row_number = int(row_number)
    if row_number < 2: raise ValueError("Invalid row number. Header row cannot be updated.")
    values = _get_sheet_values()
    if not values: raise ValueError("Google Sheet data could not be read.")
    headers = list(values[0]); mapping = _mapping(headers)
    if "Number" in updates and _phone_exists(updates.get("Number", ""), exclude_row=row_number):
        raise ValueError("Phone number already exists for another customer.")
    row_index = row_number - 1
    if row_index >= len(values): raise ValueError("The selected lead no longer exists in Google Sheets.")
    current = list(values[row_index])
    current += [""] * max(0, len(headers) - len(current))
    current = current[:len(headers)]
    for field, value in updates.items():
        if not field.startswith("__") and mapping.get(field):
            current[mapping[field] - 1] = _clean(value)
    def col(n):
        s=""
        while n:
            n,r=divmod(n-1,26); s=chr(65+r)+s
        return s
    ws.update(f"A{row_number}:{col(len(headers))}{row_number}", [current], value_input_option="RAW")
    return True


def delete_lead(row_number):
    row_number = int(row_number)
    if row_number < 2: raise ValueError("Invalid row number. Header row cannot be deleted.")
    get_worksheet().delete_rows(row_number)
    return True
