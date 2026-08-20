"""
Ultimate AI Hardware Deal Tracker & PC Builder
Single-file Streamlit application with mobile-first UI,
global multi-region price engine, AI compatibility assistant.
(Monetization removed – clean version)
"""

import streamlit as st
import requests
import pandas as pd
import time
import threading
import random
import os
from typing import Dict, List, Optional, Generator, Any
from dataclasses import dataclass, field
from bs4 import BeautifulSoup

# -----------------------------------------------------------------------------
# Try to import OpenAI (graceful fallback if not installed)
# -----------------------------------------------------------------------------
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# -----------------------------------------------------------------------------
# Configuration Constants
# -----------------------------------------------------------------------------
CATEGORIES = ["CPU", "GPU", "RAM", "SSD", "Motherboard", "Combo"]

REGIONS = {
    "Bulgaria": {
        "currency": "BGN",
        "symbol": "лв",
        "exchange_rate_to_usd": 0.55,
        "stores": ["Pazaruvaj", "Ardes", "Ozone", "Plasico", "Desktop.bg"],
    },
    "Europe": {
        "currency": "EUR",
        "symbol": "€",
        "exchange_rate_to_usd": 1.08,
        "stores": ["Mindfactory", "Caseking", "Amazon.de", "Alternate"],
    },
    "North America": {
        "currency": "USD",
        "symbol": "$",
        "exchange_rate_to_usd": 1.0,
        "stores": ["Amazon", "Newegg", "Best Buy", "Micro Center"],
    },
}

# Performance scores (higher = better) for each component
PERFORMANCE_SCORES = {
    "CPU": {
        "Intel Core i3-13100F": 12000,
        "Intel Core i5-13600K": 24000,
        "Intel Core i7-13700K": 31000,
        "Intel Core i9-13900K": 38000,
        "Intel Core i5-14600K": 25000,
        "Intel Core i7-14700K": 32000,
        "Intel Core i9-14900K": 39000,
        "Intel Core Ultra 5 245K": 20000,
        "Intel Core Ultra 7 265K": 28000,
        "Intel Core Ultra 9 285K": 35000,
        "AMD Ryzen 5 5600X": 21000,
        "AMD Ryzen 7 5800X3D": 28000,
        "AMD Ryzen 7 5700G": 18000,
        "AMD Ryzen 5 7600": 22000,
        "AMD Ryzen 7 7800X3D": 32000,
        "AMD Ryzen 9 7950X": 36000,
        "AMD Ryzen 9 7950X3D": 40000,
        "AMD Ryzen 5 8600G": 20000,
        "AMD Ryzen 7 9700X": 30000,
        "AMD Ryzen 9 9900X": 34000,
        "AMD Ryzen 9 9950X": 38000,
    },
    "GPU": {
        "NVIDIA RTX 3060": 17000,
        "NVIDIA RTX 3070": 23000,
        "NVIDIA RTX 3080": 29000,
        "NVIDIA RTX 4070": 32000,
        "NVIDIA RTX 4080": 40000,
        "NVIDIA RTX 4090": 50000,
        "NVIDIA RTX 5070": 35000,
        "NVIDIA RTX 5080": 44000,
        "NVIDIA RTX 5090": 55000,
        "AMD Radeon RX 6600": 15000,
        "AMD Radeon RX 6700 XT": 21000,
        "AMD Radeon RX 6800 XT": 27000,
        "AMD Radeon RX 7900 XTX": 42000,
        "AMD Radeon RX 8800 XT": 45000,
        "Intel Arc A770": 18000,
        "Intel Arc B580": 20000,
    },
    "RAM": {
        "16GB DDR4 3200 CL16": 8000,
        "32GB DDR4 3600 CL18": 12000,
        "16GB DDR5 5200 CL40": 10000,
        "32GB DDR5 6000 CL30": 16000,
        "64GB DDR5 6400 CL32": 22000,
        "32GB DDR5 8000 CL38": 20000,
        "64GB DDR4 4400 CL19": 18000,
        "128GB DDR5 8400 CL40": 30000,
    },
    "SSD": {
        "500GB NVMe Gen3": 6000,
        "1TB NVMe Gen3": 8000,
        "1TB NVMe Gen4": 11000,
        "2TB NVMe Gen4": 14000,
        "1TB NVMe Gen5": 13000,
        "2TB NVMe Gen5": 17000,
        "4TB NVMe Gen5": 21000,
    },
    "Motherboard": {
        "B550": 5000,
        "B650": 7000,
        "X670": 9000,
        "Z790": 10000,
        "Z890": 11000,
        "B850": 8000,
        "X870": 10000,
    },
    "Combo": {
        "AMD Ryzen 5 5600X + B550 + 16GB DDR4": 20000,
        "Intel i5-13600K + Z790 + 32GB DDR5": 25000,
        "AMD Ryzen 7 7800X3D + B650 + 32GB DDR5": 30000,
        "Intel Core Ultra 7 265K + Z890 + 32GB DDR5": 28000,
    },
}

