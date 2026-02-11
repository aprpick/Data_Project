import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent.parent
WORKING_DATA = PROJECT_ROOT / "Working_data"
SAMPLE_DATA = WORKING_DATA / "Sample_Data"
CATEGORIES_FILE = WORKING_DATA / "02_Data_Categories.json"
CLEANING_FILE = WORKING_DATA / "04_Data_Cleaning_actions.json"
DESCRIPTIONS_FILE = WORKING_DATA / "00_column_descriptions.json"

# --- STORAGE FUNCTIONS ---
def load_categories():
    if CATEGORIES_FILE.exists():
        try:
            with open(CATEGORIES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def load_cleaning_actions():
    if CLEANING_FILE.exists():
        try:
            with open(CLEANING_FILE, 'r') as f:
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

def save_cleaning_actions(actions):
    with open(CLEANING_FILE, 'w') as f:
        json.dump(actions, f, indent=2)

# --- ANALYSIS FUNCTIONS ---
def analyze_int_column(series, outlier_threshold=3.0):
    """Analyze integer column for issues"""
    issues = {
        'parsing_errors': [],
        'outliers': [],
        'negatives': [],
        'missing': []
    }
    
    # Get clean numeric values
    clean_str = series.astype(str).str.replace(r'[$,\s]', '', regex=True)
    numeric = pd.to_numeric(clean_str, errors='coerce')
    
    # Parsing errors
    parsing_errors_mask = numeric.isna() & series.notna()
    if parsing_errors_mask.any():
        issues['parsing_errors'] = series[parsing_errors_mask].index.tolist()
    
    # Missing values
    missing_mask = series.isna()
    if missing_mask.any():
        issues['missing'] = series[missing_mask].index.tolist()
    
    # Outliers and negatives (only on valid numeric)
    valid_numeric = numeric.dropna()
    if len(valid_numeric) > 0:
        mean = valid_numeric.mean()
        std = valid_numeric.std()
        
        if std > 0:
            lower = mean - outlier_threshold * std
            upper = mean + outlier_threshold * std
            outliers_mask = (numeric > upper) | (numeric < lower)
            if outliers_mask.any():
                issues['outliers'] = numeric[outliers_mask].index.tolist()
        
        # Negatives
        negatives_mask = numeric < 0
        if negatives_mask.any():
            issues['negatives'] = numeric[negatives_mask].index.tolist()
    
    return issues, numeric

def analyze_date_column(series, min_date=None, max_date=None):
    """Analyze date column for issues"""
    issues = {
        'parsing_errors': [],
        'outliers': [],
        'missing': []
    }
    
    date_series = pd.to_datetime(series, errors='coerce')
    
    # Parsing errors
    parsing_errors_mask = date_series.isna() & series.notna()
    if parsing_errors_mask.any():
        issues['parsing_errors'] = series[parsing_errors_mask].index.tolist()
    
    # Missing values
    missing_mask = series.isna()
    if missing_mask.any():
        issues['missing'] = series[missing_mask].index.tolist()
    
    # Outliers (if range specified)
    if min_date is not None and max_date is not None:
        outliers_mask = (date_series < min_date) | (date_series > max_date)
        if outliers_mask.any():
            issues['outliers'] = date_series[outliers_mask].index.tolist()
    
    return issues, date_series

def create_scatter_plot(numeric_series, issues, is_date=False):
    """Create scatter plot with color coding"""
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')
    
    # Use SEQUENTIAL indices for x-axis (0, 1, 2, ...)
    x_positions = list(range(len(numeric_series)))
    values = numeric_series.values
    
    # Create mapping from original indices to sequential positions
    original_to_sequential = {orig_idx: seq_idx for seq_idx, orig_idx in enumerate(numeric_series.index)}
    
    # Default: all green (normal)
    colors = ['green'] * len(values)
    
    # Map original indices to sequential positions for coloring
    # Priority order matters - later colors override earlier ones
    
    for orig_idx in issues.get('missing', []):
        if orig_idx in original_to_sequential:
            seq_idx = original_to_sequential[orig_idx]
            colors[seq_idx] = 'cyan'
    
    for orig_idx in issues.get('parsing_errors', []):
        if orig_idx in original_to_sequential:
            seq_idx = original_to_sequential[orig_idx]
            colors[seq_idx] = 'purple'
    
    for orig_idx in issues.get('outliers', []):
        if orig_idx in original_to_sequential:
            seq_idx = original_to_sequential[orig_idx]
            colors[seq_idx] = 'yellow'
    
    for orig_idx in issues.get('negatives', []):
        if orig_idx in original_to_sequential:
            seq_idx = original_to_sequential[orig_idx]
            colors[seq_idx] = 'red'
    
    # Plot with sequential x positions
    ax.scatter(x_positions, values, c=colors, alpha=0.6, s=20)
    ax.set_xlabel('Index', color='white')
    ax.set_ylabel('Value', color='white')
    ax.grid(True, alpha=0.2, color='gray')
    ax.tick_params(colors='white')
    
    # Format Y-axis as dates if needed
    if is_date:
        from matplotlib.dates import DateFormatter
        import matplotlib.dates as mdates
        # Convert numeric back to dates for Y-axis labels
        ax.yaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
        ax.yaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()  # Rotate date labels
    
    # Legend horizontal below the plot
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', label='Normal'),
        Patch(facecolor='red', label='Negative'),
        Patch(facecolor='yellow', label='Outlier'),
        Patch(facecolor='purple', label='Parse error (filled)'),
        Patch(facecolor='cyan', label='Missing (filled)')
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.12),
             fancybox=False, shadow=False, ncol=5, facecolor='#0E1117', edgecolor='white')
    
    # Adjust layout to make room for legend
    plt.tight_layout()
    
    return fig

