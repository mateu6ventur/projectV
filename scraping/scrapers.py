import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Optional


# =========================
# DATACLASS
# =========================

@dataclass
class SkiResort:
    name:       str
    url:        str
    latitude:   float
    longitude:  float

    # Dades d'estat de l'estació (s'omplen després del scraping)
    km_open:      Optional[float] = field(default=None)
    km_total:     Optional[float] = field(default=None)
    slopes_open:  Optional[int]   = field(default=None)
    slopes_total: Optional[int]   = field(default=None)
    lifts_open:   Optional[int]   = field(default=None)
    lifts_total:  Optional[int]   = field(default=None)
    temp_min:     Optional[float] = field(default=None)
    temp_max:     Optional[float] = field(default=None)
    precip_mm:    Optional[float] = field(default=None)

    def is_complete(self) -> bool:
        """Retorna True si totes les dades s'han extret correctament."""
        return all(v is not None for v in [
            self.km_open, self.km_total,
            self.slopes_open, self.slopes_total,
            self.lifts_open, self.lifts_total,
            self.temp_min, self.temp_max, self.precip_mm,
        ])

    def missing_fields(self) -> list[str]:
        """Retorna la llista de camps que no s'han pogut extreure."""
        fields = {
            "km_open":      self.km_open,
            "km_total":     self.km_total,
            "slopes_open":  self.slopes_open,
            "slopes_total": self.slopes_total,
            "lifts_open":   self.lifts_open,
            "lifts_total":  self.lifts_total,
            "temp_min":     self.temp_min,
            "temp_max":     self.temp_max,
            "precip_mm":    self.precip_mm,
        }
        return [name for name, val in fields.items() if val is None]

    def to_csv_row(self, date) -> list:
        """Retorna una fila per al CSV."""
        return [
            date,
            self.name,
            self.km_open,
            self.km_total,
            self.slopes_open,
            self.slopes_total,
            self.lifts_open,
            self.lifts_total,
            self.temp_min,
            self.temp_max,
            self.precip_mm,
        ]


# =========================
# CONFIGURACIÓ D'ESTACIONS
# =========================

STATIONS = [
    SkiResort(
        name="baqueira_beret",
        url="https://www.esquiades.com/en/skiresort/baqueira-beret/ski-track-conditions/",
        latitude=42.7,
        longitude=0.9,
    ),
    SkiResort(
        name="la_molina",
        url="https://www.esquiades.com/en/skiresort/la-molina/ski-track-conditions/",
        latitude=42.34,
        longitude=1.94,
    ),
    SkiResort(
        name="grandvalira",
        url="https://www.esquiades.com/en/skiresort/grandvalira/ski-track-conditions/",
        latitude=42.54,
        longitude=1.73,
    ),
    SkiResort(
        name="boi-taull",
        url="https://www.esquiades.com/en/skiresort/boi-taull/ski-track-conditions/",
        latitude=42.48,
        longitude=0.87,
    ),
    SkiResort(
        name="port-aine",
        url="https://www.esquiades.com/en/skiresort/port-aine/ski-track-conditions/",
        latitude=42.43,
        longitude=1.21,
    ),
    SkiResort(
        name="espot-esqui",
        url="https://www.esquiades.com/en/skiresort/espot-esqui/ski-track-conditions/",
        latitude=42.56,
        longitude=1.09,
    ),
    SkiResort(
        name="la-masella",
        url="https://www.esquiades.com/en/skiresort/la-masella/ski-track-conditions/",
        latitude=42.35,
        longitude=1.90,
    ),
    SkiResort(
        name="vall-de-nuria",
        url="https://www.esquiades.com/en/skiresort/vall-de-nuria/ski-track-conditions/",
        latitude=42.40,
        longitude=2.15,
    ),
    SkiResort(
        name="port-del-comte",
        url="https://www.esquiades.com/en/skiresort/port-del-comte/ski-track-conditions/",
        latitude=42.17,
        longitude=1.56,
    ),
    SkiResort(
        name="vallter-2000",
        url="https://www.esquiades.com/en/skiresort/vallter-2000/ski-track-conditions/",
        latitude=42.43,
        longitude=2.27,
    ),
    SkiResort(
        name="pal-arindal",
        url="https://www.esquiades.com/en/skiresort/pal-arinsal/ski-track-conditions/",
        latitude=42.57,
        longitude=1.47,
    ),
    SkiResort(
        name="arcalis",
        url="https://www.esquiades.com/en/skiresort/arcalis/ski-track-conditions/",
        latitude=42.63,
        longitude=1.50,
    ),
]


# =========================
# SCRAPE WEATHER
# =========================

def scrape_weather(resort: SkiResort) -> None:
    """Omple els camps de temperatura i precipitació de l'estació."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={resort.latitude}"
        f"&longitude={resort.longitude}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        "&timezone=Europe/Madrid"
    )

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    resort.temp_min  = data["daily"]["temperature_2m_min"][0]
    resort.temp_max  = data["daily"]["temperature_2m_max"][0]
    resort.precip_mm = data["daily"]["precipitation_sum"][0]


# =========================
# SCRAPE SKI STATUS
# =========================

def parse_stat_block(soup: BeautifulSoup, label: str) -> tuple[Optional[int], Optional[int]]:
    """
    Troba un bloc d'estadística pel seu label de text i retorna (valor_obert, total).

    Gestiona dues estructures HTML possibles:

    Cas A — Open Slopes / Kms of slopes (spans separats):
        <span>Open Slopes</span>
        <div class="d-flex gap-1 align-items-baseline">
            <span class="text-weight-bold text-s-17">112</span>
            <span class="text-s-13">/</span>
            <span class="text-s-13">131</span>
            <span class="color-secondary-dark">(85%)</span>
        </div>

    Cas B — Lifts ("/" i total en el mateix span):
        <span>Lifts</span>
        <div class="d-flex gap-1 align-items-baseline">
            <span class="text-weight-bold text-s-17">34</span>
            <span class="text-s-13">/36</span>
            <span class="color-secondary-dark">(94%)</span>
        </div>
    """
    for span in soup.find_all("span"):
        if span.get_text(strip=True) == label:
            container = span.find_next(
                "div", class_=lambda c: c and "gap-1" in c
            )
            if container:
                spans = container.find_all("span")
                try:
                    value  = int(spans[0].get_text(strip=True))
                    second = spans[1].get_text(strip=True)

                    if second == "/":
                        # Cas A: el total és al tercer span
                        total = int(spans[2].get_text(strip=True))
                    else:
                        # Cas B: el segon span conté "/36", eliminem la barra
                        total = int(second.replace("/", "").strip())

                    return value, total
                except (ValueError, IndexError):
                    return None, None
    return None, None


def scrape_ski_status(resort: SkiResort) -> None:
    """Omple els camps d'estat de pistes i remuntadors de l'estació."""
    headers  = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(resort.url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    resort.slopes_open,  resort.slopes_total = parse_stat_block(soup, "Open Slopes")
    resort.km_open,      resort.km_total     = parse_stat_block(soup, "Kms of slopes")
    resort.lifts_open,   resort.lifts_total  = parse_stat_block(soup, "Lifts")