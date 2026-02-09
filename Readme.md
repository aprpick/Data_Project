# Data Project - Real Estate Assessment Data

## Setup

1. Created virtual environment: `python -m venv venv`
2. Activated venv: `.\venv\Scripts\Activate.ps1`
3. Installed dependencies: `pip install pandas streamlit`

## Data Preparation

1. Created portable folder structure with relative paths
2. Generated 1,000-row sample files from raw data: `python Working_data/sample_data.py`
3. Built Streamlit categorization app: `streamlit run Working_data/column_categorizer.py`
4. Categorized all columns across 4 datasets (IDs, dates, currency, categorical, etc.)
5. Saved categorizations to `column_categories.json`

## Next Steps

- Data validation and cleaning
- Merge datasets on parcel IDs
- Analysis and reporting
