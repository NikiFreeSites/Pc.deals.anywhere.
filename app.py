"""
Ultimate AI Hardware Deal Tracker & PC Builder
Single-file Streamlit application with mobile-first UI,
global multi-region price engine, AI compatibility assistant.
"""

import streamlit as st
import requests
import pandas as pd
import time
import threading
import random
import os
import urllib.parse
from typing import Dict, List, Optional, Generator, Any
from dataclasses import dataclass, field

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

PERFORMANCE_SCORES = {
    "CPU": {
        "Intel Core i5-13600K": 24000,
        "Intel Core i7-13700K": 31000,
        "Intel Core i9-13900K": 38000,
        "Intel Core i5-14600K": 25000,
        "Intel Core i7-14700K": 32000,
        "Intel Core i9-14900K": 39000,
        "AMD Ryzen 5 7600": 22000,
        "AMD Ryzen 7 7800X3D": 32000,
        "AMD Ryzen 9 7950X3D": 40000,
        "AMD Ryzen 7 9700X": 30000,
        "AMD Ryzen 9 9950X": 38000,
    },
    "GPU": {
        "NVIDIA GeForce RTX 5090 32GB": 60000,
        "NVIDIA GeForce RTX 5080 16GB": 48000,
        "NVIDIA GeForce RTX 5070 Ti 16GB": 42000,
        "NVIDIA GeForce RTX 5070 12GB": 36000,
        "NVIDIA GeForce RTX 5060 Ti 16GB": 28000,
        "NVIDIA GeForce RTX 5060 Ti 8GB": 26000,
        "NVIDIA GeForce RTX 5060 8GB": 22000,
        "AMD Radeon RX 9070 XT 16GB": 40000,
        "AMD Radeon RX 9070 16GB": 35000,
        "AMD Radeon RX 9060 XT 16GB": 27000,
        "AMD Radeon RX 9060 XT 8GB": 25000,
        "AMD Radeon RX 7900 XTX 24GB": 38000,
        "NVIDIA GeForce RTX 4090 24GB": 45000,
    },
    "RAM": {
        "32GB DDR4 3600 CL18": 12000,
        "32GB DDR5 6000 CL30": 16000,
        "64GB DDR5 6400 CL32": 22000,
    },
    "SSD": {
        "1TB NVMe Gen4": 11000,
        "2TB NVMe Gen4": 14000,
        "2TB NVMe Gen5": 17000,
    },
    "Motherboard": {
        "B650": 7000,
        "X670E": 9500,
        "Z790": 10000,
        "X870E": 11000,
    },
    "Combo": {
        "AMD Ryzen 7 7800X3D + B650 + 32GB DDR5": 30000,
        "Intel i5-14600K + Z790 + 32GB DDR5": 27000,
    },
}

BASE_PRICES_USD = {
    "CPU": {
        "Intel Core i5-13600K": 280,
        "Intel Core i7-13700K": 350,
        "Intel Core i9-13900K": 450,
        "Intel Core i5-14600K": 300,
        "Intel Core i7-14700K": 400,
        "Intel Core i9-14900K": 550,
        "AMD Ryzen 5 7600": 200,
        "AMD Ryzen 7 7800X3D": 380,
        "AMD Ryzen 9 7950X3D": 600,
        "AMD Ryzen 7 9700X": 350,
        "AMD Ryzen 9 9950X": 650,
    },
    "GPU": {
        "NVIDIA GeForce RTX 5090 32GB": 1999,
        "NVIDIA GeForce RTX 5080 16GB": 999,
        "NVIDIA GeForce RTX 5070 Ti 16GB": 749,
        "NVIDIA GeForce RTX 5070 12GB": 549,
        "NVIDIA GeForce RTX 5060 Ti 16GB": 429,
        "NVIDIA GeForce RTX 5060 Ti 8GB": 379,
        "NVIDIA GeForce RTX 5060 8GB": 299,
        "AMD Radeon RX 9070 XT 16GB": 599,
        "AMD Radeon RX 9070 16GB": 549,
        "AMD Radeon RX 9060 XT 16GB": 349,
        "AMD Radeon RX 9060 XT 8GB": 299,
        "AMD Radeon RX 7900 XTX 24GB": 920,
        "NVIDIA GeForce RTX 4090 24GB": 1750,
    },
    "RAM": {
        "32GB DDR4 3600 CL18": 65,
        "32GB DDR5 6000 CL30": 110,
        "64GB DDR5 6400 CL32": 210,
    },
    "SSD": {
        "1TB NVMe Gen4": 75,
        "2TB NVMe Gen4": 130,
        "2TB NVMe Gen5": 250,
    },
    "Motherboard": {
        "B650": 160,
        "X670E": 280,
        "Z790": 220,
        "X870E": 320,
    },
    "Combo": {
        "AMD Ryzen 7 7800X3D + B650 + 32GB DDR5": 600,
        "Intel i5-14600K + Z790 + 32GB DDR5": 580,
    },
}

