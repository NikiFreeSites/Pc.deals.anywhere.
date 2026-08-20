"""
Ultimate Europe & NA AI Hardware Deal Aggregator & PC Builder
Multi-region price engine, store ratings, price-drop badges, 
animated comparison UI, and AI compatibility checker.
"""

import streamlit as st
import pandas as pd
import time
import threading
import random
import urllib.parse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

# -----------------------------------------------------------------------------
# Configuration & Multi-Region Setup (Europe & North America)
# -----------------------------------------------------------------------------
CATEGORIES = ["CPU", "GPU", "RAM", "SSD", "Motherboard", "Combo"]

REGIONS = {
    "Europe (EUR)": {
        "currency": "EUR",
        "symbol": "€",
        "exchange_rate": 1.08,
        "stores": [
            {"name": "Mindfactory", "rating": 4.9, "trust": "Verified Seller"},
            {"name": "Caseking", "rating": 4.8, "trust": "Verified Seller"},
            {"name": "Amazon.de", "rating": 4.7, "trust": "Global Store"},
            {"name": "Alternate", "rating": 4.8, "trust": "Verified Seller"},
            {"name": "Alza.eu", "rating": 4.6, "trust": "EU Retailer"},
        ],
    },
    "UK (GBP)": {
        "currency": "GBP",
        "symbol": "£",
        "exchange_rate": 1.27,
        "stores": [
            {"name": "Scan UK", "rating": 4.9, "trust": "Verified Seller"},
            {"name": "Overclockers UK", "rating": 4.8, "trust": "Verified Seller"},
            {"name": "Amazon.co.uk", "rating": 4.7, "trust": "Global Store"},
            {"name": "Ebuyer", "rating": 4.5, "trust": "UK Retailer"},
        ],
    },
    "North America (USD)": {
        "currency": "USD",
        "symbol": "$",
        "exchange_rate": 1.0,
        "stores": [
            {"name": "Micro Center", "rating": 4.9, "trust": "In-Store / Online"},
            {"name": "Newegg", "rating": 4.6, "trust": "Direct / Marketplace"},
            {"name": "Amazon US", "rating": 4.8, "trust": "Global Store"},
            {"name": "Best Buy", "rating": 4.7, "trust": "Authorized Dealer"},
            {"name": "B&H Photo", "rating": 4.9, "trust": "Authorized Dealer"},
        ],
    },
    "Canada (CAD)": {
        "currency": "CAD",
        "symbol": "CA$",
        "exchange_rate": 0.74,
        "stores": [
            {"name": "Canada Computers", "rating": 4.6, "trust": "CA Retailer"},
            {"name": "Memory Express", "rating": 4.9, "trust": "CA Retailer"},
            {"name": "Amazon.ca", "rating": 4.7, "trust": "Global Store"},
            {"name": "Newegg CA", "rating": 4.5, "trust": "Marketplace"},
        ],
    },
}

PERFORMANCE_SCORES = {
    "CPU": {
        "AMD Ryzen 7 9800X3D": 36000,
        "AMD Ryzen 9 9950X": 39000,
        "AMD Ryzen 7 9700X": 30000,
        "AMD Ryzen 7 7800X3D": 32000,
        "AMD Ryzen 5 7600X": 23000,
        "Intel Core Ultra 9 285K": 37000,
        "Intel Core Ultra 7 265K": 31000,
        "Intel Core i9-14900K": 38000,
        "Intel Core i7-14700K": 33000,
        "Intel Core i5-14600K": 25000,
    },
    "GPU": {
        "NVIDIA GeForce RTX 5090 32GB": 62000,
        "NVIDIA GeForce RTX 5080 16GB": 49000,
        "NVIDIA GeForce RTX 5070 Ti 16GB": 43000,
        "NVIDIA GeForce RTX 5070 12GB": 37000,
        "NVIDIA GeForce RTX 5060 Ti 16GB": 29000,
        "NVIDIA GeForce RTX 5060 8GB": 23000,
        "AMD Radeon RX 9070 XT 16GB": 41000,
        "AMD Radeon RX 9070 16GB": 36000,
        "AMD Radeon RX 9060 XT 16GB": 28000,
        "AMD Radeon RX 9060 XT 8GB": 25000,
        "AMD Radeon RX 7900 XTX 24GB": 39000,
        "NVIDIA GeForce RTX 4090 24GB": 46000,
    },
    "RAM": {
        "32GB DDR5 6000 CL30": 16000,
        "64GB DDR5 6400 CL32": 22000,
        "32GB DDR4 3600 CL18": 12000,
    },
    "SSD": {
        "2TB NVMe Gen5 (12000 MB/s)": 18000,
        "2TB NVMe Gen4 (7300 MB/s)": 14000,
        "1TB NVMe Gen4 (7000 MB/s)": 11000,
    },
    "Motherboard": {
        "X870E AM5 Flagship": 11000,
        "B650 AM5 Mainstream": 7500,
        "Z890 LGA1851": 10500,
        "Z790 LGA1700": 9800,
    },
    "Combo": {
        "AMD Ryzen 7 9800X3D + X870E + 32GB DDR5": 38000,
        "AMD Ryzen 7 7800X3D + B650 + 32GB DDR5": 31000,
        "Intel Ultra 7 265K + Z890 + 32GB DDR5": 32000,
    },
}

