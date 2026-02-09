from pathlib import Path
import pandas as pd
import streamlit as st
import json

#"streamlit run Working_data\column_categorizer.py" - To run this script

# Get project root (parent of Cleaning_Scripts folder where this script lives)
PROJECT_ROOT = Path(__file__).parent.parent

# Define folder paths
RAW_DATA = PROJECT_ROOT / "Raw_Data"
WORKING_DATA = PROJECT_ROOT / "Working_data"
CONFIG_FILE = WORKING_DATA / "column_categories.json"

# Predefined category options
CATEGORIES = [
    "Not Categorized",
    "ID/Identifier",
    "Date/Datetime",
    "Address",
    "ZIP Code",
    "City",
    "State",
    "Numeric - Currency",
    "Numeric - Measurement",
    "Numeric - Count",
    "Numeric - Percentage",
    "Categorical - Nominal",
    "Categorical - Ordinal",
    "Boolean/Binary",
    "Text - Free Form",
    "Phone Number",
    "Email",
    "IGNORE - Do Not Use",
    "Other"
]

def load_categories():
    """Load saved categories from JSON file"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_categories(categories):
    """Save categories to JSON file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(categories, f, indent=2)

def get_evenly_spaced_samples(series, num_samples=10):
    """Get evenly-spaced samples across the entire dataset"""
    non_null = series.dropna()
    if len(non_null) == 0:
        return []
    
    # Calculate evenly-spaced indices
    actual_samples = min(num_samples, len(non_null))
    if actual_samples == len(non_null):
        indices = range(len(non_null))
    else:
        step = len(non_null) / actual_samples
        indices = [int(i * step) for i in range(actual_samples)]
    
    return non_null.iloc[indices].tolist()

def is_column_uniform(series, uniformity_threshold=0.95, min_fill_rate=0.10):
    """
    Check if column has all/mostly identical values or too few non-null values
    
    Args:
        uniformity_threshold: If 95%+ of non-null values are the same, flag as uniform
        min_fill_rate: If less than 10% of rows have data, flag as uniform
    
    Returns:
        (is_uniform: bool, reason: str)
    """
    total_rows = len(series)
    non_null_count = series.notna().sum()
    
    # Check if all values are null
    if non_null_count == 0:
        return True, "All NULL"
    
    # Calculate fill rate
    fill_rate = non_null_count / total_rows
    
    # Flag if fill rate is too low (e.g., 2 values in 1000 rows = 0.2% fill rate)
    if fill_rate < min_fill_rate:
        return True, f"Too Sparse: only {non_null_count}/{total_rows} rows ({fill_rate*100:.1f}% filled)"
    
    # Get non-null values
    non_null = series.dropna()
    
    # For object/string columns, check for empty strings
    if series.dtype == 'object':
        # Check if all are empty strings
        if non_null.astype(str).str.strip().eq('').all():
            return True, "All Empty Strings"
    
    # Check uniformity of non-null values
    value_counts = non_null.value_counts()
    most_common_count = value_counts.iloc[0]
    most_common_freq = most_common_count / len(non_null)
    
    # Flag if most common value appears in 95%+ of non-null rows
    if most_common_freq >= uniformity_threshold:
        most_common_val = value_counts.index[0]
        # Truncate long values for display
        value_str = str(most_common_val)
        if len(value_str) > 30:
            value_str = value_str[:30] + "..."
        
        if most_common_freq == 1.0:
            return True, f"All Same: '{value_str}'"
        else:
            return True, f"{most_common_freq*100:.1f}% same: '{value_str}' ({most_common_count}/{len(non_null)} rows)"
    
    return False, None

