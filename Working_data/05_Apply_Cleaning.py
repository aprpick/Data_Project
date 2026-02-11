import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import sys

# --- CONFIGURATION ---
PROJECT_ROOT = Path(__file__).parent.parent  # Script is in Working_data, parent is project root
RAW_DATA = PROJECT_ROOT / "Raw_Data"
CLEANED_DATA = PROJECT_ROOT / "Cleaned_Data"
WORKING_DATA = PROJECT_ROOT / "Working_data"
CATEGORIES_FILE = WORKING_DATA / "02_Data_Categories.json"
CLEANING_FILE = WORKING_DATA / "04_Data_Cleaning_actions.json"
CHUNK_SIZE = 50000  # Process 50k rows at a time

# Create output folder
CLEANED_DATA.mkdir(exist_ok=True)

# --- LOAD CONFIGS ---
def load_json(filepath):
    """Load JSON file safely"""
    if not filepath.exists():
        print(f"❌ ERROR: {filepath} not found!")
        sys.exit(1)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ ERROR: {filepath} is not valid JSON!")
        sys.exit(1)

# --- VALIDATION ---
def validate_configs(categories, cleaning_actions, csv_filename):
    """Validate that all non-string columns have cleaning actions"""
    # Remove "sample_" prefix for lookup
    lookup_name = csv_filename.replace("sample_", "") if csv_filename.startswith("sample_") else csv_filename
    
    # Try with and without sample_ prefix
    cat_key = None
    for key in categories.keys():
        if key == csv_filename or key == lookup_name or key.replace("sample_", "") == csv_filename.replace("sample_", ""):
            cat_key = key
            break
    
    if not cat_key:
        print(f"❌ ERROR: {csv_filename} not found in categories!")
        return False
    
    file_categories = categories[cat_key]
    
    # Check for non-string columns missing cleaning actions
    missing_actions = []
    for col, cat in file_categories.items():
        if cat in ['int', 'float', 'date']:
            # Look for cleaning actions with any matching filename variant
            found = False
            for action_key in cleaning_actions.keys():
                if action_key == csv_filename or action_key == cat_key or action_key.replace("sample_", "") == csv_filename.replace("sample_", ""):
                    if col in cleaning_actions[action_key]:
                        found = True
                        break
            if not found:
                missing_actions.append(f"{col} ({cat})")
    
    if missing_actions:
        print(f"❌ ERROR: Missing cleaning actions for {csv_filename}:")
        for col in missing_actions:
            print(f"   - {col}")
        return False
    
    return True

# --- CLEANING FUNCTIONS ---
def clean_numeric_string(series):
    """Remove currency symbols, commas, parentheses from string series"""
    return series.astype(str).str.replace(r'[$,\s)]', '', regex=True).str.replace('(', '-', regex=False)

