import requests
from datetime import datetime

from scrapers import STATIONS, scrape_weather, scrape_ski_status
from storage import get_csv_path, save_resort


# =========================
# PIPELINE PRINCIPAL
# =========================

def process_resort(resort, date, file_path):
    """Processa una estació: scraping, validació i guardada."""
    print(f"\n  Scraping weather...")
    scrape_weather(resort)

    print(f"  Scraping ski status...")
    scrape_ski_status(resort)

    if not resort.is_complete():
        missing = resort.missing_fields()
        print(f"  ALERTA: No s'han pogut extreure: {', '.join(missing)}")
        print(f"  Pot ser que la web hagi canviat el seu format HTML.")

    save_resort(resort, date, file_path)
    print(f"  Dades guardades correctament.")


if __name__ == "__main__":

    today     = datetime.now().date()
    file_path = get_csv_path()

    print(f"Inici del scraping — {today}")
    print(f"Fitxer de sortida: {file_path}")

    for resort in STATIONS:
        print(f"\nProcessant: {resort.name}...")
        try:
            process_resort(resort, today, file_path)
        except requests.RequestException as e:
            print(f"  ERROR de xarxa per a {resort.name}: {e}")
        except Exception as e:
            print(f"  ERROR inesperat per a {resort.name}: {e}")

    print(f"\nFinalitzat. {len(STATIONS)} estacions processades.")