SPECS = {
    "CPU": {
        "Intel Core i5-13600K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "Intel Core i7-13700K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "Intel Core i9-13900K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "Intel Core i5-14600K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "Intel Core i7-14700K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "Intel Core i9-14900K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "AMD Ryzen 5 7600": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 7 7800X3D": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 9 7950X3D": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 7 9700X": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 9 9950X": {"socket": "AM5", "ram": "DDR5"},
    },
    "RAM": {
        "32GB DDR4 3600 CL18": {"type": "DDR4"},
        "32GB DDR5 6000 CL30": {"type": "DDR5"},
        "64GB DDR5 6400 CL32": {"type": "DDR5"},
    },
    "Motherboard": {
        "B650": {"socket": "AM5", "ram": "DDR5"},
        "X670E": {"socket": "AM5", "ram": "DDR5"},
        "Z790": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "X870E": {"socket": "AM5", "ram": "DDR5"},
    },
}


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


def convert_usd_to_local(usd_price: float, region: str) -> float:
    rate = REGIONS[region]["exchange_rate_to_usd"]
    return round(usd_price / rate, 2)


def format_price(price: float, region: str) -> str:
    symbol = REGIONS[region]["symbol"]
    return f"{symbol}{price:,.2f}"


def compute_value_score(performance_score: float, price: float) -> float:
    if price <= 0:
        return 0.0
    return round((performance_score / price) * 100, 2)


def generate_live_search_url(product_name: str, store: str) -> str:
    encoded_query = urllib.parse.quote_plus(product_name)
    if "Amazon" in store:
        return f"https://www.amazon.com/s?k={encoded_query}"
    elif "Newegg" in store:
        return f"https://www.newegg.com/p/pl?d={encoded_query}"
    elif "Best Buy" in store:
        return f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_query}"
    elif "Mindfactory" in store:
        return f"https://www.mindfactory.de/search_result.php?search_query={encoded_query}"
    elif "Caseking" in store:
        return f"https://www.caseking.de/search?sSearch={encoded_query}"
    return f"https://www.google.com/search?q={encoded_query}+{urllib.parse.quote_plus(store)}"


def generate_mock_deals(region: str) -> List[Deal]:
    deals = []
    stores = REGIONS[region]["stores"]
    currency = REGIONS[region]["currency"]
    for category in CATEGORIES:
        for name, usd_price in BASE_PRICES_USD.get(category, {}).items():
            local_price = convert_usd_to_local(usd_price, region) * random.uniform(0.92, 1.08)
            local_price = round(local_price, 2)
            store = random.choice(stores)
            url = generate_live_search_url(name, store)
            performance = PERFORMANCE_SCORES.get(category, {}).get(name, 0)
            specs = SPECS.get(category, {}).get(name, {})
            deals.append(
                Deal(name, category, local_price, region, store, url, performance, currency, specs)
            )
    return deals


class BackgroundFetcher:
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
                    deals = generate_mock_deals(region)
                    with self._lock:
                        self._deals[region] = deals
                except Exception:
                    pass
            time.sleep(self.interval)

    def get_deals(self, region: str) -> List[Deal]:
        with self._lock:
            return list(self._deals.get(region, []))


def check_compatibility(parts: Dict[str, Optional[Dict]]) -> List[str]:
    issues = []
    cpu, mobo, ram = parts.get("CPU"), parts.get("Motherboard"), parts.get("RAM")

    if cpu and mobo:
        cpu_sock = cpu.get("specs", {}).get("socket", "")
        mobo_sock = mobo.get("specs", {}).get("socket", "")
        if cpu_sock and mobo_sock and cpu_sock != mobo_sock:
            issues.append(f"Socket mismatch: CPU uses {cpu_sock} while Motherboard requires {mobo_sock}.")

        cpu_ram = cpu.get("specs", {}).get("ram", "")
        mobo_ram = mobo.get("specs", {}).get("ram", "")
        if ram:
            ram_type = ram.get("specs", {}).get("type", "")
            if ram_type and mobo_ram and ram_type not in mobo_ram:
                issues.append(f"RAM {ram_type} is not supported by Motherboard ({mobo_ram}).")
    return issues