def apply_column_cleaning(df, col_name, actions, category):
    """
    Apply cleaning actions to a single column
    Returns: (cleaned_df, stats_dict)
    """
    stats = {
        'rows_removed': 0,
        'values_filled': 0,
        'values_capped': 0,
        'values_converted': 0,
        'parsing_errors': 0,
        'outliers': 0,
        'negatives': 0,
        'missing': 0
    }
    
    original_len = len(df)
    series = df[col_name].copy()
    
    # === DATE COLUMN ===
    if category == 'date':
        # Parse dates
        date_series = pd.to_datetime(series, errors='coerce')
        
        # Track issues
        parsing_errors_mask = date_series.isna() & series.notna()
        missing_mask = series.isna()
        stats['parsing_errors'] = parsing_errors_mask.sum()
        stats['missing'] = missing_mask.sum()
        
        # Handle parsing errors
        parse_action = actions.get('parsing_errors', 'keep')
        if parse_action == 'remove':
            df = df[~parsing_errors_mask]
            stats['rows_removed'] += parsing_errors_mask.sum()
            date_series = date_series[~parsing_errors_mask]
        elif parse_action == 'interpolate':
            date_series = date_series.interpolate(method='linear')
            stats['values_filled'] += parsing_errors_mask.sum()
        
        # Handle outliers (date range)
        if actions.get('min_date') and actions.get('max_date'):
            min_dt = pd.Timestamp(actions['min_date'])
            max_dt = pd.Timestamp(actions['max_date'])
            outliers_mask = (date_series < min_dt) | (date_series > max_dt)
            stats['outliers'] = outliers_mask.sum()
            
            outlier_action = actions.get('outliers', 'keep')
            if outlier_action == 'remove':
                df = df[~outliers_mask]
                stats['rows_removed'] += outliers_mask.sum()
                date_series = date_series[~outliers_mask]
            elif outlier_action == 'interpolate':
                date_series[outliers_mask] = pd.NaT
                date_series = date_series.interpolate(method='linear')
                stats['values_filled'] += outliers_mask.sum()
        
        # Handle missing
        miss_action = actions.get('missing', 'keep')
        if miss_action == 'remove':
            missing_now = date_series.isna()
            df = df[~missing_now]
            stats['rows_removed'] += missing_now.sum()
            date_series = date_series[~missing_now]
        elif miss_action == 'interpolate':
            before = date_series.isna().sum()
            date_series = date_series.interpolate(method='linear')
            stats['values_filled'] += before - date_series.isna().sum()
        
        df[col_name] = date_series
        return df, stats
    
    # === NUMERIC COLUMN (int/float) ===
    else:
        # Convert to numeric
        clean_str = clean_numeric_string(series)
        numeric_series = pd.to_numeric(clean_str, errors='coerce')
        
        # Track issues
        parsing_errors_mask = numeric_series.isna() & series.notna()
        missing_mask = series.isna()
        stats['parsing_errors'] = parsing_errors_mask.sum()
        stats['missing'] = missing_mask.sum()
        
        # Handle parsing errors
        parse_action = actions.get('parsing_errors', 'keep')
        if parse_action == 'strip':
            df[col_name] = numeric_series
        elif parse_action == 'remove':
            df = df[~parsing_errors_mask]
            stats['rows_removed'] += parsing_errors_mask.sum()
            numeric_series = numeric_series[~parsing_errors_mask]
        elif parse_action == 'mean':
            valid_values = numeric_series.dropna()
            if len(valid_values) > 0:
                fill_value = valid_values.mean()
                numeric_series[parsing_errors_mask] = fill_value
                stats['values_filled'] += parsing_errors_mask.sum()
            df[col_name] = numeric_series
        elif parse_action == 'median':
            valid_values = numeric_series.dropna()
            if len(valid_values) > 0:
                fill_value = valid_values.median()
                numeric_series[parsing_errors_mask] = fill_value
                stats['values_filled'] += parsing_errors_mask.sum()
            df[col_name] = numeric_series
        
        # Recalculate for outliers/negatives (work with current numeric_series)
        if len(numeric_series) > 0:
            # Handle outliers
            outlier_threshold = actions.get('outlier_threshold', 3.0)
            mean = numeric_series.mean()
            std = numeric_series.std()
            
            if std > 0:
                lower = mean - outlier_threshold * std
                upper = mean + outlier_threshold * std
                outliers_mask = (numeric_series > upper) | (numeric_series < lower)
                stats['outliers'] = outliers_mask.sum()
                
                outlier_action = actions.get('outliers', 'keep')
                if outlier_action == 'remove':
                    df = df[~outliers_mask]
                    stats['rows_removed'] += outliers_mask.sum()
                    numeric_series = numeric_series[~outliers_mask]
                elif outlier_action == 'mean':
                    numeric_series[outliers_mask] = mean
                    stats['values_filled'] += outliers_mask.sum()
                elif outlier_action == 'median':
                    numeric_series[outliers_mask] = numeric_series.median()
                    stats['values_filled'] += outliers_mask.sum()
                elif outlier_action == 'cap':
                    numeric_series = numeric_series.clip(lower=lower, upper=upper)
                    stats['values_capped'] += outliers_mask.sum()
                
                df[col_name] = numeric_series
            
            # Handle negatives
            negatives_mask = numeric_series < 0
            stats['negatives'] = negatives_mask.sum()
            
            neg_action = actions.get('negatives', 'keep')
            if neg_action == 'remove':
                df = df[~negatives_mask]
                stats['rows_removed'] += negatives_mask.sum()
                numeric_series = numeric_series[~negatives_mask]
            elif neg_action == 'absolute':
                numeric_series = numeric_series.abs()
                stats['values_converted'] += negatives_mask.sum()
            elif neg_action == 'mean':
                if negatives_mask.any():
                    numeric_series[negatives_mask] = numeric_series.mean()
                    stats['values_filled'] += negatives_mask.sum()
            elif neg_action == 'median':
                if negatives_mask.any():
                    numeric_series[negatives_mask] = numeric_series.median()
                    stats['values_filled'] += negatives_mask.sum()
            
            df[col_name] = numeric_series
        
        # Handle missing
        miss_action = actions.get('missing', 'keep')
        if miss_action == 'remove':
            missing_now = numeric_series.isna()
            df = df[~missing_now]
            stats['rows_removed'] += missing_now.sum()
        elif miss_action == 'mean':
            before = numeric_series.isna().sum()
            numeric_series = numeric_series.fillna(numeric_series.mean())
            stats['values_filled'] += before - numeric_series.isna().sum()
            df[col_name] = numeric_series
        elif miss_action == 'median':
            before = numeric_series.isna().sum()
            numeric_series = numeric_series.fillna(numeric_series.median())
            stats['values_filled'] += before - numeric_series.isna().sum()
            df[col_name] = numeric_series
        
        return df, stats

