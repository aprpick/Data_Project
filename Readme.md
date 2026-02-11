1. Place .csv data in Raw_Data folder.
2. Add Column tooltips to Working_data\00_column_descriptions.json.
3. Run "Working_data\00_Sample_Data.py" to create 10,000 row copies from any .csv in "Working_data\Sample_Data".
4. Run "streamlit run Working_data\01_Data_Catagorizer.py" assign data types to the sample .csvs, some will be automatically assigned if unambiguous. The rest will need to be manually assigned. Saving Creates "Working_data\02_Data_Categories.json".
5. Run "Working_data\03_Data_Cleaning_Config.py" and select cleaning actions to create "Working_data\04_Data_Cleaning_actions.json".
6.
