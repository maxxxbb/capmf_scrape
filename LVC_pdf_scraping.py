import pandas as pd
import camelot
import re
import xlsxwriter

### 1. Define Global variables

# 1.1 Path to pdf containing land value capture policies data
pdf_file = r"\\main.oecd.org\ASgenENV\ENVINFO\BACKUP\STATA\IPAC\CAP\Excel files\1_RawDataCAP\Extension\LVC_full_report.pdf"

# 1.2 Country list and their respective pages in the pdf - copied from pdf table of contents

country_pages = {
    'Argentina': 42,
    'Australia': 46,
    'Austria': 50,
    'Bangladesh': 54,
    'Belgium': 57,
    'Brazil': 61,
    'Canada': 64,
    'Chile': 67,
    'China, People’s Republic of': 71,
    'Colombia': 75,
    'Costa Rica': 79,
    'Czech Republic': 82,
    'Denmark': 85,
    'Dominican Republic': 89,
    'Ecuador': 92,
    'Egypt': 96,
    'Estonia': 100,
    'Ethiopia': 103,
    'Finland': 106,
    'France': 110,
    'Germany': 114,
    'Ghana': 120,
    'Greece': 123,
    'Hong Kong': 126,
    'Hungary': 129,
    'India': 131,
    'Indonesia': 135,
    'Ireland': 138,
    'Israel': 141,
    'Italy': 146,
    'Japan': 152,
    'Korea': 156,
    'Latvia': 160,
    'Lithuania': 163,
    'Luxembourg': 166,
    'Mexico': 168,
    'Morocco': 172,
    'Namibia': 175,
    'Netherlands': 177,
    'New Zealand': 180,
    'Nigeria': 183,
    'Norway': 186,
    'Pakistan': 189,
    'Peru': 192,
    'Poland': 196,
    'Portugal': 200,
    'Singapore': 204,
    'Slovak Republic': 208,
    'Slovenia': 212,
    'South Africa': 216,
    'Spain': 220,
    'Sweden': 224,
    'Switzerland': 227,
    'Tunisia': 230,
    'Turkey': 233,
    'Uganda': 237,
    'Ukraine': 239,
    'United Kingdom': 242,
    'United States': 245,
    'Vietnam': 249
}

# 1.3 LVC data variables
columns = ["Instrument (OECD-Lincoln taxonomy)", "Local name", "National legal provision", "Implementation", "Use"]

# 1.4 Path where xlsx will be stored

output_path = "//main.oecd.org/ASgenENV/ENVINFO/BACKUP/STATA/IPAC/CAP/Excel files/1_RawDataCAP/Extension/LVC.xlsx"

### 2. Define functions

def extract_valid_years(text):
    """
    Extracts the year in which the national legal provision 
    based on the string provided in the national legal provision
    column. Applied to each row in function extract_LVC_Data

    Input:
            - text: string containing the national legal provision

    Output:

            - valid_years: list of valid years extracted from the text

    """
    # Regular expression to find sequences of 4 digits
    year_pattern = r'\b\d{4}\b'
    
    # Find all matches of the pattern in the text
    matches = re.findall(year_pattern, text)
    
    # Filter matches to include only years between 1900 and 2025
    valid_years = [int(year) for year in matches if 1800 <= int(year) <= 2025]
    
    return valid_years if valid_years else None  
        



def extract_LVC_Data(pdf_file, dictionary, columns, output_path):
    """
    Loops over countries and respective pages in the predefined 
    dictionary and extracts the country tables from the pdf. 
    Concatenates all country Dataframes into one and applies
    some datacleaning steps.
    
    Input:
            - pdf_file: path to pdf containing land value capture policies data
            - dictionary: dictionary containing countries and their respective pages in the pdf
            - columns: list of column names for the extracted data
            - output_path: Location where xlsx is stored
    
    Output:
            - combined_df: concatenated DataFrame containing all extracted data on LVC policies
        
    """

    dfs = []

    # Iterate through each country and its respective page number
    for country, page_number in dictionary.items():
        # Calculate the actual page number (adding 2 to the dictionary value)
        actual_page_number = page_number + 2
        
        # Read the PDF and extract tables from the specified page
        tables = camelot.read_pdf(pdf_file, pages=str(actual_page_number))
        
        # Iterate through each table extracted from the page
        for table in tables:
            # Extract the data from the table into a DataFrame
            df = table.df
            
            # Set the column names
            if len(df.columns) < len(columns):
                df.columns = columns[:len(df.columns)]
            else:
                df.columns = columns
            
            
            df["Country"] = country
            print(f"{country} data extracted")
            
            # Append the DataFrame to the list of country dfs
            dfs.append(df)

    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(dfs, ignore_index=True)


    # Data cleaning 
    combined_df = combined_df.replace(r'\n','', regex=True)        
    combined_df = combined_df.replace(r' +', ' ', regex=True)
    combined_df['Instrument (OECD-Lincoln taxonomy)'].replace('', pd.NA, inplace=True)
    combined_df['Instrument (OECD-Lincoln taxonomy)'].fillna(method='ffill', inplace=True)

    # Create year variable based on national legal provision
    combined_df['Year'] = combined_df['National legal provision'].apply(extract_valid_years)


    ### get subset where no year is recognized but legislation is in place
    subset_df = combined_df[
    (~combined_df["National legal provision"].isin(["None", "No", "n/a", "N/A"])) &
    (combined_df["Year"].isna())]


    ## Save Excel
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        combined_df.to_excel(writer, sheet_name='Combined', index=False)
        #subset_df.to_excel(writer, sheet_name='Subset', index=False)


### 3. Run the function

extract_LVC_Data(pdf_file = pdf_file, dictionary = country_pages, columns=columns ,output_path = output_path)
