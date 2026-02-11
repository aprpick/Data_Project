from pathlib import Path
import pandas as pd
import random

# Get project root (parent of Working_data folder where this script lives)
PROJECT_ROOT = Path(__file__).parent.parent

# Define folder paths
RAW_DATA = PROJECT_ROOT / "Working_data\Raw_Data"
WORKING_DATA = PROJECT_ROOT / "Working_data\Sample_Data"

# Sample size
SAMPLE_SIZE = 10000

def sample_csv_files():
    """Sample 10000 rows from each CSV in Raw_Data and save to Working_data"""
    
    # Get all CSV files in Raw_Data
    csv_files = list(RAW_DATA.glob("*.csv"))
    
    if not csv_files:
        print("❌ No CSV files found in Raw_Data folder")
        return
    
    print(f"📊 Found {len(csv_files)} CSV file(s) in Raw_Data\n")
    
    for csv_file in csv_files:
        try:
            print(f"📖 Processing: {csv_file.name}")
            
            # Fast row count using wc-like approach
            print(f"   🔢 Counting rows...")
            with open(csv_file, 'r', encoding='utf-8') as f:
                total_rows = sum(1 for _ in f) - 1  # -1 for header
            
            print(f"   📏 Total rows: {total_rows:,}")
            
            # Determine sample size
            sample_n = min(SAMPLE_SIZE, total_rows)
            
            if total_rows <= SAMPLE_SIZE:
                # Small file - just read it all
                print(f"   📥 Reading all rows...")
                df = pd.read_csv(csv_file)
            else:
                # Large file - use skiprows for MUCH faster sampling
                print(f"   ⚡ Fast sampling {sample_n:,} rows...")
                
                # Generate random row indices to keep
                random.seed(42)
                skip_indices = sorted(random.sample(range(1, total_rows + 1), total_rows - sample_n))
                
                # Read CSV but skip the randomly selected rows
                df = pd.read_csv(csv_file, skiprows=skip_indices)
            
            # Create output filename with "sample_" prefix
            output_file = WORKING_DATA / f"sample_{csv_file.name}"
            
            # Save to Working_data
            print(f"   💾 Saving to {output_file.name}...")
            df.to_csv(output_file, index=False)
            
            print(f"   ✅ Complete! Sampled {len(df):,} rows\n")
            
        except Exception as e:
            print(f"   ❌ Error processing {csv_file.name}: {e}\n")

if __name__ == "__main__":
    print("🎲 CSV Sampling Script (Fast Version)\n")
    print(f"📂 Raw Data Folder: {RAW_DATA}")
    print(f"📂 Working Data Folder: {WORKING_DATA}")
    print(f"🔢 Sample Size: {SAMPLE_SIZE:,} rows\n")
    
    sample_csv_files()
    
    print("✨ Sampling complete!")