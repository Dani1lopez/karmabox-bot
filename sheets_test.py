import gspread
from datetime import datetime, timezone

SHEET_NAME = "KarmaBox Leads"

gc = gspread.service_account(filename="secrets/service_account.json")
sh = gc.open(SHEET_NAME)
ws = sh.sheet1

ws.append_row([
    "test-id",
    datetime.now(timezone.utc).isoformat(),
    "Test",
    "User",
    "600000000",
    "Calle Test"
])

print("OK: fila añadida")