# Mock base prices in USD for each component (used as fallback)
BASE_PRICES_USD = {
    "CPU": {
        "Intel Core i3-13100F": 120,
        "Intel Core i5-13600K": 280,
        "Intel Core i7-13700K": 380,
        "Intel Core i9-13900K": 550,
        "Intel Core i5-14600K": 300,
        "Intel Core i7-14700K": 400,
        "Intel Core i9-14900K": 580,
        "Intel Core Ultra 5 245K": 250,
        "Intel Core Ultra 7 265K": 350,
        "Intel Core Ultra 9 285K": 450,
        "AMD Ryzen 5 5600X": 150,
        "AMD Ryzen 7 5800X3D": 320,
        "AMD Ryzen 7 5700G": 180,
        "AMD Ryzen 5 7600": 200,
        "AMD Ryzen 7 7800X3D": 400,
        "AMD Ryzen 9 7950X": 550,
        "AMD Ryzen 9 7950X3D": 650,
        "AMD Ryzen 5 8600G": 220,
        "AMD Ryzen 7 9700X": 330,
        "AMD Ryzen 9 9900X": 450,
        "AMD Ryzen 9 9950X": 600,
    },
    "GPU": {
        "NVIDIA RTX 3060": 300,
        "NVIDIA RTX 3070": 500,
        "NVIDIA RTX 3080": 700,
        "NVIDIA RTX 4070": 600,
        "NVIDIA RTX 4080": 1100,
        "NVIDIA RTX 4090": 1600,
        "NVIDIA RTX 5070": 550,
        "NVIDIA RTX 5080": 1000,
        "NVIDIA RTX 5090": 2000,
        "AMD Radeon RX 6600": 250,
        "AMD Radeon RX 6700 XT": 400,
        "AMD Radeon RX 6800 XT": 600,
        "AMD Radeon RX 7900 XTX": 1000,
        "AMD Radeon RX 8800 XT": 900,
        "Intel Arc A770": 350,
        "Intel Arc B580": 280,
    },
    "RAM": {
        "16GB DDR4 3200 CL16": 60,
        "32GB DDR4 3600 CL18": 110,
        "16GB DDR5 5200 CL40": 90,
        "32GB DDR5 6000 CL30": 160,
        "64GB DDR5 6400 CL32": 300,
        "32GB DDR5 8000 CL38": 250,
        "64GB DDR4 4400 CL19": 220,
        "128GB DDR5 8400 CL40": 600,
    },
    "SSD": {
        "500GB NVMe Gen3": 40,
        "1TB NVMe Gen3": 70,
        "1TB NVMe Gen4": 100,
        "2TB NVMe Gen4": 180,
        "1TB NVMe Gen5": 150,
        "2TB NVMe Gen5": 250,
        "4TB NVMe Gen5": 450,
    },
    "Motherboard": {
        "B550": 120,
        "B650": 180,
        "X670": 280,
        "Z790": 250,
        "Z890": 300,
        "B850": 200,
        "X870": 300,
    },
    "Combo": {
        "AMD Ryzen 5 5600X + B550 + 16GB DDR4": 350,
        "Intel i5-13600K + Z790 + 32GB DDR5": 550,
        "AMD Ryzen 7 7800X3D + B650 + 32GB DDR5": 700,
        "Intel Core Ultra 7 265K + Z890 + 32GB DDR5": 650,
    },
}

