from pathlib import Path
import pandas as pd
import json
import re

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent

# Define folder paths
WORKING_DATA = PROJECT_ROOT / "Working_data"
CONFIG_FILE = WORKING_DATA / "column_categories.json"

def load_categories():
    """Load column categorizations from JSON"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        print("❌ No column_categories.json found. Run categorizer first!")
        return {}

def clean_currency(series):
    """Clean currency columns: remove $, commas, convert to float"""
    if series.dtype == 'object':
        # Remove $, commas, whitespace
        cleaned = series.astype(str).str.replace(r'[$,\s]', '', regex=True)
        # Replace empty strings and 'nan' with actual NaN
        cleaned = cleaned.replace(['', 'nan', 'None'], pd.NA)
        # Convert to float
        return pd.to_numeric(cleaned, errors='coerce')
    return series

def clean_date(series):
    """Convert date columns to datetime"""
    return pd.to_datetime(series, errors='coerce')

def clean_boolean(series):
    """Standardize boolean columns"""
    if series.dtype == 'object':
        # Map common boolean representations
        bool_map = {
            'true': True, 'True': True, 'TRUE': True, 'yes': True, 'Yes': True, 'Y': True, '1': True,
            'false': False, 'False': False, 'FALSE': False, 'no': False, 'No': False, 'N': False, '0': False
        }
        return series.map(bool_map).astype('boolean')
    return series.astype('boolean')

def clean_zip_code(series):
    """Clean and format ZIP codes"""
    if series.dtype == 'float64':
        # Convert float to string, remove decimal
        cleaned = series.fillna('').astype(str).str.replace(r'\.0$', '', regex=True)
    else:
        cleaned = series.astype(str)
    
    # Remove non-digits, keep only first 5-6 digits
    cleaned = cleaned.str.extract(r'(\d{5,6})')[0]
    return cleaned

def clean_state(series):
    """Standardize state codes to uppercase 2-letter format"""
    if series.dtype == 'object':
        return series.str.strip().str.upper()
    return series

def clean_numeric_count(series):
    """Ensure numeric count columns are integers"""
    return pd.to_numeric(series, errors='coerce').astype('Int64')

def clean_dataframe(df, file_key, categories):
    """Apply cleaning transformations based on categorizations"""
    
    if file_key not in categories:
        print(f"⚠️  No categorizations found for {file_key}")
        return df
    
    file_categories = categories[file_key]
    changes_log = []
    
    for col_name in df.columns:
        if col_name not in file_categories:
            continue
            
        category = file_categories[col_name]
        original_dtype = df[col_name].dtype
        
        try:
            # Apply cleaning based on category
            if category == "Numeric - Currency":
                df[col_name] = clean_currency(df[col_name])
                changes_log.append(f"  ✓ {col_name}: Cleaned currency ({original_dtype} → {df[col_name].dtype})")
                
            elif category == "Date/Datetime":
                df[col_name] = clean_date(df[col_name])
                changes_log.append(f"  ✓ {col_name}: Converted to datetime ({original_dtype} → {df[col_name].dtype})")
                
            elif category == "Boolean/Binary":
                df[col_name] = clean_boolean(df[col_name])
                changes_log.append(f"  ✓ {col_name}: Standardized boolean ({original_dtype} → {df[col_name].dtype})")
                
            elif category == "ZIP Code":
                df[col_name] = clean_zip_code(df[col_name])
                changes_log.append(f"  ✓ {col_name}: Formatted ZIP code ({original_dtype} → {df[col_name].dtype})")
                
            elif category == "State":
                df[col_name] = clean_state(df[col_name])
                changes_log.append(f"  ✓ {col_name}: Standardized state code ({original_dtype} → {df[col_name].dtype})")
                
            elif category == "Numeric - Count":
                if df[col_name].dtype == 'object':
                    df[col_name] = clean_numeric_count(df[col_name])
                    changes_log.append(f"  ✓ {col_name}: Converted to integer ({original_dtype} → {df[col_name].dtype})")
                    
        except Exception as e:
            changes_log.append(f"  ❌ {col_name}: Error - {str(e)}")
    
    return df, changes_log

def clean_all_samples():
    """Clean all sample CSV files in Working_data"""
    
    print("🧹 Data Cleaning Script\n")
    print(f"📂 Working Directory: {WORKING_DATA}\n")
    
    # Load categorizations
    categories = load_categories()
    if not categories:
        return
    
    # Get all sample CSV files
    csv_files = list(WORKING_DATA.glob("sample_*.csv"))
    
    if not csv_files:
        print("❌ No sample CSV files found in Working_data folder")
        return
    
    print(f"📊 Found {len(csv_files)} sample file(s)\n")
    
    for csv_file in csv_files:
        print(f"📄 Processing: {csv_file.name}")
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            original_shape = df.shape
            
            # Clean based on categories
            result = clean_dataframe(df, csv_file.name, categories)

            # Handle case where file has no categorizations
            if isinstance(result, tuple):
                df_cleaned, changes = result
            else:
                df_cleaned = result
                changes = []
            
            # Print changes
            if changes:
                for change in changes:
                    print(change)
            else:
                print("  ℹ️  No cleaning rules applied")
            
            # Overwrite original file
            df_cleaned.to_csv(csv_file, index=False)
            print(f"  💾 Saved cleaned data ({original_shape[0]} rows, {original_shape[1]} cols)\n")
            
        except Exception as e:
            print(f"  ❌ Error processing file: {e}\n")
    
    print("✨ Cleaning complete!")

if __name__ == "__main__":
    clean_all_samples()