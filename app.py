import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
import re
import urllib.parse
import platform
import requests

# ─────────────────────────────────────────────────────────────────────────────
# 🔑 ENTER YOUR MASTER PROXY KEY HERE ONCE
# ─────────────────────────────────────────────────────────────────────────────
# Go to scraperapi.com, create a free account in 10 seconds (no credit card), 
# and paste your API key here. Your users will NEVER see this or have to type it!
SCRAPERAPI_KEY = "b38c9824416ae6e528b18e75a83a4d9b"

# 🏢 STREAMLIT CONFIG & GLOBAL CONFIG
st.set_page_config(page_title="Myntra TOS Intelligence Dashboard", layout="wide")
OUTPUT_CSV   = "dashboard_cache.csv"
TARGET_BRAND = "CULT"

# Inject Custom SaaS CSS Stylesheet
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700&display=swap');
        .stApp { font-family: 'Inter', sans-serif; }
        .dashboard-banner { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 32px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .dashboard-banner h1 { color: #ffffff !important; font-size: 28px; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
        .dashboard-banner p { color: #94a3b8 !important; margin: 8px 0 0 0; font-size: 14px; }
        .analytics-container { display: flex; gap: 20px; margin-bottom: 35px; }
        .analytics-card { background: #ffffff !important; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; flex: 1; box-shadow: 0 1px 3px rgba(0,0,0,0.02); position: relative; overflow: hidden; }
        .analytics-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #cbd5e1; }
        .analytics-card.blue::before { background: #3b82f6; }
        .analytics-card.emerald::before { background: #10b981; }
        .analytics-card.amber::before { background: #f59e0b; }
        .analytics-card.purple::before { background: #8b5cf6; }
        .analytics-card .lbl { font-size: 12px; color: #64748b !important; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
        .analytics-card .val { font-size: 28px; font-weight: 700; color: #0f172a !important; margin: 6px 0 2px 0; }
        .analytics-card .sub { font-size: 11px; color: #94a3b8 !important; }
        .stream-card { background: #ffffff !important; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); transition: transform 0.2s ease; }
        .stream-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .stream-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 14px; }
        .stream-title { font-size: 16px; font-weight: 600; color: #0f172a !important; margin: 0; }
        .pill { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; }
        .pill-green { background: #dcfce7 !important; color: #15803d !important; }
        .pill-orange { background: #ffedd5 !important; color: #c2410c !important; }
        .pill-red { background: #fee2e2 !important; color: #b91c1c !important; }
        .meta-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
        .meta-item { font-size: 13px; color: #334155 !important; }
        .meta-label { color: #64748b !important; font-size: 11px; font-weight: 500; text-transform: uppercase; margin-bottom: 2px; }
        .meta-value { font-weight: 600; color: #1e293b !important; }
        .code-style { font-family: monospace; background: #f8fafc; padding: 2px 6px; border-radius: 4px; border: 1px solid #e2e8f0; }
    </style>
    """,
    unsafe_allow_html=True
)

# ─────────────────────────────────────────────────────────────────────────────
# 🛡️ UNIFIED DATA PARSING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def parse_myntra_html(html_content, keyword_clean):
    soup = BeautifulSoup(html_content, "html.parser")
    products = soup.select("li.product-base")
    
    if products:
        for rank, prod in enumerate(products, start=1):
            brand_el = prod.select_one(".product-brand")
            brand_name = brand_el.get_text(strip=True) if brand_el else ""
            
            if TARGET_BRAND.lower() in brand_name.lower():
                product_el = prod.select_one(".product-product")
                product_name = product_el.get_text(strip=True) if product_el else ""
                
                style_id = ""
                link_el = prod.select_one("a[href]")
                if link_el and link_el.get("href"):
                    href_str = link_el["href"]
                    id_match = re.search(r"/(\d+)/buy", href_str) or re.search(r"/(\d+)(?:\.html)?$", href_str)
                    if id_match: style_id = id_match.group(1)
                
                is_ad = False
                if prod.select_one(".product-adBadge, [class*='adBadge'], .xcomm-ad-tag"):
                    is_ad = True
                else:
                    for tag in prod.find_all(["div", "span"]):
                        if tag.get_text(strip=True).upper() == "AD":
                            is_ad = True
                            break
                
                listing_type = "Ad" if is_ad else "Organic"
                status_msg = "Top 4 Verified" if rank <= 4 else "Found Down Page"
                return [keyword_clean, "Yes" if rank <= 4 else "No", brand_name, product_name, style_id, rank, listing_type, status_msg]
        
        return [keyword_clean, "No", "Outside Page 1", "Outside Page 1", "None", "", "N/A", "Outside Page 1"]
    
    return [keyword_clean, "No", "N/A", "N/A", "None", "", "N/A", "No Products Found"]

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ AUTO-SENSING AUTOMATION ROUTING ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def run_live_scraper(keywords):
    if not keywords:
        st.warning("⚠️ Please enter target terms to run scan loops.")
        return False

    if os.path.exists(OUTPUT_CSV):
        try: os.remove(OUTPUT_CSV)
        except: pass

    # 🤖 AUTO-DETECTION: Windows laptop means local testing. Linux means Streamlit Cloud production.
    is_local_machine = (platform.system() == "Windows")
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    all_results = []
    driver = None
    
    if is_local_machine:
        options = Options()
        options.add_argument("--headless=new")       
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        driver = webdriver.Chrome(options=options)

    try:
        for idx, keyword in enumerate(keywords, start=1):
            keyword_clean = keyword.strip()
            if not keyword_clean: continue
            
            status_text.markdown(f"⏳ **Scanning Matrix Item ({idx}/{len(keywords)}):** `{keyword_clean}`...")
            encoded_query = urllib.parse.quote(keyword_clean)
            search_url = f"https://www.myntra.com/{encoded_query}?rawQuery={encoded_query}"
            
            row = [keyword_clean, "No", "Network Timeout", "Data Incomplete", "None", "", "N/A", "Execution Interrupted"]
            
            try:
                if is_local_machine:
                    # ⚡ LOCAL OPERATION PATH (Direct Selenium)
                    driver.get(search_url)
                    time.sleep(4)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                    WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.product-base")))
                    row = parse_myntra_html(driver.page_source, keyword_clean)
                else:
                    # 🌐 CLOUD OPERATION PATH (Invisible Automated Firewall Bypass)
                    if not SCRAPERAPI_KEY or "YOUR_PASTED" in SCRAPERAPI_KEY:
                        row = [keyword_clean, "No", "Configuration Error", "Missing API Master Key Token", "None", "", "N/A", "Setup Incomplete"]
                    else:
                        proxy_url = f"https://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={urllib.parse.quote(search_url)}"
                        res = requests.get(proxy_url, timeout=30)
                        if res.status_code == 200:
                            row = parse_myntra_html(res.text, keyword_clean)
                        else:
                            row = [keyword_clean, "No", "Proxy Error", f"HTTP {res.status_code}", "None", "", "N/A", "Gateway Rejection"]
                            
            except Exception as e:
                err_str = str(e)
                status_desc = "Blocked by Firewall" if "TimeoutException" in type(e).__name__ or "Message" in err_str else f"Error: {err_str[:20]}"
                row = [keyword_clean, "No", "Security Filtered", "Data Blocked", "None", "", "N/A", status_desc]

            all_results.append(row)
            pd.DataFrame(all_results, columns=["Search_Term", "Cult_In_Top_4", "Brand_Found", "Product_Name", "Style_ID", "Rank_Position", "Listing_Type", "Status"]).to_csv(OUTPUT_CSV, index=False)
            progress_bar.progress(idx / len(keywords))
            
    finally:
        if driver: driver.quit()
        status_text.empty()
        progress_bar.empty()
    return True

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 APPLICATION FRONTEND LAYER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dashboard-banner">
        <h1>🎯 Myntra Share of Voice & Shareable Intelligence Dashboard</h1>
        <p>Enterprise layout matrix monitoring brand position visibility smoothly across runtime environments.</p>
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("⌨️ Target Query Grid Setup", expanded=True):
    input_text = st.text_area("Targets (One keyword per line):", value="yoga mat\nshaker\nsteel bottle\nduffle bag", height=110)
    input_keywords = [line.strip() for line in input_text.split("\n") if line.strip()]
    run_btn = st.button("🚀 Run Live Visibility Diagnostic Scan", type="primary", use_container_width=True)

if run_btn:
    with st.spinner("Processing network extraction routines..."):
        if run_live_scraper(input_keywords):
            st.toast("Dashboard data mapping completed successfully!", icon="🎉")

st.markdown("<br>", unsafe_allow_html=True)

if os.path.exists(OUTPUT_CSV):
    try:
        df = pd.read_csv(OUTPUT_CSV)
        total_kws = len(df)
        top4_hits = len(df[df["Cult_In_Top_4"].astype(str).str.upper() == "YES"])
        ad_hits   = len(df[df["Listing_Type"].astype(str).str.upper() == "AD"])
        org_hits  = len(df[df["Listing_Type"].astype(str).str.upper() == "ORGANIC"])
        share_pct = (top4_hits / total_kws * 100) if total_kws > 0 else 0.0

        st.markdown(
            f"""
            <div class="analytics-container">
                <div class="analytics-card blue"><div class="lbl">Total Terms Run</div><div class="val">{total_kws}</div><div class="sub">Active visibility tracking tracks</div></div>
                <div class="analytics-card emerald"><div class="lbl">Top 4 Placements</div><div class="val">{top4_hits}</div><div class="sub">{share_pct:.1f}% Premium Layout Share</div></div>
                <div class="analytics-card amber"><div class="lbl">Sponsored Ads</div><div class="val">{ad_hits}</div><div class="sub">Paid media tracks verified</div></div>
                <div class="analytics-card purple"><div class="lbl">Organic Matches</div><div class="val">{org_hits}</div><div class="sub">Natural algorithmic placements</div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.subheader("📋 Search Optimization Activity Log")
        
        for _, row in df.iterrows():
            is_t4 = str(row['Cult_In_Top_4']).upper() == 'YES'
            is_nf = any(x in str(row['Status']).upper() for x in ["NOT FOUND", "NO RESULTS", "OUTSIDE", "BLOCKED", "TIMEOUT", "FILTERED", "ERROR"])
            
            pill_class = "pill-green" if is_t4 else ("pill-orange" if not is_nf else "pill-red")
            status_txt = "TOP 4 COVERED" if is_t4 else ("BELOW TOP 4" if not is_nf else "NOT LOCATED")
            
            raw_rank = row.get('Rank_Position')
            if pd.notna(raw_rank) and str(raw_rank).strip() != "" and str(raw_rank).strip().lower() not in ["none", "nan", "n/a"]:
                try: rank_display = f"#{int(float(raw_rank))}"
                except: rank_display = "—"
            else: rank_display = "—"
                
            style_id_display = str(row['Style_ID']).strip() if pd.notna(row['Style_ID']) and str(row['Style_ID']).strip() != "" else "None"
            
            clean_term = str(row['Search_Term']).replace('"', '&quot;')
            clean_brand = str(row['Brand_Found']).replace('"', '&quot;')
            clean_prod = str(row['Product_Name']).replace('"', '&quot;')
            clean_status_flag = str(row['Status']).replace('"', '&quot;')

            st.markdown(
                f"""
                <div class="stream-card">
                    <div class="stream-header">
                        <div class="stream-title">🔍 Keyword: &nbsp;<strong>{clean_term}</strong></div>
                        <span class="pill {pill_class}">{status_txt}</span>
                    </div>
                    <div class="meta-grid">
                        <div class="meta-item"><div class="meta-label">Brand Found</div><div class="meta-value">{clean_brand}</div></div>
                        <div class="meta-item"><div class="meta-label">Grid Ranking</div><div class="meta-value"><span class="code-style">{rank_display}</span> ({row['Listing_Type']})</div></div>
                        <div class="meta-item"><div class="meta-label">Myntra Style ID</div><div class="meta-value class="code-style"">{style_id_display}</div></div>
                        <div class="meta-item"><div class="meta-label">Engine Diagnosis</div><div class="meta-value" style="font-size:12px; color: {'#dc2626' if is_nf else '#16a34a'}; font-weight: 500;">{clean_status_flag}</div></div>
                    </div>
                    <div style="margin-top: 12px; font-size: 13px; color: #475569;">
                        <span style="color: #94a3b8; font-weight: 500; font-size: 11px; text-transform: uppercase; display: block; margin-bottom: 2px;">Resolved Item Description</span>
                        {clean_prod}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception as read_err:
        st.error(f"Error compiling visual intelligence log elements: {read_err}")