# Specs for compatibility checks
SPECS = {
    "CPU": {
        "Intel Core i3-13100F": {"socket": "LGA1700", "ram": "DDR4/DDR5", "cores": 4},
        "Intel Core i5-13600K": {"socket": "LGA1700", "ram": "DDR4/DDR5", "cores": 14},
        "Intel Core i7-13700K": {"socket": "LGA1700", "ram": "DDR4/DDR5", "cores": 16},
        "Intel Core i9-13900K": {"socket": "LGA1700", "ram": "DDR4/DDR5", "cores": 24},
        "Intel Core i5-14600K": {"socket": "LGA1700", "ram": "DDR4/DDR5", "cores": 14},
        "Intel Core i7-14700K": {"socket": "LGA1700", "ram": "DDR4/DDR5", "cores": 20},
        "Intel Core i9-14900K": {"socket": "LGA1700", "ram": "DDR4/DDR5", "cores": 24},
        "Intel Core Ultra 5 245K": {"socket": "LGA1851", "ram": "DDR5", "cores": 14},
        "Intel Core Ultra 7 265K": {"socket": "LGA1851", "ram": "DDR5", "cores": 20},
        "Intel Core Ultra 9 285K": {"socket": "LGA1851", "ram": "DDR5", "cores": 24},
        "AMD Ryzen 5 5600X": {"socket": "AM4", "ram": "DDR4", "cores": 6},
        "AMD Ryzen 7 5800X3D": {"socket": "AM4", "ram": "DDR4", "cores": 8},
        "AMD Ryzen 7 5700G": {"socket": "AM4", "ram": "DDR4", "cores": 8, "apu": True},
        "AMD Ryzen 5 7600": {"socket": "AM5", "ram": "DDR5", "cores": 6},
        "AMD Ryzen 7 7800X3D": {"socket": "AM5", "ram": "DDR5", "cores": 8},
        "AMD Ryzen 9 7950X": {"socket": "AM5", "ram": "DDR5", "cores": 16},
        "AMD Ryzen 9 7950X3D": {"socket": "AM5", "ram": "DDR5", "cores": 16},
        "AMD Ryzen 5 8600G": {"socket": "AM5", "ram": "DDR5", "cores": 6, "apu": True},
        "AMD Ryzen 7 9700X": {"socket": "AM5", "ram": "DDR5", "cores": 8},
        "AMD Ryzen 9 9900X": {"socket": "AM5", "ram": "DDR5", "cores": 12},
        "AMD Ryzen 9 9950X": {"socket": "AM5", "ram": "DDR5", "cores": 16},
    },
    "RAM": {
        "16GB DDR4 3200 CL16": {"type": "DDR4", "capacity": "16GB", "speed": "3200", "cl": "16"},
        "32GB DDR4 3600 CL18": {"type": "DDR4", "capacity": "32GB", "speed": "3600", "cl": "18"},
        "16GB DDR5 5200 CL40": {"type": "DDR5", "capacity": "16GB", "speed": "5200", "cl": "40"},
        "32GB DDR5 6000 CL30": {"type": "DDR5", "capacity": "32GB", "speed": "6000", "cl": "30"},
        "64GB DDR5 6400 CL32": {"type": "DDR5", "capacity": "64GB", "speed": "6400", "cl": "32"},
        "32GB DDR5 8000 CL38": {"type": "DDR5", "capacity": "32GB", "speed": "8000", "cl": "38"},
        "64GB DDR4 4400 CL19": {"type": "DDR4", "capacity": "64GB", "speed": "4400", "cl": "19"},
        "128GB DDR5 8400 CL40": {"type": "DDR5", "capacity": "128GB", "speed": "8400", "cl": "40"},
    },
    "SSD": {
        "500GB NVMe Gen3": {"type": "PCIe 3.0", "read": 3500, "write": 3000},
        "1TB NVMe Gen3": {"type": "PCIe 3.0", "read": 3500, "write": 3000},
        "1TB NVMe Gen4": {"type": "PCIe 4.0", "read": 7000, "write": 5000},
        "2TB NVMe Gen4": {"type": "PCIe 4.0", "read": 7000, "write": 5000},
        "1TB NVMe Gen5": {"type": "PCIe 5.0", "read": 12000, "write": 10000},
        "2TB NVMe Gen5": {"type": "PCIe 5.0", "read": 12000, "write": 10000},
        "4TB NVMe Gen5": {"type": "PCIe 5.0", "read": 14000, "write": 12000},
    },
    "Motherboard": {
        "B550": {"socket": "AM4", "ram": "DDR4", "pcie": "3.0/4.0"},
        "B650": {"socket": "AM5", "ram": "DDR5", "pcie": "4.0/5.0"},
        "X670": {"socket": "AM5", "ram": "DDR5", "pcie": "4.0/5.0"},
        "Z790": {"socket": "LGA1700", "ram": "DDR4/DDR5", "pcie": "4.0/5.0"},
        "Z890": {"socket": "LGA1851", "ram": "DDR5", "pcie": "5.0"},
        "B850": {"socket": "AM5", "ram": "DDR5", "pcie": "4.0/5.0"},
        "X870": {"socket": "AM5", "ram": "DDR5", "pcie": "5.0"},
    },
    "Combo": {
        "AMD Ryzen 5 5600X + B550 + 16GB DDR4": {"socket": "AM4", "ram": "DDR4"},
        "Intel i5-13600K + Z790 + 32GB DDR5": {"socket": "LGA1700", "ram": "DDR5"},
        "AMD Ryzen 7 7800X3D + B650 + 32GB DDR5": {"socket": "AM5", "ram": "DDR5"},
        "Intel Core Ultra 7 265K + Z890 + 32GB DDR5": {"socket": "LGA1851", "ram": "DDR5"},
    },
}


# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------
@dataclass
class Deal:
    name: str
    category: str
    price: float
    region: str
    store: str
    url: str
    performance_score: float
    currency: str
    specs: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "region": self.region,
            "store": self.store,
            "url": self.url,
            "performance_score": self.performance_score,
            "currency": self.currency,
            "specs": self.specs,
        }


# -----------------------------------------------------------------------------
# Currency Helper
# -----------------------------------------------------------------------------
def convert_usd_to_local(usd_price: float, region: str) -> float:
    rate = REGIONS[region]["exchange_rate_to_usd"]
    return round(usd_price / rate, 2)


def format_price(price: float, region: str) -> str:
    symbol = REGIONS[region]["symbol"]
    return f"{symbol}{price:,.2f}"


# -----------------------------------------------------------------------------
# Value Score Calculation
# -----------------------------------------------------------------------------
def compute_value_score(performance_score: float, price: float) -> float:
    if price <= 0:
        return 0.0
    return round((performance_score / price) * 100, 2)


# -----------------------------------------------------------------------------
# Scraper Functions (attempt live, fallback to mock)
# -----------------------------------------------------------------------------
def scrape_store_live(store: str, region: str, category: str) -> List[Deal]:
    """
    Attempt to scrape real deals from a store using requests + BeautifulSoup.
    Falls back to an empty list on any failure.
    """
    base_urls = {
        "Pazaruvaj": "https://www.pazaruvaj.com",
        "Ardes": "https://ardes.bg",
        "Ozone": "https://ozone.bg",
        "Mindfactory": "https://www.mindfactory.de",
        "Caseking": "https://www.caseking.de",
        "Amazon.de": "https://www.amazon.de",
        "Alternate": "https://www.alternate.de",
        "Amazon": "https://www.amazon.com",
        "Newegg": "https://www.newegg.com",
        "Best Buy": "https://www.bestbuy.com",
        "Micro Center": "https://www.microcenter.com",
        "Plasico": "https://plasico.bg",
        "Desktop.bg": "https://desktop.bg",
    }
    base = base_urls.get(store, "")
    if not base:
        return []
    search_url = f"{base}/search?q={category.replace(' ', '+')}"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(search_url, headers=headers, timeout=3)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        # Very generic extraction: find all anchor tags with price-like text
        # This will rarely work reliably; hence we always fall back to mock data.
        products = []
        for item in soup.select("a"):
            text = item.get_text(strip=True)
            if text and any(ch.isdigit() for ch in text):
                products.append(text)
        if not products:
            return []
        # If products found, we would map them to Deals here.
        # For now, returning empty to force fallback to mock data.
        return []
    except Exception:
        return []


def generate_mock_deals(region: str) -> List[Deal]:
    """Generate complete mock dataset for a region."""
    deals = []
    stores = REGIONS[region]["stores"]
    currency = REGIONS[region]["currency"]
    for category in CATEGORIES:
        for name, usd_price in BASE_PRICES_USD[category].items():
            # Convert to local price with random variation
            local_price = convert_usd_to_local(usd_price, region) * random.uniform(0.85, 1.15)
            local_price = round(local_price, 2)
            store = random.choice(stores)
            # Clean URL (no affiliate tags)
            url = f"https://{store.lower().replace(' ', '')}.example.com/product/{name.replace(' ', '-')}"
            performance = PERFORMANCE_SCORES.get(category, {}).get(name, 0)
            specs = SPECS.get(category, {}).get(name, {})
            deals.append(Deal(
                name=name,
                category=category,
                price=local_price,
                region=region,
                store=store,
                url=url,
                performance_score=performance,
                currency=currency,
                specs=specs,
            ))
    return deals