def main():
    st.set_page_config(page_title="Column Categorizer", layout="wide")
    
    st.title("📊 Data Column Categorizer")
    st.markdown("---")
    
    # Load saved categories
    saved_categories = load_categories()
    
    # Get all sample CSV files from Working_data
    csv_files = list(WORKING_DATA.glob("sample_*.csv"))
    
    if not csv_files:
        st.error("❌ No sample CSV files found in Working_data folder")
        st.info("Run sample_data.py first to create sample files!")
        return
    
    # File selector
    st.sidebar.header("📁 Select File")
    selected_file = st.sidebar.selectbox(
        "Choose a CSV file:",
        csv_files,
        format_func=lambda x: x.name
    )
    
    # Load the selected file
    df = pd.read_csv(selected_file)
    
    st.sidebar.markdown("---")
    st.sidebar.metric("Total Rows", len(df))
    st.sidebar.metric("Total Columns", len(df.columns))
    
    # Initialize session state for this file if not exists
    file_key = selected_file.name
    if file_key not in saved_categories:
        saved_categories[file_key] = {}
    
    # Count uniform columns (all same value) for current file
    uniform_results = {col: is_column_uniform(df[col]) for col in df.columns}
    uniform_cols = sum(1 for is_uniform, _ in uniform_results.values() if is_uniform)
    if uniform_cols > 0:
        st.sidebar.warning(f"⚠️ {uniform_cols} uniform column(s) in this file")
    
    # Count uncategorized columns across ALL files
    total_uncategorized = 0
    for csv_file in csv_files:
        temp_df = pd.read_csv(csv_file)
        temp_file_key = csv_file.name
        if temp_file_key in saved_categories:
            for col in temp_df.columns:
                if saved_categories[temp_file_key].get(col, "Not Categorized") == "Not Categorized":
                    total_uncategorized += 1
        else:
            # File not in saved_categories means all columns uncategorized
            total_uncategorized += len(temp_df.columns)
    
    if total_uncategorized > 0:
        st.sidebar.error(f"❌ {total_uncategorized} column(s) across all files need categorization!")
    else:
        st.sidebar.success(f"✅ All columns categorized across all files!")
    
    # Main content area
    st.header(f"📄 {selected_file.name}")
    
    # Progress indicator (excluding IGNORE columns)
    categorized_count = sum(
        1 for key, cat in saved_categories[file_key].items() 
        if not key.startswith("notes_") and cat not in ["Not Categorized", "IGNORE - Do Not Use"]
    )
    ignored_count = sum(
        1 for key, cat in saved_categories[file_key].items() 
        if not key.startswith("notes_") and cat == "IGNORE - Do Not Use"
    )
    total_columns = len(df.columns)
    progress = categorized_count / total_columns if total_columns > 0 else 0
    
    st.progress(progress)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Categorized", f"{categorized_count}/{total_columns}")
    with col_b:
        st.metric("Ignored", ignored_count)
    with col_c:
        st.metric("Progress", f"{progress*100:.1f}%")
    
    st.markdown("---")
    
    # Column categorization interface
    for col_name in df.columns:
        # Check if column is uniform (all same value)
        is_uniform, uniform_reason = is_column_uniform(df[col_name])
        
        # Add visual indicator for uniform columns
        expander_label = f"🔍 **{col_name}**"
        if is_uniform:
            expander_label = f"⚠️ **{col_name}** (UNIFORM: {uniform_reason})"
        
        with st.expander(expander_label, expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show uniform column warning
                if is_uniform:
                    st.error(f"⚠️ This column has all identical values: {uniform_reason}")
                    st.info("💡 Consider marking as 'IGNORE - Do Not Use'")
                
                # Show sample data - evenly spaced across the dataset
                st.markdown("**Sample Values (evenly spaced):**")
                sample_values = get_evenly_spaced_samples(df[col_name], num_samples=10)
                
                if len(sample_values) > 0:
                    for i, val in enumerate(sample_values, 1):
                        st.text(f"{i}. {val}")
                else:
                    st.text("No non-null values found")
                
                # Show data type info
                st.markdown("**Data Info:**")
                st.text(f"Pandas dtype: {df[col_name].dtype}")
                st.text(f"Unique values: {df[col_name].nunique()}")
                st.text(f"Missing values: {df[col_name].isna().sum()}")
                st.text(f"Non-null values: {df[col_name].notna().sum()}")
                st.text(f"Total rows: {len(df[col_name])}")
                
                # Calculate fill rate
                fill_rate = (df[col_name].notna().sum() / len(df[col_name])) * 100
                st.text(f"Fill rate: {fill_rate:.1f}%")
            
            with col2:
                # Category selector
                current_category = saved_categories[file_key].get(col_name, "Not Categorized")
                
                # Auto-suggest IGNORE for uniform columns
                if is_uniform and current_category == "Not Categorized":
                    current_category = "IGNORE - Do Not Use"
                
                selected_category = st.selectbox(
                    "Category:",
                    CATEGORIES,
                    index=CATEGORIES.index(current_category),
                    key=f"cat_{file_key}_{col_name}"
                )
                
                # Save the selection
                saved_categories[file_key][col_name] = selected_category
                
                # Show warning if ignoring non-uniform column
                if selected_category == "IGNORE - Do Not Use" and not is_uniform:
                    st.warning("⚠️ You're ignoring a column with varying data")
                
                # Notes field
                notes_key = f"notes_{col_name}"
                if notes_key not in saved_categories[file_key]:
                    saved_categories[file_key][notes_key] = ""
                
                notes = st.text_area(
                    "Notes:",
                    value=saved_categories[file_key].get(notes_key, ""),
                    key=f"notes_{file_key}_{col_name}",
                    height=100
                )
                
                saved_categories[file_key][notes_key] = notes
    
    # Save button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("💾 Save Categories", type="primary", use_container_width=True):
            save_categories(saved_categories)
            st.success("✅ Categories saved!")

    with col2:
        if st.button("📥 Export Summary", use_container_width=True):
            export_summary(saved_categories, file_key, df)
    
    with col3:
        if st.button("🚫 Auto-Ignore Uniform", use_container_width=True):
            # Auto-set all uniform columns to IGNORE
            uniform_count = 0
            for col_name in df.columns:
                is_uniform, uniform_reason = uniform_results[col_name]
                if is_uniform:
                    # Only auto-ignore if not already categorized
                    current_cat = saved_categories[file_key].get(col_name, "Not Categorized")
                    if current_cat == "Not Categorized":
                        saved_categories[file_key][col_name] = "IGNORE - Do Not Use"
                        # Add auto-generated note
                        notes_key = f"notes_{col_name}"
                        saved_categories[file_key][notes_key] = f"Auto-ignored: {uniform_reason}"
                        uniform_count += 1
            
            save_categories(saved_categories)
            st.success(f"✅ Auto-ignored {uniform_count} uniform column(s)!")
            st.rerun()
    
    # Show summary table
    st.markdown("---")
    st.subheader("📋 Current Categorization Summary")
    
    # Filter options
    show_filter = st.radio(
        "Show columns:",
        ["All", "Categorized only", "Not categorized", "Ignored only"],
        horizontal=True
    )
    
    summary_data = []
    for col_name in df.columns:
        category = saved_categories[file_key].get(col_name, "Not Categorized")
        notes_key = f"notes_{col_name}"
        notes = saved_categories[file_key].get(notes_key, "")
        is_uniform, uniform_reason = is_column_uniform(df[col_name])
        fill_rate = (df[col_name].notna().sum() / len(df[col_name])) * 100
        
        # Apply filter
        if show_filter == "Categorized only" and category in ["Not Categorized", "IGNORE - Do Not Use"]:
            continue
        elif show_filter == "Not categorized" and category != "Not Categorized":
            continue
        elif show_filter == "Ignored only" and category != "IGNORE - Do Not Use":
            continue
        
        summary_data.append({
            "Column": col_name,
            "Category": category,
            "Dtype": str(df[col_name].dtype),
            "Unique": df[col_name].nunique(),
            "Fill Rate": f"{fill_rate:.1f}%",
            "Uniform": uniform_reason if is_uniform else "",
            "Notes": notes[:50] + "..." if len(notes) > 50 else notes
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)
    
    # Show statistics
    st.markdown("---")
    st.subheader("📈 Statistics")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.metric("Total Columns", len(df.columns))
    with stat_col2:
        st.metric("Categorized", categorized_count)
    with stat_col3:
        st.metric("Ignored", ignored_count)
    with stat_col4:
        st.metric("Uniform Columns", uniform_cols)

def export_summary(categories, file_key, df):
    """Export categorization summary to CSV"""
    summary_data = []
    
    for col_name in df.columns:
        category = categories[file_key].get(col_name, "Not Categorized")
        notes_key = f"notes_{col_name}"
        notes = categories[file_key].get(notes_key, "")
        is_uniform, uniform_reason = is_column_uniform(df[col_name])
        fill_rate = (df[col_name].notna().sum() / len(df[col_name])) * 100
        
        summary_data.append({
            "file": file_key,
            "column": col_name,
            "category": category,
            "dtype": str(df[col_name].dtype),
            "unique_values": df[col_name].nunique(),
            "missing_values": df[col_name].isna().sum(),
            "fill_rate_percent": f"{fill_rate:.1f}",
            "is_uniform": is_uniform,
            "uniform_reason": uniform_reason if is_uniform else "",
            "total_rows": len(df[col_name]),
            "notes": notes
        })
    
    summary_df = pd.DataFrame(summary_data)
    output_file = WORKING_DATA / f"categorization_summary_{file_key.replace('.csv', '')}.csv"
    summary_df.to_csv(output_file, index=False)
    
    st.success(f"✅ Summary exported to: {output_file.name}")

if __name__ == "__main__":
    main()