def apply_preview_actions(series, numeric_series, actions, outlier_threshold=3):
    """Apply actions and return preview of results"""
    preview_series = numeric_series.copy()
    
    # Parse errors
    if actions.get('parsing_errors') == 'strip':
        pass  # Already converted
    elif actions.get('parsing_errors') == 'remove':
        preview_series = preview_series[preview_series.notna()]
    elif actions.get('parsing_errors') == 'mean':
        # Calculate mean from VALID values only (exclude NaN parse errors)
        valid_values = preview_series.dropna()
        if len(valid_values) > 0:
            mean_val = valid_values.mean()
            preview_series = preview_series.fillna(mean_val)
    elif actions.get('parsing_errors') == 'median':
        # Calculate median from VALID values only (exclude NaN parse errors)
        valid_values = preview_series.dropna()
        if len(valid_values) > 0:
            median_val = valid_values.median()
            preview_series = preview_series.fillna(median_val)
    
    # Outliers
    if len(preview_series) > 0:
        mean = preview_series.mean()
        std = preview_series.std()
        
        if std > 0:
            lower = mean - outlier_threshold * std
            upper = mean + outlier_threshold * std
            outlier_mask = (preview_series > upper) | (preview_series < lower)
            
            if actions.get('outliers') == 'remove':
                preview_series = preview_series[~outlier_mask]
            elif actions.get('outliers') == 'mean':
                preview_series[outlier_mask] = mean
            elif actions.get('outliers') == 'median':
                preview_series[outlier_mask] = preview_series.median()
            elif actions.get('outliers') == 'cap':
                preview_series = preview_series.clip(lower=lower, upper=upper)
    
    # Negatives
    if actions.get('negatives') == 'remove':
        neg_mask = preview_series < 0
        preview_series = preview_series[~neg_mask]
    elif actions.get('negatives') == 'absolute':
        preview_series = preview_series.abs()
    elif actions.get('negatives') == 'mean':
        neg_mask = preview_series < 0
        if neg_mask.any():
            preview_series[neg_mask] = preview_series.mean()
    elif actions.get('negatives') == 'median':
        neg_mask = preview_series < 0
        if neg_mask.any():
            preview_series[neg_mask] = preview_series.median()
    
    # Missing
    if actions.get('missing') == 'remove':
        preview_series = preview_series.dropna()
    elif actions.get('missing') == 'mean':
        preview_series = preview_series.fillna(preview_series.mean())
    elif actions.get('missing') == 'median':
        preview_series = preview_series.fillna(preview_series.median())
    
    return preview_series