def fetch_deals_region(region: str) -> List[Deal]:
    """Fetch deals for a region, combining live and mock."""
    live_deals = []
    # Try live scraping for each store and category (very limited)
    for store in REGIONS[region]["stores"]:
        for category in CATEGORIES:
            live_deals.extend(scrape_store_live(store, region, category))
    # If live scraping failed, use mock dataset
    if not live_deals:
        return generate_mock_deals(region)
    return live_deals


# -----------------------------------------------------------------------------
# Background Fetcher (Thread)
# -----------------------------------------------------------------------------
class BackgroundFetcher:
    """Background thread that periodically refreshes deals for all regions."""

    def __init__(self, interval_minutes: int = 10):
        self.interval = interval_minutes * 60
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._deals: Dict[str, List[Deal]] = {}
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def _run(self):
        while not self._stop_event.is_set():
            for region in REGIONS.keys():
                try:
                    deals = fetch_deals_region(region)
                    with self._lock:
                        self._deals[region] = deals
                except Exception as e:
                    print(f"Error fetching {region}: {e}")
            time.sleep(self.interval)

    def get_deals(self, region: str) -> List[Deal]:
        with self._lock:
            return list(self._deals.get(region, []))

    def stop(self):
        self._stop_event.set()


# -----------------------------------------------------------------------------
# AI Assistant Functions
# -----------------------------------------------------------------------------
def build_system_prompt(region: str, budget: float, resolution: str,
                        selected_parts: Dict[str, Dict]) -> str:
    currency = REGIONS[region]["currency"]
    parts_summary = "\n".join(
        f"{cat}: {part.get('name', 'None')}" for cat, part in selected_parts.items() if part
    )
    return f"""You are an expert PC hardware assistant.
Current user context:
- Region: {region} (currency: {currency})
- Budget: {budget} {currency}
- Target resolution: {resolution}

Current build:
{parts_summary if parts_summary else "No components selected."}

Provide advice on compatibility, value, and performance. Use the Speed-to-Price Value Score when relevant."""