# --- MAIN PROCESSING ---
def process_csv(csv_path, categories, cleaning_actions):
    """Process a single CSV file with chunked processing"""
    csv_filename = csv_path.name
    print(f"\n📄 Processing: {csv_filename}")
    
    # Validate configs
    if not validate_configs(categories, cleaning_actions, csv_filename):
        return False
    
    # Find matching category key
    cat_key = None
    for key in categories.keys():
        if key == csv_filename or key.replace("sample_", "") == csv_filename.replace("sample_", ""):
            cat_key = key
            break
    
    file_categories = categories[cat_key]
    
    # Find matching actions key
    action_key = None
    for key in cleaning_actions.keys():
        if key == csv_filename or key == cat_key or key.replace("sample_", "") == csv_filename.replace("sample_", ""):
            action_key = key
            break
    
    file_actions = cleaning_actions.get(action_key, {}) if action_key else {}
    
    # Determine which columns to keep/delete
    cols_to_delete = [col for col, cat in file_categories.items() if cat == 'IGNORE']
    cols_to_clean = {col: cat for col, cat in file_categories.items() if cat in ['int', 'float', 'date']}
    cols_to_copy = [col for col, cat in file_categories.items() if cat == 'string']
    
    print(f"   🗑️  Deleting {len(cols_to_delete)} IGNORE columns")
    print(f"   🧹 Cleaning {len(cols_to_clean)} numeric/date columns")
    print(f"   📋 Copying {len(cols_to_copy)} string columns as-is")
    
    # Count total rows
    print(f"   📊 Counting rows...")
    with open(csv_path, 'r', encoding='utf-8') as f:
        total_rows = sum(1 for _ in f) - 1  # -1 for header
    print(f"   📈 Total rows: {total_rows:,}")
    
    # Process in chunks
    output_path = CLEANED_DATA / f"Cleaned_{csv_filename}"
    chunk_stats = []
    first_chunk = True
    total_rows_output = 0
    
    print(f"   ⚡ Processing in chunks of {CHUNK_SIZE:,}...")
    
    for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=CHUNK_SIZE), 1):
        chunk_start_rows = len(chunk)
        
        # Delete IGNORE columns
        chunk = chunk.drop(columns=cols_to_delete, errors='ignore')
        
        # Clean numeric/date columns
        for col, cat in cols_to_clean.items():
            if col in chunk.columns and col in file_actions:
                chunk, stats = apply_column_cleaning(chunk, col, file_actions[col], cat)
                chunk_stats.append((col, stats))
        
        # Write chunk
        chunk.to_csv(output_path, mode='w' if first_chunk else 'a', header=first_chunk, index=False)
        first_chunk = False
        total_rows_output += len(chunk)
        
        rows_removed = chunk_start_rows - len(chunk)
        print(f"      Chunk {chunk_num}: {chunk_start_rows:,} → {len(chunk):,} rows ({rows_removed:,} removed)")
    
    print(f"   ✅ Output: {total_rows_output:,} rows ({total_rows - total_rows_output:,} removed total)")
    print(f"   💾 Saved to: {output_path.name}")
    
    return True

def main():
    print("=" * 60)
    print("🧹 DATA CLEANING - APPLY SCRIPT")
    print("=" * 60)
    print(f"📂 Input:  {RAW_DATA}")
    print(f"📂 Output: {CLEANED_DATA}")
    print(f"⚙️  Config: {CATEGORIES_FILE.name} + {CLEANING_FILE.name}\n")
    
    # Load configs
    categories = load_json(CATEGORIES_FILE)
    cleaning_actions = load_json(CLEANING_FILE)
    
    # Find CSV files
    csv_files = sorted(list(RAW_DATA.glob("*.csv")))
    
    if not csv_files:
        print("❌ No CSV files found in Raw_Data!")
        return
    
    print(f"📊 Found {len(csv_files)} CSV file(s)\n")
    
    # Process each file
    success_count = 0
    for csv_file in csv_files:
        if process_csv(csv_file, categories, cleaning_actions):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✨ COMPLETE: {success_count}/{len(csv_files)} files processed successfully")
    print("=" * 60)

if __name__ == "__main__":
    main()