def apply_preview_actions_date(series, date_series, actions, min_date=None, max_date=None):
    """Apply actions to date column and return preview"""
    preview_series = date_series.copy()
    
    # Parse errors
    if actions.get('parsing_errors') == 'remove':
        preview_series = preview_series[preview_series.notna()]
    elif actions.get('parsing_errors') == 'interpolate':
        preview_series = preview_series.interpolate(method='linear')
    
    # Outliers
    if min_date is not None and max_date is not None:
        outlier_mask = (preview_series < min_date) | (preview_series > max_date)
        
        if actions.get('outliers') == 'remove':
            preview_series = preview_series[~outlier_mask]
        elif actions.get('outliers') == 'interpolate':
            preview_series[outlier_mask] = pd.NaT
            preview_series = preview_series.interpolate(method='linear')
    
    # Missing
    if actions.get('missing') == 'remove':
        preview_series = preview_series.dropna()
    elif actions.get('missing') == 'interpolate':
        preview_series = preview_series.interpolate(method='linear')
    
    return preview_series

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Data Cleaning Configurator", layout="wide")
    
    # Increase font sizes
    st.markdown("""
        <style>
        .stMarkdown, .stText, .stRadio label, .stSlider label {
            font-size: 16px !important;
        }
        .stExpander summary {
            font-size: 16px !important;
        }
        h1 { font-size: 42px !important; }
        h2 { font-size: 32px !important; }
        h3 { font-size: 24px !important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🧹 Data Cleaning Configurator")
    st.markdown("Configure cleaning actions. No changes applied until you run apply_cleaning.py")
    
    # Load data
    categories = load_categories()
    cleaning_actions = load_cleaning_actions()
    descriptions = load_descriptions()
    
    if not categories:
        st.error("❌ No column categories found. Run Data_Profiler.py first!")
        return
    
    # File selector
    csv_files = sorted(list(SAMPLE_DATA.glob("sample_*.csv")))
    file_names = [f.name for f in csv_files]
    
    selected_file = st.selectbox("Select File", file_names)
    
    if not selected_file:
        return
    
    # Load CSV
    df = pd.read_csv(SAMPLE_DATA / selected_file)
    
    # Get descriptions for this file
    file_descriptions = descriptions.get(selected_file, {})
    
    # Initialize cleaning actions for this file
    if selected_file not in cleaning_actions:
        cleaning_actions[selected_file] = {}
    
    # Get categorized columns
    file_categories = categories.get(selected_file, {})
    
    st.markdown("---")
    
    # Process int, float, date, and IGNORE columns
    for col_name in df.columns:
        category = file_categories.get(col_name, "Not Categorized")
        
        if category not in ['int', 'float', 'date', 'IGNORE']:
            continue
        
        # Display IGNORE columns differently
        if category == 'IGNORE':
            st.markdown(f"### 🗑️ {col_name} (IGNORE)")
            col_desc = file_descriptions.get(col_name, "")
            if col_desc:
                st.caption(f"ℹ️ {col_desc}")
            
            # Grey container
            st.markdown("""
                <div style="background-color: #2b2b2b; padding: 10px; border-radius: 5px; border-left: 4px solid #666;">
                    <span style="color: #999;">This column is being ignored</span>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
            continue
        
        # Display column header with description tooltip if available
        col_desc = file_descriptions.get(col_name, "")
        if col_desc:
            st.subheader(f"📊 {col_name} ({category})")
            st.caption(f"ℹ️ {col_desc}")
        else:
            st.subheader(f"📊 {col_name} ({category})")
        
        # Initialize actions for this column
        if col_name not in cleaning_actions[selected_file]:
            if category == 'date':
                cleaning_actions[selected_file][col_name] = {
                    'category': category,
                    'parsing_errors': 'keep',
                    'outliers': 'keep',
                    'missing': 'keep',
                    'min_date': None,
                    'max_date': None
                }
            else:  # int or float
                cleaning_actions[selected_file][col_name] = {
                    'category': category,
                    'parsing_errors': 'keep',
                    'outliers': 'keep',
                    'negatives': 'keep',
                    'missing': 'keep',
                    'outlier_threshold': 3.0
                }
        
        col_actions = cleaning_actions[selected_file][col_name]
        
        # Analyze based on type
        if category == 'date':
            # Parse dates to get default range
            temp_dates = pd.to_datetime(df[col_name], errors='coerce')
            valid_dates = temp_dates.dropna()
            
            # Set default min/max if not set
            if col_actions['min_date'] is None and len(valid_dates) > 0:
                col_actions['min_date'] = valid_dates.min().strftime('%Y-%m-%d')
            if col_actions['max_date'] is None and len(valid_dates) > 0:
                col_actions['max_date'] = valid_dates.max().strftime('%Y-%m-%d')
            
            # Analyze with date range
            min_dt = pd.Timestamp(col_actions['min_date']) if col_actions['min_date'] else None
            max_dt = pd.Timestamp(col_actions['max_date']) if col_actions['max_date'] else None
            issues, date_series = analyze_date_column(df[col_name], min_dt, max_dt)
        else:
            # Analyze numeric
            issues, numeric_series = analyze_int_column(df[col_name], col_actions['outlier_threshold'])
        
        # Count issues
        total_issues = sum(len(v) for v in issues.values())
        
        # For dates, always show controls (to adjust range)
        # For numeric, skip if no issues
        if total_issues == 0 and category != 'date':
            st.success("✅ No issues found")
            st.markdown("---")
            continue
        
        # Layout: Plot on LEFT, Actions on RIGHT
        plot_col, action_col = st.columns([2, 1])
        
        with action_col:
            st.markdown("**Actions:**")
            
            if category == 'date':
                # === DATE COLUMN HANDLING ===
                # Parsing errors
                if len(issues['parsing_errors']) > 0:
                    st.markdown(f"🔴 **Parse Errors:** {len(issues['parsing_errors'])} rows")
                    with st.expander("👁️ View problem samples"):
                        samples = df.loc[issues['parsing_errors'][:10], col_name]
                        for idx, val in samples.items():
                            st.text(f"{val} (row {idx})")
                    parse_action = st.radio(
                        "Action:",
                        ['keep', 'remove', 'interpolate'],
                        index=['keep', 'remove', 'interpolate'].index(col_actions['parsing_errors']),
                        key=f"{col_name}_parse",
                        format_func=lambda x: {'keep': 'Keep as-is', 'remove': 'Remove rows', 'interpolate': 'Interpolate'}[x]
                    )
                    col_actions['parsing_errors'] = parse_action
                    st.markdown("---")
                
                # Date range
                st.markdown("🟡 **Date Range**")
                min_date_input = st.date_input(
                    "Min Date",
                    value=pd.to_datetime(col_actions['min_date']) if col_actions['min_date'] else None,
                    key=f"{col_name}_min_date"
                )
                max_date_input = st.date_input(
                    "Max Date",
                    value=pd.to_datetime(col_actions['max_date']) if col_actions['max_date'] else None,
                    key=f"{col_name}_max_date"
                )
                
                new_min = min_date_input.strftime('%Y-%m-%d')
                new_max = max_date_input.strftime('%Y-%m-%d')
                
                if new_min != col_actions['min_date'] or new_max != col_actions['max_date']:
                    col_actions['min_date'] = new_min
                    col_actions['max_date'] = new_max
                    issues, date_series = analyze_date_column(df[col_name], pd.Timestamp(new_min), pd.Timestamp(new_max))
                
                if len(issues['outliers']) > 0:
                    st.caption(f"{len(issues['outliers'])} dates outside range")
                    outlier_action = st.radio(
                        "Action:",
                        ['keep', 'remove', 'interpolate'],
                        index=['keep', 'remove', 'interpolate'].index(col_actions['outliers']),
                        key=f"{col_name}_outlier",
                        format_func=lambda x: {'keep': 'Keep as-is', 'remove': 'Remove rows', 'interpolate': 'Interpolate'}[x]
                    )
                    col_actions['outliers'] = outlier_action
                st.markdown("---")
                
                # Missing
                if len(issues['missing']) > 0:
                    st.markdown(f"⚪ **Missing:** {len(issues['missing'])} rows")
                    miss_action = st.radio(
                        "Action:",
                        ['keep', 'remove', 'interpolate'],
                        index=['keep', 'remove', 'interpolate'].index(col_actions['missing']),
                        key=f"{col_name}_miss",
                        format_func=lambda x: {'keep': 'Keep as NaT', 'remove': 'Remove rows', 'interpolate': 'Interpolate'}[x]
                    )
                    col_actions['missing'] = miss_action
            
            else:
                # === NUMERIC COLUMN HANDLING ===
                # Parsing errors
                if len(issues['parsing_errors']) > 0:
                    st.markdown(f"🔴 **Parse Errors:** {len(issues['parsing_errors'])} rows")
                    with st.expander("👁️ View problem samples"):
                        samples = df.loc[issues['parsing_errors'][:10], col_name]
                        for idx, val in samples.items():
                            st.text(f"{val} (row {idx})")
                    parse_action = st.radio(
                        "Action:",
                        ['keep', 'strip', 'remove', 'mean', 'median'],
                        index=['keep', 'strip', 'remove', 'mean', 'median'].index(col_actions['parsing_errors']),
                        key=f"{col_name}_parse",
                        format_func=lambda x: {'keep': 'Keep as-is', 'strip': 'Strip non-numeric', 'remove': 'Remove rows', 'mean': 'Fill with mean', 'median': 'Fill with median'}[x]
                    )
                    col_actions['parsing_errors'] = parse_action
                    st.markdown("---")
                
                # Sample of normal rows
                normal_indices = [i for i in range(len(df[col_name])) 
                                if i not in issues['parsing_errors'] 
                                and i not in issues['outliers']
                                and i not in issues['negatives']
                                and i not in issues['missing']]
                if len(normal_indices) > 0:
                    with st.expander("👁️ View normal value samples"):
                        sample_normal = df[col_name].iloc[normal_indices[:10]]
                        for idx, val in sample_normal.items():
                            st.text(f"{val} (row {idx})")
                    st.markdown("---")
                
                # Outliers
                if len(issues['outliers']) > 0:
                    st.markdown(f"🟡 **Outliers**")
                    threshold = st.slider(f"Threshold", 1.0, 5.0, col_actions['outlier_threshold'], key=f"{col_name}_thresh", step=0.1)
                    mean = numeric_series.mean()
                    std = numeric_series.std()
                    if std > 0:
                        lower = mean - threshold * std
                        upper = mean + threshold * std
                        current_outlier_count = ((numeric_series > upper) | (numeric_series < lower)).sum()
                    else:
                        current_outlier_count = 0
                    st.caption(f"{current_outlier_count} outliers at {threshold:.1f}σ")
                    if threshold != col_actions['outlier_threshold']:
                        col_actions['outlier_threshold'] = threshold
                        issues, numeric_series = analyze_int_column(df[col_name], threshold)
                    outlier_action = st.radio(
                        "Action:",
                        ['keep', 'remove', 'mean', 'median', 'cap'],
                        index=['keep', 'remove', 'mean', 'median', 'cap'].index(col_actions['outliers']),
                        key=f"{col_name}_outlier",
                        format_func=lambda x: {'keep': 'Keep as-is', 'remove': 'Remove rows', 'mean': 'Replace with mean', 'median': 'Replace with median', 'cap': f'Cap at {threshold}σ'}[x]
                    )
                    col_actions['outliers'] = outlier_action
                    st.markdown("---")
                
                # Negatives
                if len(issues['negatives']) > 0:
                    st.markdown(f"🔴 **Negatives:** {len(issues['negatives'])} rows")
                    neg_action = st.radio(
                        "Action:",
                        ['keep', 'remove', 'absolute', 'mean', 'median'],
                        index=['keep', 'remove', 'absolute', 'mean', 'median'].index(col_actions['negatives']),
                        key=f"{col_name}_neg",
                        format_func=lambda x: {'keep': 'Keep as-is', 'remove': 'Remove rows', 'absolute': 'Convert to absolute', 'mean': 'Replace with mean', 'median': 'Replace with median'}[x]
                    )
                    col_actions['negatives'] = neg_action
                    st.markdown("---")
                
                # Missing
                if len(issues['missing']) > 0:
                    st.markdown(f"⚪ **Missing:** {len(issues['missing'])} rows")
                    miss_action = st.radio(
                        "Action:",
                        ['keep', 'remove', 'mean', 'median'],
                        index=['keep', 'remove', 'mean', 'median'].index(col_actions['missing']),
                        key=f"{col_name}_miss",
                        format_func=lambda x: {'keep': 'Keep as NaN', 'remove': 'Remove rows', 'mean': 'Fill with mean', 'median': 'Fill with median'}[x]
                    )
                    col_actions['missing'] = miss_action
        
        with plot_col:
            if category == 'date':
                # Date preview
                min_dt = pd.Timestamp(col_actions['min_date']) if col_actions['min_date'] else None
                max_dt = pd.Timestamp(col_actions['max_date']) if col_actions['max_date'] else None
                
                preview_series = apply_preview_actions_date(df[col_name], date_series, col_actions, min_dt, max_dt)
                
                # Convert to numeric for plotting
                numeric_dates = preview_series.astype('int64') / 10**9 / 86400
                
                preview_issues = {
                    'parsing_errors': [],
                    'outliers': issues['outliers'],
                    'negatives': [],
                    'missing': []
                }
                
                if col_actions['parsing_errors'] == 'interpolate':
                    preview_issues['parsing_errors'] = issues['parsing_errors']
                if col_actions['missing'] == 'interpolate':
                    preview_issues['missing'] = issues['missing']
                
                fig = create_scatter_plot(numeric_dates, preview_issues, is_date=True)
                st.pyplot(fig)
                plt.close(fig)
            else:
                # Numeric preview
                preview_series = apply_preview_actions(
                    df[col_name], 
                    numeric_series, 
                    col_actions,
                    col_actions['outlier_threshold']
                )
                
                preview_issues = {
                    'parsing_errors': [],
                    'outliers': issues['outliers'],
                    'negatives': issues['negatives'],
                    'missing': []
                }
                
                if col_actions['parsing_errors'] in ['mean', 'median']:
                    preview_issues['parsing_errors'] = issues['parsing_errors']
                
                if col_actions['missing'] in ['mean', 'median']:
                    preview_issues['missing'] = issues['missing']
                
                fig = create_scatter_plot(preview_series, preview_issues)
                st.pyplot(fig)
                plt.close(fig)
        
        st.markdown("---")
    
    # Save button
    if st.button("💾 Save Cleaning Plan", type="primary"):
        save_cleaning_actions(cleaning_actions)
        st.success(f"✅ Cleaning plan saved to {CLEANING_FILE}")
        st.info("Run `python apply_cleaning.py` to apply these changes")

if __name__ == "__main__":
    main()