"""
Ultimate Europe & NA AI Hardware Deal Aggregator & PC Builder
Multi-region price engine, store ratings, price-drop badges,
animated comparison UI, and AI compatibility checker.
"""

import time
import random
import urllib.parse
from typing import Dict, List
from dataclasses import dataclass, field

import streamlit as st

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
# Helpers & Price Engine
# -----------------------------------------------------------------------------
def convert_price(usd: float, region_key: str) -> float:
    rate = REGIONS[region_key]["exchange_rate"]
    return round(usd / rate, 2)


def generate_store_url(product_name: str, store_name: str) -> str:
    query = urllib.parse.quote_plus(f"{product_name} {store_name}")
    return f"https://www.google.com/search?q={query}"


def build_pazar_data(region_key: str) -> List[ProductDeal]:
    """Generate one simulated snapshot of deals for a region.

    NOTE: this is randomly generated demo data, not a live price feed.
    Call it once per region/session (see caching in main()) rather than
    on every rerun, or prices will visibly jump around on every click.
    """
    region_info = REGIONS[region_key]
    currency = region_info["currency"]
    symbol = region_info["symbol"]
    stores_list = region_info["stores"]

    deals = []
    for category in CATEGORIES:
        for name, usd_msrp in BASE_PRICES_USD.get(category, {}).items():
            base_local = convert_price(usd_msrp, region_key)

            offers = []
            selected_stores = random.sample(stores_list, min(4, len(stores_list)))
            for store in selected_stores:
                # Realistic store-to-store variance, skewed so that a genuine
                # "deal" (below MSRP) is the common case rather than a coin flip.
                variance = random.uniform(0.90, 1.07)
                store_price = round(base_local * variance, 2)
                offers.append(Offer(
                    store=store["name"],
                    price=store_price,
                    url=generate_store_url(name, store["name"]),
                    rating=store["rating"],
                    trust_label=store["trust"],
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
                specs=specs,
            ))
    return deals


def check_ram_support(component_ram_field: str, ram_type: str) -> bool:
    """True if a CPU/motherboard's supported-RAM field includes ram_type."""
    if not component_ram_field or not ram_type:
        return True
    supported = [x.strip() for x in component_ram_field.split("/")]
    return ram_type in supported


def run_compatibility_check(build: dict) -> List[str]:
    issues = []
    cpu = build.get("CPU")
    mobo = build.get("Motherboard")
    ram = build.get("RAM")

    if cpu and mobo:
        cpu_sock = cpu.get("specs", {}).get("socket", "")
        mobo_sock = mobo.get("specs", {}).get("socket", "")
        if cpu_sock and mobo_sock and cpu_sock != mobo_sock:
            issues.append(
                f"Socket mismatch: {cpu['name']} needs {cpu_sock}, "
                f"but {mobo['name']} is {mobo_sock}."
            )

    if mobo and ram:
        mobo_ram = mobo.get("specs", {}).get("ram", "")
        ram_type = ram.get("specs", {}).get("type", "")
        if not check_ram_support(mobo_ram, ram_type):
            issues.append(
                f"Memory mismatch: {mobo['name']} supports {mobo_ram}, "
                f"but {ram['name']} is {ram_type}."
            )

    if cpu and ram:
        cpu_ram = cpu.get("specs", {}).get("ram", "")
        ram_type = ram.get("specs", {}).get("type", "")
        if not check_ram_support(cpu_ram, ram_type):
            issues.append(
                f"Memory mismatch: {cpu['name']} supports {cpu_ram}, "
                f"but {ram['name']} is {ram_type}."
            )

    return issues


