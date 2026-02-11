import streamlit as st
import pandas as pd
from pathlib import Path
import json
import re

"streamlit run Working_data/01_Data_Categorizer.py"

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent.parent
WORKING_DATA = PROJECT_ROOT / "Working_data"
SAMPLE_DATA = WORKING_DATA / "Sample_Data"  # ← Add this
CONFIG_FILE = WORKING_DATA / "02_Data_Categories.json"
DESCRIPTIONS_FILE = WORKING_DATA / "00_column_descriptions.json"
CATEGORIES = ["int", "float", "date", "string", "IGNORE"]

# --- STORAGE FUNCTIONS ---
def load_categories():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def load_descriptions():
    if DESCRIPTIONS_FILE.exists():
        try:
            with open(DESCRIPTIONS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_single_category(file_name, col_name, new_category):
    """Updates a single category in the JSON file immediately"""
    current_data = load_categories()
    if file_name not in current_data:
        current_data[file_name] = {}
    
    current_data[file_name][col_name] = new_category
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(current_data, f, indent=2)

# --- ANALYTICS ENGINE ---
def get_dominance_stats(series):
    """Calculates how dominant the most frequent value is."""
    clean = series.dropna().astype(str)
    clean = clean[clean.str.strip().str.len() > 0]
    
    if len(clean) == 0:
        return 0.0
        
    counts = clean.value_counts(normalize=True)
    top_pct = counts.iloc[0]
    return top_pct

def analyze_column(series):
    """
    Analyzes column to return strict type matches.
    """
    # 1. Base Clean (Filter out empty/whitespace)
    clean_series = series.dropna().astype(str)
    clean_series = clean_series[clean_series.str.strip().str.len() > 0]
    
    total_rows = len(series)
    filled_rows = len(clean_series)
    
    # Initialize Stats
    stats = {k: 0.0 for k in CATEGORIES}
    
    # 2. Check IGNORE (Empty / Dominance)
    is_ignore = False
    ignore_reason = ""
    
    if filled_rows == 0:
        is_ignore = True
        ignore_reason = "Empty"
    else:
        fill_rate = filled_rows / total_rows
        if fill_rate < 0.05: # >95% Empty
            is_ignore = True
            ignore_reason = f">95% Empty ({ (1-fill_rate)*100:.1f}%)"
        else:
            # Dominance Check
            counts = clean_series.value_counts(normalize=True)
            top_freq = counts.iloc[0]
            if top_freq >= 0.95:
                is_ignore = True
                ignore_reason = f"Dominance {top_freq:.0%}"

    # 3. Numeric Analysis (Strict separation)
    cleaned_str = clean_series.str.replace(r'[$,_\s)]', '', regex=True).str.replace('(', '-', regex=False)
    numeric_series = pd.to_numeric(cleaned_str, errors='coerce')
    
    if filled_rows > 0:
        valid_numerics = numeric_series.notna()
        numeric_count = valid_numerics.sum()
        
        # Calculate Non-Numeric % (This is the "string" score)
        stats['string'] = (filled_rows - numeric_count) / filled_rows
        
        # Strict Int: Numeric AND No remainder
        ints = numeric_series[valid_numerics]
        strict_ints = (ints % 1 == 0).sum()
        stats['int'] = strict_ints / filled_rows
        
        # Strict Float: Numeric AND Remainder
        strict_floats = (ints % 1 != 0).sum()
        stats['float'] = strict_floats / filled_rows

    # 4. Strict Date Analysis
    if filled_rows > 0:
        try:
            # Try parsing everything
            dates = pd.to_datetime(clean_series, errors='coerce')
            is_valid_date = dates.notna()
            
            # Identify pure numbers (like "2023" or "1")
            is_pure_number = clean_series.str.match(r'^\d+$')
            
            # Logic: If it's a pure number, it must be 8 digits (YYYYMMDD) to count as a date.
            # This prevents "2023" (4 digits) from being called a date.
            mask_exclude = is_pure_number & (clean_series.str.len() != 8)
            
            final_date_mask = is_valid_date & (~mask_exclude)
            
            stats['date'] = final_date_mask.sum() / filled_rows
        except:
            stats['date'] = 0.0
            
    # 5. Recommendation Logic (Threshold: 95%)
    confident = True
    
    if is_ignore:
        rec_type = "IGNORE"
        rec_reason = ignore_reason
    elif stats['int'] >= 0.95:
        rec_type = "int"
        rec_reason = f"Integers ({stats['int']:.0%})"
    elif (stats['int'] + stats['float']) >= 0.95:
        rec_type = "float"
        rec_reason = f"Numeric (contains decimals)"
    elif stats['date'] >= 0.95:
        rec_type = "date"
        rec_reason = f"Dates ({stats['date']:.0%})"
    else:
        rec_type = "string"
        rec_reason = "Mixed Content"
        confident = False
        
    return {
        "recommended": rec_type,
        "reason": rec_reason,
        "confident": confident,
        "stats": stats
    }

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Data Type Assessor", layout="wide")
    
    # Custom CSS
    st.markdown("""
        <style>
        .green-header { color: #0f5132; background-color: #d1e7dd; padding: 10px; border-radius: 5px; border-left: 5px solid #198754; }
        .red-header { color: #842029; background-color: #f8d7da; padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545; }
        .ignore-header { color: #495057; background-color: #e2e3e5; padding: 10px; border-radius: 5px; border-left: 5px solid #6c757d; }
        .block-container { padding-top: 1rem; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛡️ Rapid Column Categorizer")

    if not WORKING_DATA.exists():
        st.error(f"Folder not found: {WORKING_DATA}")
        return

    # Load files
    csv_files = sorted(list(SAMPLE_DATA.glob("sample_*.csv")))
    file_names = [f.name for f in csv_files]
    saved_data = load_categories()
    descriptions = load_descriptions()
    
    # File Selector
    col_sel, col_prog = st.columns([1, 2])
    with col_sel:
        selected_file = st.selectbox("Select File", file_names, key="file_selector")
    
    if not selected_file: return
    
    # Load Data
    file_path = SAMPLE_DATA / selected_file
    df = pd.read_csv(file_path)
    if selected_file not in saved_data: saved_data[selected_file] = {}
    
    # Get descriptions for this file
    file_descriptions = descriptions.get(selected_file, {})

    # Stats
    total_cols = len(df.columns)
    saved_cols = len([c for c in df.columns if c in saved_data[selected_file]])
    
    with col_prog:
        st.write("") 
        st.progress(saved_cols/total_cols)
    
    st.markdown("---")

    # --- PROCESS COLUMNS ---
    for col in df.columns:
        series = df[col]
        
        # 1. Analyze
        analysis = analyze_column(series)
        stats = analysis['stats']
        
        is_saved = col in saved_data[selected_file]
        saved_val = saved_data[selected_file].get(col)
        
        # Determine Display State
        if is_saved:
            current_cat = saved_val
            is_green = True 
            auto_msg = "SAVED"
        elif analysis['confident']:
            current_cat = analysis['recommended']
            is_green = True 
            auto_msg = f"AUTO: {analysis['recommended'].upper()}"
        else:
            current_cat = "string" 
            is_green = False 
            auto_msg = f"SUGGESTED: {analysis['recommended'].upper()}"
            
        # Stats
        dom_pct = get_dominance_stats(series)
        null_pct = (series.isna().sum() / len(series)) * 100
        unique_count = series.nunique()
        
        # Header Styling
        if current_cat == "IGNORE":
            header_class = "ignore-header"
            icon = "🚫"
        elif is_green:
            header_class = "green-header"
            icon = "✅"
        else:
            header_class = "red-header"
            icon = "⚠️"
        
        # UI Container
        with st.container(border=True):
            # Header with tooltip if description exists
            col_desc = file_descriptions.get(col, "")
            tooltip_html = f' <span title="{col_desc}" style="cursor:help;">ℹ️</span>' if col_desc else ''
            
            st.markdown(f"""
                <div class="{header_class}">
                    <b>{icon} {col}{tooltip_html}</b> <span style="float:right; opacity:0.7; font-size:0.9em">{auto_msg}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Revised Columns Ratio: Smaller stats, Wider samples
            c1, c2, c3 = st.columns([0.8, 3.5, 1.2])
            
            # Col 1: Stats
            with c1:
                st.text(f"Unique: {unique_count}")
                
                # Missing (Red if > 50%)
                miss_style = "color:red; font-weight:bold" if null_pct > 50 else ""
                st.markdown(f"Missing: <span style='{miss_style}'>{null_pct:.1f}%</span>", unsafe_allow_html=True)
                
                # Dominance (Red if > 90%)
                dom_style = "color:red; font-weight:bold" if dom_pct > 0.9 else ""
                st.markdown(f"Dominance: <span style='{dom_style}'>{dom_pct*100:.1f}%</span>", unsafe_allow_html=True)
            
            # Col 2: Samples (Evenly Spaced Grid)
            with c2:
                # 1. Clean Data
                clean_samp = series.dropna().astype(str)
                clean_samp = clean_samp[clean_samp.str.strip().str.len() > 0]
                
                # 2. Evenly Spaced Sampling
                num_samples = 50
                if len(clean_samp) > num_samples:
                    indices = [int(i * (len(clean_samp) - 1) / (num_samples - 1)) for i in range(num_samples)]
                    head_samp = clean_samp.iloc[indices].tolist()
                else:
                    head_samp = clean_samp.tolist()
                
                # 3. Format: Grid of 4 columns (Widened for readability)
                chunk_size = 4
                lines = []
                for i in range(0, len(head_samp), chunk_size):
                    chunk = head_samp[i:i + chunk_size]
                    # Increase width to 22 chars per column for spacing
                    row = [f"{val[:20]:<22}" for val in chunk] 
                    lines.append("".join(row))
                
                formatted_code = "\n".join(lines)
                st.code(formatted_code, language=None)
                
                if not is_saved:
                    st.caption(f"Reason: {analysis['reason']}")

            # Col 3: Action
            with c3:
                def format_option(option):
                    score = stats.get(option, 0)
                    if option == "IGNORE": return "IGNORE"
                    return f"{option} ({score*100:.0f}%)"

                new_cat = st.radio(
                    "Type",
                    CATEGORIES,
                    key=f"rad_{col}",
                    index=CATEGORIES.index(current_cat) if current_cat in CATEGORIES else 3,
                    label_visibility="collapsed",
                    format_func=format_option 
                )
                
                if new_cat != saved_val:
                    save_single_category(selected_file, col, new_cat)
                    if not is_saved:
                        st.rerun()
                    else:
                        st.toast(f"Updated {col} -> {new_cat}")

    st.markdown("---")

if __name__ == "__main__":
    main()