def stream_ai_response(prompt: str, context: Dict) -> Generator[str, None, None]:
    """
    Stream AI response using OpenAI if API key is set,
    otherwise fall back to a local rule-based response.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and OPENAI_AVAILABLE:
        client = OpenAI(api_key=api_key)
        system_prompt = build_system_prompt(
            context.get("region", "North America"),
            context.get("budget", 1500),
            context.get("resolution", "1440p"),
            context.get("selected_parts", {}),
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    else:
        yield from local_ai_response(prompt, context)


def local_ai_response(prompt: str, context: Dict) -> Generator[str, None, None]:
    """Fallback local response when OpenAI is unavailable."""
    selected = context.get("selected_parts", {})
    parts_list = [f"{cat}: {part.get('name', 'Unknown')}" for cat, part in selected.items() if part]
    if not parts_list:
        parts_list = ["No components selected yet."]
    response = (
        "I'm running in offline mode (no OpenAI API key set).\n"
        "Here's what I know about your build:\n" +
        "\n".join(parts_list) +
        "\n\nUse the Speed-to-Price Value Score to compare components. "
        "Check compatibility before purchasing."
    )
    for i in range(0, len(response), 20):
        yield response[i:i+20]


# -----------------------------------------------------------------------------
# Compatibility Check
# -----------------------------------------------------------------------------
def check_compatibility(parts: Dict[str, Optional[Dict]]) -> List[str]:
    """
    parts: dict with keys 'CPU', 'Motherboard', 'RAM', 'GPU', 'SSD'
    Each value is a Deal.to_dict() (or None).
    Returns list of issues.
    """
    issues = []
    cpu = parts.get("CPU")
    mobo = parts.get("Motherboard")
    ram = parts.get("RAM")
    gpu = parts.get("GPU")
    ssd = parts.get("SSD")

    if cpu and mobo:
        cpu_socket = cpu.get("specs", {}).get("socket", "")
        mobo_socket = mobo.get("specs", {}).get("socket", "")
        if cpu_socket and mobo_socket and cpu_socket != mobo_socket:
            issues.append(f"CPU socket ({cpu_socket}) does not match motherboard socket ({mobo_socket}).")

        cpu_ram = cpu.get("specs", {}).get("ram", "")
        mobo_ram = mobo.get("specs", {}).get("ram", "")
        if ram:
            ram_type = ram.get("specs", {}).get("type", "")
            if ram_type:
                if mobo_ram and ram_type not in mobo_ram:
                    issues.append(f"RAM type {ram_type} not supported by motherboard (supports {mobo_ram}).")
                if cpu_ram and ram_type not in cpu_ram:
                    issues.append(f"RAM type {ram_type} not supported by CPU (supports {cpu_ram}).")

    if ssd and mobo:
        ssd_interface = ssd.get("specs", {}).get("type", "")
        mobo_pcie = mobo.get("specs", {}).get("pcie", "")
        if "5.0" in ssd_interface and mobo_pcie and "5.0" not in mobo_pcie:
            issues.append(f"SSD uses PCIe 5.0 but motherboard only supports {mobo_pcie}.")

    if cpu and gpu:
        cpu_name = cpu.get("name", "")
        gpu_name = gpu.get("name", "")
        tdp = estimate_tdp(cpu_name, gpu_name)
        issues.append(f"Estimated system TDP: {tdp}W. Recommend PSU ≥ {tdp + 100}W.")

    if cpu and gpu:
        cpu_score = cpu.get("performance_score", 0)
        gpu_score = gpu.get("performance_score", 0)
        bottleneck = bottleneck_percentage(cpu_score, gpu_score, "1440p")
        if bottleneck > 15:
            issues.append(f"Potential CPU/GPU bottleneck at 1440p: ~{bottleneck}% GPU performance loss.")

    return issues


def estimate_tdp(cpu_name: str, gpu_name: str) -> int:
    """Rough TDP estimation."""
    cpu_power = 0
    gpu_power = 0
    if cpu_name:
        if any(x in cpu_name for x in ["i9", "Ryzen 9", "Ultra 9"]):
            cpu_power = 150
        elif any(x in cpu_name for x in ["i7", "Ryzen 7", "Ultra 7"]):
            cpu_power = 120
        elif any(x in cpu_name for x in ["i5", "Ryzen 5", "Ultra 5"]):
            cpu_power = 90
        else:
            cpu_power = 65
    if gpu_name:
        if "5090" in gpu_name:
            gpu_power = 500
        elif "4090" in gpu_name or "5080" in gpu_name or "7900 XTX" in gpu_name:
            gpu_power = 450
        elif "4080" in gpu_name or "8800 XT" in gpu_name:
            gpu_power = 350
        elif "3080" in gpu_name or "6800 XT" in gpu_name or "5070" in gpu_name:
            gpu_power = 300
        elif "3070" in gpu_name or "6700 XT" in gpu_name or "B580" in gpu_name:
            gpu_power = 220
        else:
            gpu_power = 150
    base = 50
    return base + cpu_power + gpu_power


def bottleneck_percentage(cpu_score: float, gpu_score: float, resolution: str) -> float:
    """Estimate CPU/GPU bottleneck percentage."""
    if cpu_score <= 0 or gpu_score <= 0:
        return 0.0
    res_factor = {"1080p": 0.7, "1440p": 0.85, "4K": 1.0}.get(resolution, 0.85)
    ratio = cpu_score / gpu_score
    if ratio < 0.5:
        return round(40 * res_factor, 1)
    elif ratio < 0.8:
        return round(25 * res_factor, 1)
    elif ratio < 1.2:
        return round(10 * res_factor, 1)
    return 0.0


# -----------------------------------------------------------------------------
# Streamlit App
# -----------------------------------------------------------------------------
def main():
    # Page config
    st.set_page_config(
        page_title="AI Hardware Deal Tracker & PC Builder",
        page_icon="🖥️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #FFFFFF;
        }
        .deal-card {
            background-color: #1E1E1E;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            border: 1px solid #333;
        }
        .deal-card:hover {
            border-color: #00ADB5;
        }
        .value-score {
            font-size: 1.2rem;
            font-weight: bold;
            color: #00ADB5;
        }
        .buy-button {
            background-color: #00ADB5;
            color: #000;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            text-decoration: none;
            display: inline-block;
            margin-top: 0.5rem;
        }
        /* Mobile responsiveness: stack columns */
        @media (max-width: 768px) {
            .stColumns {
                flex-direction: column;
            }
            .stButton>button {
                width: 100%;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize background fetcher (cached resource)
    @st.cache_resource(show_spinner=False)
    def get_fetcher() -> BackgroundFetcher:
        fetcher = BackgroundFetcher(interval_minutes=10)
        fetcher.start()
        return fetcher

    fetcher = get_fetcher()

    # Initialize session state
    if "build" not in st.session_state:
        st.session_state.build = {}
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Sidebar
    with st.sidebar:
        st.title("⚙️ Settings")

        region = st.selectbox("🌍 Region", list(REGIONS.keys()), index=0)
        budget = st.slider(f"💰 Budget ({REGIONS[region]['symbol']})",
                           min_value=100, max_value=5000, value=1500, step=50)
        resolution = st.selectbox("🎮 Target Resolution", ["1080p", "1440p", "4K"], index=1)
        category_filter = st.radio("📦 Category", ["All"] + CATEGORIES, index=0)

    # Main area
    st.title("🖥️ AI Hardware Deal Tracker & PC Builder")

    # Fetch deals for selected region
    deals = fetcher.get_deals(region)
    if not deals:
        # Fallback to immediate fetch if background thread hasn't populated yet
        deals = fetch_deals_region(region)

    # Filter by budget and category
    filtered = [d for d in deals if d.price <= budget]
    if category_filter != "All":
        filtered = [d for d in filtered if d.category == category_filter]

    # Sort by value score descending
    filtered.sort(key=lambda x: compute_value_score(x.performance_score, x.price), reverse=True)

    # Display deals in a responsive grid
    if filtered:
        st.subheader(f"🔥 Top Deals in {region} (max {format_price(budget, region)})")
        cols = st.columns(3)
        for idx, deal in enumerate(filtered[:15]):  # Limit to 15 to avoid overload
            with cols[idx % 3]:
                with st.container():
                    st.markdown('<div class="deal-card">', unsafe_allow_html=True)
                    st.markdown(f"**{deal.name}**")
                    st.markdown(f"Store: {deal.store}")
                    st.markdown(f"Price: **{format_price(deal.price, deal.region)}**")
                    value = compute_value_score(deal.performance_score, deal.price)
                    st.markdown(f'<span class="value-score">Value Score: {value:.1f}</span>',
                                unsafe_allow_html=True)
                    # Buy button (no affiliate)
                    st.markdown(f'<a href="{deal.url}" target="_blank" class="buy-button">'
                                'Buy Now →</a>', unsafe_allow_html=True)
                    # Add to build button
                    if deal.category != "Combo":
                        if st.button("Add to Build", key=f"add_{region}_{deal.name}_{deal.store}"):
                            st.session_state.build[deal.category] = deal.to_dict()
                            st.success(f"Added {deal.name} to build!")
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No deals found matching your filters.")

    # Build summary & compatibility
    st.markdown("---")
    st.subheader("🛠️ Your Build")
    build = st.session_state.build
    if build:
        for cat, part in build.items():
            st.markdown(f"**{cat}:** {part['name']} – {format_price(part['price'], part['region'])}")
        if st.button("✅ Check Compatibility"):
            issues = check_compatibility(build)
            if issues:
                st.error("Compatibility Issues Found:")
                for issue in issues:
                    st.markdown(f"• {issue}")
            else:
                st.success("All components are compatible! 🎉")
        if st.button("🗑️ Clear Build"):
            st.session_state.build = {}
            st.rerun()
    else:
        st.info("No components selected. Browse deals above and click 'Add to Build'.")

    # AI Assistant
    st.markdown("---")
    st.subheader("🤖 AI Hardware Assistant")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about hardware compatibility, value, or recommendations..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        context = {
            "region": region,
            "budget": budget,
            "resolution": resolution,
            "selected_parts": build,
        }

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            try:
                for chunk in stream_ai_response(prompt, context):
                    full_response += chunk
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            except Exception as e:
                response_placeholder.error(f"AI error: {e}")
                full_response = f"Error: {e}"
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    st.markdown("---")
    st.caption("© 2026 Hardware Deals Tracker | Built with Streamlit")


if __name__ == "__main__":
    main()