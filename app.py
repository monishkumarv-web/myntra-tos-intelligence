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
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import re
import urllib.parse

# ─────────────────────────────────────────────────────────────────────────────
# 🏢 STREAMLIT CONFIG & GLOBAL THEMING
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Myntra TOS Intelligence Dashboard", layout="wide")

OUTPUT_CSV   = r"C:\Users\monishkumar.v\Desktop\Scrapping\dashboard_cache.csv"
TARGET_BRAND = "CULT"

# Inject Custom SaaS CSS Stylesheet
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Global typography smoothing */
        .stApp { font-family: 'Inter', sans-serif; }
        
        /* Dashboard Hero Banner */
        .dashboard-banner { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #ffffff; padding: 32px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .dashboard-banner h1 { color: #ffffff !important; font-size: 28px; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
        .dashboard-banner p { color: #94a3b8 !important; margin: 8px 0 0 0; font-size: 14px; }
        
        /* Executive Analytics Grid */
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
        
        /* Modern Activity Stream Component Cards */
        .stream-card { background: #ffffff !important; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); transition: transform 0.2s ease; }
        .stream-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .stream-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 12px; margin-bottom: 14px; }
        .stream-title { font-size: 16px; font-weight: 600; color: #0f172a !important; margin: 0; }
        
        /* Status Badges Component */
        .pill { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; }
        .pill-green { background: #dcfce7 !important; color: #15803d !important; }
        .pill-orange { background: #ffedd5 !important; color: #c2410c !important; }
        .pill-red { background: #fee2e2 !important; color: #b91c1c !important; }
        .pill-dark { background: #f1f5f9 !important; color: #334155 !important; font-family: monospace; }
        
        /* Metadata Information Layout Grid */
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
# ⚙️ AUTOMATION PIPELINE LAYER (SELENIUM CORE ENGINE)
# ─────────────────────────────────────────────────────────────────────────────
def run_live_scraper(keywords):
    if not keywords:
        st.warning("⚠️ Please enter at least one target keyword row to scan.")
        return False

    if os.path.exists(OUTPUT_CSV):
        try:
            os.remove(OUTPUT_CSV)
        except:
            pass

    # 🔧 STREAMLIT CLOUD COMPATIBLE CHROME CONFIGURATION
    options = Options()
    options.add_argument("--headless=new")       
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    # Point directly to the Linux package installs on the Streamlit server
    options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    # Launch driver natively without using ChromeDriverManager()
    driver = webdriver.Chrome(service=service, options=options)
    all_results = []
    
    # ... (Keep the rest of your scraper loops exactly the same!)
    try:
        for idx, keyword in enumerate(keywords, start=1):
            keyword_clean = keyword.strip()
            if not keyword_clean:
                continue
                
            status_text.markdown(f"⏳ **Scraping item ({idx}/{len(keywords)}):** `{keyword_clean}`...")
            
            encoded_query = urllib.parse.quote(keyword_clean)
            search_url = f"https://www.myntra.com/{encoded_query}?rawQuery={encoded_query}"
            
            row = [keyword_clean, "No", "No TOS", "No TOS", "No TOS", "", "N/A", "Not Found"]
            
            try:
                driver.get(search_url)
                time.sleep(3.5)
                
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight/1.5);")
                time.sleep(1)
                
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.product-base")))
                
                soup = BeautifulSoup(driver.page_source, "html.parser")
                products = soup.select("li.product-base")
                
                if products:
                    found_cult = False
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
                                if id_match:
                                    style_id = id_match.group(1)
                            
                            is_ad = False
                            if prod.select_one(".product-adBadge, [class*='adBadge'], .xcomm-ad-tag"):
                                is_ad = True
                            else:
                                for tag in prod.find_all(["div", "span"]):
                                    if tag.get_text(strip=True).upper() == "AD":
                                        is_ad = True
                                        break
                            
                            listing_type = "Ad" if is_ad else "Organic"
                            
                            if rank <= 4:
                                row = [keyword_clean, "Yes", brand_name, product_name, style_id, rank, listing_type, "Top 4 Verified"]
                            else:
                                row = [keyword_clean, "No", brand_name, product_name, style_id, rank, listing_type, "Found Down Page"]
                            
                            found_cult = True
                            break
                    
                    if not found_cult:
                        row = [keyword_clean, "No", "No TOS", "No TOS", "No TOS", "", "N/A", "Outside Page 1"]
                else:
                    row = [keyword_clean, "No", "N/A", "N/A", "N/A", "", "N/A", "No Results"]

            except Exception as item_err:
                row = [keyword_clean, "Error", "N/A", "N/A", "N/A", "", "N/A", f"Error: {str(item_err)[:20]}"]

            all_results.append(row)
            
            df_running = pd.DataFrame(all_results, columns=["Search_Term", "Cult_In_Top_4", "Brand_Found", "Product_Name", "Style_ID", "Rank_Position", "Listing_Type", "Status"])
            df_running.to_csv(OUTPUT_CSV, index=False)
            
            progress_bar.progress(idx / len(keywords))

        status_text.empty()
        progress_bar.empty()
        return True
    finally:
        driver.quit()

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 APPLICATION FRONTEND LAYER (CLEAN PREMIUM LAYOUT DESIGN)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dashboard-banner">
        <h1>🎯 Myntra Share of Voice & TOS Intelligence Engine</h1>
        <p>Real-time shareable competitive analytics platform monitoring brand visibility across premium layout search grids.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Control Input Panel Card Configuration
with st.expander("⌨️ Configure Query Targets & Settings", expanded=True):
    input_text = st.text_area(
        label="Enter target terms (One keyword string per line description layout):",
        value="cult sport shoes\ncult t-shirt\nrunning shoes",
        height=120
    )
    
    input_keywords = [line.strip() for line in input_text.split("\n") if line.strip()]
    
    st.write("")
    run_btn = st.button("🚀 Execute Live Visibility Scan", type="primary", use_container_width=True)

if run_btn:
    with st.spinner("Executing secure browser session tracking routines..."):
        success = run_live_scraper(input_keywords)
        if success:
            st.toast("Analytics extraction completed successfully!", icon="🎉")

st.markdown("<br>", unsafe_allow_html=True)

# Data Display Render Loop Block
if os.path.exists(OUTPUT_CSV):
    try:
        df = pd.read_csv(OUTPUT_CSV)
        df["Rank_Position"] = df["Rank_Position"].replace({np.nan: None})
        
        total_kws = len(df)
        top4_hits = len(df[df["Cult_In_Top_4"].astype(str).str.upper() == "YES"])
        ad_hits   = len(df[df["Listing_Type"].astype(str).str.upper() == "AD"])
        org_hits  = len(df[df["Listing_Type"].astype(str).str.upper() == "ORGANIC"])
        share_pct = (top4_hits / total_kws * 100) if total_kws > 0 else 0.0

        # Injecting Clean Styled KPI Cards Grid
        st.markdown(
            f"""
            <div class="analytics-container">
                <div class="analytics-card blue"><div class="lbl">Total Terms Run</div><div class="val">{total_kws}</div><div class="sub">Active catalog visibility tracks</div></div>
                <div class="analytics-card emerald"><div class="lbl">Top 4 Placements</div><div class="val">{top4_hits}</div><div class="sub">{share_pct:.1f}% Premium Visibility Share</div></div>
                <div class="analytics-card amber"><div class="lbl">Sponsored Ads</div><div class="val">{ad_hits}</div><div class="sub">Paid media placements found</div></div>
                <div class="analytics-card purple"><div class="lbl">Organic Matches</div><div class="val">{org_hits}</div><div class="sub">Natural algorithmic rankings</div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.subheader("📋 Search Optimization Activity Log")
        
        # Build clean custom item cards line by line safely handling mathematical NaN values
        for _, row in df.iterrows():
            is_t4 = str(row['Cult_In_Top_4']).upper() == 'YES'
            is_nf = "NOT FOUND" in str(row['Status']).upper() or "NO RESULTS" in str(row['Status']).upper() or "OUTSIDE PAGE 1" in str(row['Status']).upper()
            
            pill_class = "pill-green" if is_t4 else ("pill-orange" if not is_nf else "pill-red")
            status_txt = "TOP 4 COVERED" if is_t4 else ("BELOW TOP 4" if not is_nf else "NOT LOCATED")
            
            # ─── SAFELY HANDLE THE RANK POSITION INT CONVERSION ───
            raw_rank = row['Rank_Position']
            if pd.notna(raw_rank) and str(raw_rank).strip() != "" and str(raw_rank).strip().lower() != "none":
                try:
                    rank_display = f"#{int(float(raw_rank))}"
                except:
                    rank_display = "—"
            else:
                rank_display = "—"
                
            style_id_display = str(row['Style_ID']).strip() if pd.notna(row['Style_ID']) and str(row['Style_ID']).strip() != "" else "None"
            
            # Escape strings cleanly to prevent markup breakdown injections
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
                        <div class="meta-item"><div class="meta-label">Engine Diagnosis</div><div class="meta-value" style="font-size:12px;">{clean_status_flag}</div></div>
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
        st.error(f"Error compiling visual intelligence log: {read_err}")
else:
    st.info("💡 Input target search configurations above and hit execute to populate live dashboard data streams.")

<div style="margin-top: 12px; font-size: 13px; color: #475569;">
                        <span style="color: #94a3b8; font-weight: 500; font-size: 11px; text-transform: uppercase; display: block; margin-bottom: 2px;">Resolved Item Description</span>
                        {clean_prod}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
# ADD THESE TWO LINES AT THE VERY END OF YOUR FILE:
except Exception as e:
    st.error(f"Error compiling visual intelligence log: {e}")