
1. Place .csv data in Raw_Data folder.
2. Add column tooltips to Working_data\00_column_descriptions.json. See below for format.
3. Run "python Working_data\00_Sample_Data.py" to create 10,000 row samples from any .csv in Raw_Data and save to Working_data\Sample_Data.
4. Run "streamlit run Working_data\01_Data_Catagorizer.py" to assign data types to the sample .csvs. Some will be automatically assigned if unambiguous, the rest need manual assignment. Saving creates "Working_data\02_Data_Categories.json".
5. Run "streamlit run Working_data\03_Data_Cleaning_Config.py" and select cleaning actions to create "Working_data\04_Data_Cleaning_actions.json".
6. Run "python Working_data\05_Apply_Cleaning.py" to clean and save new .csvs to Working_data\Cleaned_Data. A detailed report is generated at "Working_data\Cleaned_Data\00_Cleaning_Report.md".



{

  "sample_file1.csv": {

    "column1": "Description for column 1",

    "column2": "Description for column 2"

  },

  "sample_file2.csv": {

    "column1": "Description for column 1",

    "column2": "Description for column 2"

  }

}
