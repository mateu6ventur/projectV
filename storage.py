import csv
import os
from scrapers import SkiResort


# =========================
# CONFIGURACIÓ CSV
# =========================

CSV_HEADERS = [
    "date",
    "station",
    "km_open",
    "km_total",
    "slopes_open",
    "slopes_total",
    "lifts_open",
    "lifts_total",
    "temp_min",
    "temp_max",
    "precip_mm",
]


# =========================
# FUNCIONS D'EMMAGATZEMATGE
# =========================

def get_csv_path() -> str:
    """Retorna la ruta del fitxer CSV, creant la carpeta /data si cal."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "ski_data.csv")


def save_resort(resort: SkiResort, date, file_path: str) -> None:
    """Afegeix una fila al CSV per a una estació. Crea el fitxer amb capçalera si no existeix."""
    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(CSV_HEADERS)
        writer.writerow(resort.to_csv_row(date))