# -----------------------------------------------------------------------------
# Main Application
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="HardwarePazar Europe & NA",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
        .stApp {
            background-color: #0d0f12;
            color: #e2e8f0;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

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

        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        .badge-deal {
            background: linear-gradient(90deg, #ff416c, #ff4b2b, #ff416c);
            background-size: 200% 100%;
            animation: shimmer 3s infinite linear;
            color: white;
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
            filter: brightness(1.15);
        }

        @media (max-width: 768px) {
            .pazar-title { font-size: 1.6rem; }
            .price-best { font-size: 1.3rem; }
        }
    </style>
    """, unsafe_allow_html=True)

    # Session State
    if "build" not in st.session_state:
        st.session_state.build = {}
    if "deals_cache" not in st.session_state:
        st.session_state.deals_cache = {}
    if "last_generated" not in st.session_state:
        st.session_state.last_generated = {}

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

        st.markdown("---")
        refresh_clicked = st.button("🔄 Refresh Prices", use_container_width=True)
        if selected_region in st.session_state.last_generated:
            st.caption(f"Prices generated at {st.session_state.last_generated[selected_region]}")
        st.caption("Demo data: prices are simulated, not a live feed.")

    # Generate (or reuse cached) deals for this region — only regenerate on
    # region change or explicit refresh, so prices stay stable while the
    # user filters, sorts, or adds items to their build.
    if selected_region not in st.session_state.deals_cache or refresh_clicked:
        st.session_state.deals_cache[selected_region] = build_pazar_data(selected_region)
        st.session_state.last_generated[selected_region] = time.strftime("%H:%M:%S")

    deals = st.session_state.deals_cache[selected_region]

    # Main Header
    st.markdown(
        f'<div class="pazar-title">⚡ HardwarePazar '
        f'<span style="font-size: 1rem; color: #00adb5; font-weight: normal;">[{selected_region}]</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("Multi-store price comparison across Europe & North America. Simulated demo data.")

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
                # Use a real bordered container so the badge, price, store
                # list, and "add to build" button are all visually contained
                # together — raw <div>...</div> spread across separate
                # st.markdown() calls doesn't actually wrap the widgets in
                # between, which is why things used to look disconnected.
                with st.container(border=True):
                    head_col, badge_col = st.columns([3, 1])
                    with head_col:
                        st.markdown(
                            f'<span style="font-size:0.75rem;color:#00adb5;font-weight:700;">{item.category}</span>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"#### {item.name}")
                    with badge_col:
                        if item.price_drop_pct > 0:
                            st.markdown(f'<span class="badge-deal">🔥 -{item.price_drop_pct}% OFF</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="badge-normal">Standard MSRP</span>', unsafe_allow_html=True)

                    price_html = f'<span class="price-best">{item.symbol}{item.best_price:,.2f}</span>'
                    if item.price_drop_pct > 0:
                        price_html += f'<span class="price-msrp">{item.symbol}{item.msrp_price:,.2f}</span>'
                    price_html += f'<span style="font-size:0.8rem;color:#a0aec0;margin-left:8px;">({len(item.offers)} stores)</span>'
                    st.markdown(price_html, unsafe_allow_html=True)

                    with st.expander(f"🛒 Compare {len(item.offers)} store offers", expanded=False):
                        for offer in item.offers:
                            st.markdown(f"""
                            <div class="store-row">
                                <div>
                                    <strong style="color: #e2e8f0;">{offer.store}</strong>
                                    <div style="font-size: 0.7rem; color: #718096;">⭐ {offer.rating} | {offer.trust_label}</div>
                                </div>
                                <div style="text-align: right;">
                                    <span style="font-size: 1rem; font-weight: 700; color: #00adb5;">{item.symbol}{offer.price:,.2f}</span>
                                    <a href="{offer.url}" target="_blank" class="buy-link" style="margin-left: 8px;">Search this deal →</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                    if item.category != "Combo":
                        if st.button(f"➕ Add {item.name} to Custom Build", key=f"btn_{selected_region}_{idx}", use_container_width=True):
                            st.session_state.build[item.category] = {
                                "name": item.name,
                                "price": item.best_price,
                                "symbol": item.symbol,
                                "specs": item.specs,
                            }
                            st.toast(f"Added {item.name} to build!")
    else:
        st.warning("No matching products found within the selected budget threshold.")

    # PC Builder & Compatibility Inspector Section
    st.markdown("---")
    st.subheader("🛠️ Active Custom Rig Build")

    build = st.session_state.build
    if build:
        total_price = sum(item["price"] for item in build.values())
        symbol_used = next(iter(build.values()))["symbol"]

        b_cols = st.columns(min(len(build), 4))
        for i, (cat, details) in enumerate(build.items()):
            with b_cols[i % 4]:
                st.info(f"**{cat}**\n\n{details['name']}\n\n**{details['symbol']}{details['price']:,.2f}**")

        st.markdown(f"### Total Build Price: **{symbol_used}{total_price:,.2f}**")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Run Compatibility & Bottleneck Check", use_container_width=True):
                issues = run_compatibility_check(build)
                if issues:
                    for iss in issues:
                        st.error(f"❌ {iss}")
                else:
                    st.success("🎉 All selected components pass compatibility validation!")
                    st.balloons()
        with col_b:
            if st.button("🗑️ Reset Build", use_container_width=True):
                st.session_state.build = {}
                st.rerun()
    else:
        st.info("Your custom rig build is currently empty. Browse deals above and add components.")


if __name__ == "__main__":
    main()