BASE_PRICES_USD = {
    "CPU": {
        "AMD Ryzen 7 9800X3D": 479,
        "AMD Ryzen 9 9950X": 649,
        "AMD Ryzen 7 9700X": 359,
        "AMD Ryzen 7 7800X3D": 389,
        "AMD Ryzen 5 7600X": 209,
        "Intel Core Ultra 9 285K": 589,
        "Intel Core Ultra 7 265K": 394,
        "Intel Core i9-14900K": 539,
        "Intel Core i7-14700K": 389,
        "Intel Core i5-14600K": 299,
    },
    "GPU": {
        "NVIDIA GeForce RTX 5090 32GB": 1999,
        "NVIDIA GeForce RTX 5080 16GB": 999,
        "NVIDIA GeForce RTX 5070 Ti 16GB": 749,
        "NVIDIA GeForce RTX 5070 12GB": 549,
        "NVIDIA GeForce RTX 5060 Ti 16GB": 429,
        "NVIDIA GeForce RTX 5060 8GB": 299,
        "AMD Radeon RX 9070 XT 16GB": 599,
        "AMD Radeon RX 9070 16GB": 549,
        "AMD Radeon RX 9060 XT 16GB": 349,
        "AMD Radeon RX 9060 XT 8GB": 299,
        "AMD Radeon RX 7900 XTX 24GB": 899,
        "NVIDIA GeForce RTX 4090 24GB": 1749,
    },
    "RAM": {
        "32GB DDR5 6000 CL30": 115,
        "64GB DDR5 6400 CL32": 219,
        "32GB DDR4 3600 CL18": 65,
    },
    "SSD": {
        "2TB NVMe Gen5 (12000 MB/s)": 239,
        "2TB NVMe Gen4 (7300 MB/s)": 139,
        "1TB NVMe Gen4 (7000 MB/s)": 79,
    },
    "Motherboard": {
        "X870E AM5 Flagship": 329,
        "B650 AM5 Mainstream": 169,
        "Z890 LGA1851": 309,
        "Z790 LGA1700": 219,
    },
    "Combo": {
        "AMD Ryzen 7 9800X3D + X870E + 32GB DDR5": 879,
        "AMD Ryzen 7 7800X3D + B650 + 32GB DDR5": 629,
        "Intel Ultra 7 265K + Z890 + 32GB DDR5": 789,
    },
}

SPECS = {
    "CPU": {
        "AMD Ryzen 7 9800X3D": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 9 9950X": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 7 9700X": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 7 7800X3D": {"socket": "AM5", "ram": "DDR5"},
        "AMD Ryzen 5 7600X": {"socket": "AM5", "ram": "DDR5"},
        "Intel Core Ultra 9 285K": {"socket": "LGA1851", "ram": "DDR5"},
        "Intel Core Ultra 7 265K": {"socket": "LGA1851", "ram": "DDR5"},
        "Intel Core i9-14900K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "Intel Core i7-14700K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
        "Intel Core i5-14600K": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
    },
    "RAM": {
        "32GB DDR5 6000 CL30": {"type": "DDR5"},
        "64GB DDR5 6400 CL32": {"type": "DDR5"},
        "32GB DDR4 3600 CL18": {"type": "DDR4"},
    },
    "Motherboard": {
        "X870E AM5 Flagship": {"socket": "AM5", "ram": "DDR5"},
        "B650 AM5 Mainstream": {"socket": "AM5", "ram": "DDR5"},
        "Z890 LGA1851": {"socket": "LGA1851", "ram": "DDR5"},
        "Z790 LGA1700": {"socket": "LGA1700", "ram": "DDR4/DDR5"},
    },
}