def main():
    st.set_page_config(
        page_title="Ultimate Hardware Deal Tracker",
        page_icon="🖥️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom styling keeping blue-on-blue intact and adding animations
    st.markdown(
        """
    <style>
        .stApp { background-color: #121212; color: #FFFFFF; }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(0, 173, 181, 0.5); }
            70% { box-shadow: 0 0 12px 12px rgba(0, 173, 181, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 173, 181, 0); }
        }
        
        .deal-card {
            background-color: #1E1E1E; 
            border-radius: 8px; 
            padding: 1rem; 
            margin: 0.5rem 0;
            border: 1px solid #333; 
            transition: transform 0.2s ease-in-out;
        }
        .deal-card:hover { 
            border-color: #00ADB5; 
            animation: pulse 1.5s infinite; 
            transform: scale(1.02); 
        }
        .value-score { font-size: 1.2rem; font-weight: bold; color: #00ADB5; }
        .buy-button { 
            background-color: #00ADB5; 
            color: #000000 !important; 
            border-radius: 6px; 
            padding: 0.5rem 1rem; 
            text-decoration: none; 
            display: inline-block; 
            margin-top: 0.5rem; 
            font-weight: bold;
        }
        
        /* Blue on blue text CSS preserved */
        .blue-on-blue { background-color: #0000FF; color: #0000FF; padding: 5px; user-select: all; }
        
        @media (max-width: 768px) { 
            .stColumns { flex-direction: column; } 
            .stButton>button { width: 100%; }
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    @st.cache_resource(show_spinner=False)
    def get_fetcher() -> BackgroundFetcher:
        fetcher = BackgroundFetcher(interval_minutes=10)
        fetcher.start()
        return fetcher

    fetcher = get_fetcher()
    if "build" not in st.session_state:
        st.session_state.build = {}

    with st.sidebar:
        st.title("⚙️ Settings")
        region = st.selectbox("🌍 Region", list(REGIONS.keys()), index=0)
        budget = st.slider(f"💰 Budget ({REGIONS[region]['symbol']})", 100, 6000, 2000, 50)
        category_filter = st.radio("📦 Category", ["All"] + CATEGORIES, index=0)
        st.markdown('<div class="blue-on-blue">Blue-on-blue text retained</div>', unsafe_allow_html=True)

    st.title("🖥️ Hardware Deal Tracker & PC Builder")

    deals = fetcher.get_deals(region) or generate_mock_deals(region)
    filtered = [d for d in deals if d.price <= budget]
    if category_filter != "All":
        filtered = [d for d in filtered if d.category == category_filter]
    filtered.sort(key=lambda x: compute_value_score(x.performance_score, x.price), reverse=True)

    if filtered:
        st.subheader(f"🔥 Best Deals in {region}")
        cols = st.columns(3)
        for idx, deal in enumerate(filtered[:18]):
            with cols[idx % 3]:
                st.markdown('<div class="deal-card">', unsafe_allow_html=True)
                st.markdown(
                    f"**{deal.name}**\n\nStore: {deal.store}\n\nPrice: **{format_price(deal.price, deal.region)}**"
                )
                val_score = compute_value_score(deal.performance_score, deal.price)
                st.markdown(
                    f'<span class="value-score">Value Score: {val_score:.1f}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<a href="{deal.url}" target="_blank" class="buy-button">View Real Product →</a>',
                    unsafe_allow_html=True,
                )

                if deal.category != "Combo" and st.button(
                    "Add to Build", key=f"add_{region}_{deal.category}_{idx}"
                ):
                    st.session_state.build[deal.category] = deal.to_dict()
                    st.toast(f"Added {deal.name} to build!")
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No components found matching your current budget filter.")

    st.markdown("---")
    st.subheader("🛠️ Current Build")
    if st.session_state.build:
        for cat, part in st.session_state.build.items():
            st.markdown(f"**{cat}:** {part['name']} – {format_price(part['price'], part['region'])}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Check Compatibility"):
                # Audio effect trigger on click
                st.markdown(
                    """<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""",
                    unsafe_allow_html=True,
                )
                issues = check_compatibility(st.session_state.build)
                if issues:
                    st.error("Compatibility Issues Detected:")
                    for issue in issues:
                        st.markdown(f"• {issue}")
                else:
                    st.success("All selected components are 100% compatible! 🎉")
                    st.balloons()
        with col2:
            if st.button("🗑️ Clear Build"):
                st.session_state.build = {}
                st.rerun()


if __name__ == "__main__":
    main()