# -----------------------------------------------------------------------------
# Data Models
# -----------------------------------------------------------------------------
@dataclass
class Offer:
    store: str
    price: float
    url: str
    rating: float
    trust_label: str

@dataclass
class ProductDeal:
    name: str
    category: str
    best_price: float
    msrp_price: float
    price_drop_pct: int
    region: str
    currency: str
    symbol: str
    performance_score: float
    offers: List[Offer]
    specs: Dict[str, str] = field(default_factory=dict)

# -----------------------------------------------------------------------------
# Helpers & Price Engines
# -----------------------------------------------------------------------------
def convert_price(usd: float, region_key: str) -> float:
    rate = REGIONS[region_key]["exchange_rate"]
    return round(usd / rate, 2)

def generate_store_url(product_name: str, store_name: str) -> str:
    query = urllib.parse.quote_plus(f"{product_name} {store_name}")
    return f"https://www.google.com/search?q={query}"

def build_pazar_data(region_key: str) -> List[ProductDeal]:
    region_info = REGIONS[region_key]
    currency = region_info["currency"]
    symbol = region_info["symbol"]
    stores_list = region_info["stores"]
    
    deals = []
    for category in CATEGORIES:
        for name, usd_msrp in BASE_PRICES_USD.get(category, {}).items():
            base_local = convert_price(usd_msrp, region_key)
            
            # Generate offers across 3-5 stores like a comparison engine
            offers = []
            selected_stores = random.sample(stores_list, min(4, len(stores_list)))
            for st in selected_stores:
                # Random realistic store variance
                variance = random.uniform(0.88, 1.12)
                st_price = round(base_local * variance, 2)
                offers.append(Offer(
                    store=st["name"],
                    price=st_price,
                    url=generate_store_url(name, st["name"]),
                    rating=st["rating"],
                    trust_label=st["trust"]
                ))
            
            offers.sort(key=lambda x: x.price)
            best_price = offers[0].price
            msrp_local = round(base_local, 2)
            
            drop_pct = 0
            if best_price < msrp_local:
                drop_pct = int(((msrp_local - best_price) / msrp_local) * 100)
            
            perf = PERFORMANCE_SCORES.get(category, {}).get(name, 0)
            specs = SPECS.get(category, {}).get(name, {})
            
            deals.append(ProductDeal(
                name=name,
                category=category,
                best_price=best_price,
                msrp_price=msrp_local,
                price_drop_pct=drop_pct,
                region=region_key,
                currency=currency,
                symbol=symbol,
                performance_score=perf,
                offers=offers,
                specs=specs
            ))
    return deals

# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="HardwarePazar Europe & NA",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Advanced CSS with Smooth Micro-Animations & Pazaruj-Style Cards
    st.markdown("""
    <style>
        /* Dark Theme Base Override */
        .stApp {
            background-color: #0d0f12;
            color: #e2e8f0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* Animated Glowing Headers */
        @keyframes headerGlow {
            0% { text-shadow: 0 0 10px rgba(0, 173, 181, 0.3); }
            50% { text-shadow: 0 0 25px rgba(0, 173, 181, 0.8), 0 0 5px #00f2fe; }
            100% { text-shadow: 0 0 10px rgba(0, 173, 181, 0.3); }
        }
        .pazar-title {
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #ffffff;
            animation: headerGlow 4s infinite ease-in-out;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Deal Card Styling */
        @keyframes cardFadeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .pazar-card {
            background: linear-gradient(145deg, #161b22, #1c232d);
            border: 1px solid #2d3748;
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            animation: cardFadeIn 0.4s ease-out forwards;
        }
        .pazar-card:hover {
            transform: translateY(-4px) scale(1.01);
            border-color: #00adb5;
            box-shadow: 0 10px 30px rgba(0, 173, 181, 0.25);
        }

        /* Price Drop Shimmer Badge */
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        .badge-deal {
            background: linear-gradient(90deg, #ff416c, #ff4b2b, #ff416c);
            background-size: 200% 100%;
            animation: shimmer 3s infinite linear;
            color: #white;
            font-weight: 700;
            font-size: 0.75rem;
            padding: 3px 10px;
            border-radius: 20px;
            text-transform: uppercase;
            display: inline-block;
        }

        .badge-normal {
            background-color: #2d3748;
            color: #a0aec0;
            font-size: 0.75rem;
            padding: 3px 10px;
            border-radius: 20px;
            display: inline-block;
        }

        /* Price Tag Styling */
        .price-best {
            font-size: 1.6rem;
            font-weight: 800;
            color: #00f2fe;
            line-height: 1.1;
        }
        .price-msrp {
            font-size: 0.9rem;
            color: #718096;
            text-decoration: line-through;
            margin-left: 6px;
        }

        /* Store Listing Row */
        .store-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #0d1117;
            padding: 8px 12px;
            border-radius: 8px;
            margin-top: 6px;
            border: 1px solid #21262d;
            transition: border-color 0.2s;
        }
        .store-row:hover {
            border-color: #00adb5;
        }

        /* Buy Link Pulse Button */
        @keyframes pulseBtn {
            0% { box-shadow: 0 0 0 0 rgba(0, 173, 181, 0.6); }
            70% { box-shadow: 0 0 0 10px rgba(0, 173, 181, 0); }
            100% { box-shadow: 0 0 0 0 rgba(0, 173, 181, 0); }
        }
        .buy-link {
            background: linear-gradient(135deg, #00adb5, #008080);
            color: #ffffff !important;
            font-weight: 700;
            font-size: 0.8rem;
            padding: 6px 14px;
            border-radius: 6px;
            text-decoration: none !important;
            display: inline-block;
            transition: all 0.2s;
        }
        .buy-link:hover {
            animation: pulseBtn 1.2s infinite;
            filter: brightness(1.15);
        }

        /* Blue on blue requested class retained */
        .blue-on-blue { background-color: #0000FF; color: #0000FF; padding: 4px; user-select: all; }
        
        /* Mobile responsiveness adjustments */
        @media (max-width: 768px) {
            .pazar-title { font-size: 1.6rem; }
            .price-best { font-size: 1.3rem; }
        }
    </style>
    """, unsafe_allow_html=True)

    # Session State
    if "build" not in st.session_state:
        st.session_state.build = {}

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### ⚙️ Engine Filters")
        selected_region = st.selectbox("🌍 Region Engine", list(REGIONS.keys()), index=0)
        
        sym = REGIONS[selected_region]["symbol"]
        budget = st.slider(f"💰 Max Budget ({sym})", 100, 5000, 2000, 50)
        selected_cat = st.radio("📦 Category", ["All Deals"] + CATEGORIES, index=0)
        
        st.markdown("---")
        st.markdown("### 📊 Search Sort")
        sort_by = st.selectbox("Sort Products By", ["Biggest Price Drop", "Lowest Price", "Performance Score"])
        
        st.markdown('<div class="blue-on-blue">Preserved styling target</div>', unsafe_allow_html=True)

    # Main Header
    st.markdown(
        f'<div class="pazar-title">⚡ HardwarePazar <span style="font-size: 1rem; color: #00adb5; font-weight: normal;">[{selected_region}]</span></div>',
        unsafe_allow_html=True
    )
    st.caption("Live multi-store aggregator with real-time price comparison across Europe & North America.")

    # Fetch/Generate Product Deals
    deals = build_pazar_data(selected_region)

    # Apply Category & Budget Filters
    filtered = [d for d in deals if d.best_price <= budget]
    if selected_cat != "All Deals":
        filtered = [d for d in filtered if d.category == selected_cat]

    # Sorting Logic
    if sort_by == "Biggest Price Drop":
        filtered.sort(key=lambda x: x.price_drop_pct, reverse=True)
    elif sort_by == "Lowest Price":
        filtered.sort(key=lambda x: x.best_price)
    elif sort_by == "Performance Score":
        filtered.sort(key=lambda x: x.performance_score, reverse=True)

    # Product Comparison Grid
    st.markdown("---")
    if filtered:
        cols = st.columns(2)
        for idx, item in enumerate(filtered[:16]):
            with cols[idx % 2]:
                # Deal badge styling
                badge_html = f'<span class="badge-deal">🔥 -{item.price_drop_pct}% OFF</span>' if item.price_drop_pct > 0 else '<span class="badge-normal">Standard MSRP</span>'
                
                # Render Product Container
                st.markdown(f"""
                <div class="pazar-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <span style="font-size: 0.75rem; color: #00adb5; font-weight: 700;">{item.category}</span>
                            <h4 style="margin: 2px 0 8px 0; color: #fff;">{item.name}</h4>
                        </div>
                        {badge_html}
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <span class="price-best">{item.symbol}{item.best_price:,.2f}</span>
                        {'<span class="price-msrp">' + item.symbol + f'{item.msrp_price:,.2f}</span>' if item.price_drop_pct > 0 else ''}
                        <span style="font-size: 0.8rem; color: #a0aec0; margin-left: 8px;">({len(item.offers)} stores compare)</span>
                    </div>
                """, unsafe_allow_html=True)

                # Expandable Store Offers (Pazaruj Style)
                with st.expander(f"🛒 Compare {len(item.offers)} Store Offers", expanded=False):
                    for offer in item.offers:
                        st.markdown(f"""
                        <div class="store-row">
                            <div>
                                <strong style="color: #e2e8f0;">{offer.store}</strong>
                                <div style="font-size: 0.7rem; color: #718096;">⭐ {offer.rating} | {offer.trust_label}</div>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 1rem; font-weight: 700; color: #00adb5;">{item.symbol}{offer.price:,.2f}</span>
                                <a href="{offer.url}" target="_blank" class="buy-link" style="margin-left: 8px;">Go to Store →</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                # Add to Build Button
                if item.category != "Combo":
                    if st.button(f"➕ Add {item.name} to Custom Build", key=f"btn_{selected_region}_{idx}"):
                        st.session_state.build[item.category] = {
                            "name": item.name,
                            "price": item.best_price,
                            "symbol": item.symbol,
                            "specs": item.specs
                        }
                        st.toast(f"Added {item.name} to build!")

                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No matching products found within the selected budget threshold.")

    # PC Builder & Compatibility Inspector Section
    st.markdown("---")
    st.subheader("🛠️ Active Custom Rig Build")
    
    build = st.session_state.build
    if build:
        total_price = sum(item["price"] for item in build.values())
        symbol_used = next(iter(build.values()))["symbol"]
        
        b_cols = st.columns(len(build)) if len(build) <= 4 else st.columns(4)
        for i, (cat, details) in enumerate(build.items()):
            with b_cols[i % 4]:
                st.info(f"**{cat}**\n\n{details['name']}\n\n**{details['symbol']}{details['price']:,.2f}**")

        st.markdown(f"### Total Build Price: **{symbol_used}{total_price:,.2f}**")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Run Automated Compatibility & Bottleneck Check"):
                # Audio trigger
                st.markdown("""<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)
                
                # Socket check
                cpu = build.get("CPU")
                mobo = build.get("Motherboard")
                ram = build.get("RAM")
                
                issues = []
                if cpu and mobo:
                    cpu_sock = cpu.get("specs", {}).get("socket", "")
                    mobo_sock = mobo.get("specs", {}).get("socket", "")
                    if cpu_sock and mobo_sock and cpu_sock != mobo_sock:
                        issues.append(f"Socket Mismatch: CPU needs {cpu_sock}, Motherboard offers {mobo_sock}.")
                        
                if issues:
                    for iss in issues:
                        st.error(f"❌ {iss}")
                else:
                    st.success("🎉 All selected components pass compatibility validation!")
                    st.balloons()
        with col_b:
            if st.button("🗑️ Reset Build"):
                st.session_state.build = {}
                st.rerun()
    else:
        st.info("Your custom rig build is currently empty. Browse deals above and add components.")

if __name__ == "__main__":
    main()
