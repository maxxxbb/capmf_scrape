import pandas as pd
import camelot
import numpy as np

def extract_tables_from_pdf(file_path, pages, table_areas):
    """
    Extract tables from PDF file using Camelot.
    
    Parameters:
    - file_path (str): Path to the MARPOL PDF file.
    - pages (str or list): Page number(s) to extract tables from.
    - table_areas (list of str): List of table areas in format 'x1,y1,x2,y2'.

    Returns:
    - list of pandas.DataFrame: List of DataFrames containing extracted tables.
    """
    tables = []
    for page, area in zip(pages, table_areas):
        tables_page = camelot.read_pdf(file_path, pages=str(page), flavor='stream', table_areas=[area])
        for table in tables_page:
            tables.append(table.df)
    return tables

def clean_combined_data(combined):
    """
    Renames columns and cleans 'Country' strings by removing extra information.
    
    Parameters:
    - combined (pandas.DataFrame): DataFrame containing combined MARPOL data.

    Returns:
    - pandas.DataFrame: Cleaned DataFrame.
    """
    combined.rename(columns={0: "Country", 1: "Signature", 2: "EntryintoForce"}, inplace=True)
    combined['Country'] = combined['Country'].fillna('').str.split(' \(').str[0]
    return combined

def add_manual_data(combined):
    """
    Add manually specified data for Macau and Hong Kong to combined DataFrame.

    Parameters:
    - combined (pandas.DataFrame): DataFrame containing combined data.

    Returns:
    - pandas.DataFrame: DataFrame with manually added data.
    """
    new_data = {
        'Country': ['Macau', 'Hong Kong'],
        'Signature': ['23 May 2006', '20 March 2008'],
        'EntryintoForce': ['23 May 2006', '20 March 2008']
    }
    new_rows = pd.DataFrame(new_data)
    combined = pd.concat([combined, new_rows], ignore_index=True)
    return combined

def generate_panel_data(combined):
    """
    Generate panel data format spanning from 1990 to 2023.

    Parameters:
    - combined (pandas.DataFrame): DataFrame containing combined MARPOL data.

    Returns:
    - pandas.DataFrame: Panel data formatted MARPOL data
    """
    panel_data = pd.DataFrame()
    for year in range(1990, 2024):  
        temp = combined.copy()
        temp['Year'] = year
        panel_data = pd.concat([panel_data, temp], axis=0)
    return panel_data

def clean_panel_data(panel_data):
    """
    Clean panel data by converting date columns to years, handling NaN values,
    and creating 'marpol_sign' and 'marpol_effect' columns.

    Parameters:
    - panel_data (pandas.DataFrame): DataFrame containing panel data.

    Returns:
    - pandas.DataFrame: Cleaned panel data.
    """
    panel_data['Signature'] = pd.to_datetime(panel_data['Signature'], errors='coerce').dt.year
    panel_data['EntryintoForce'] = pd.to_datetime(panel_data['EntryintoForce'], errors='coerce').dt.year
    panel_data['Country'] = panel_data['Country'].str.replace('\n', '')

    panel_data.loc[panel_data['Year'] < 2005, 'EntryintoForce'] = np.nan
    panel_data.loc[panel_data['Year'] < 1997, 'Signature'] = np.nan

    panel_data['marpol_sign'] = (panel_data['Signature'] <= panel_data['Year']).astype(int)
    panel_data['marpol_effect'] = (panel_data['EntryintoForce'] <= panel_data['Year']).astype(int)

    panel_data = panel_data.sort_values(by=['Country', 'Year']).reset_index(drop=True)
    panel_data = panel_data[['Country', 'Year', 'marpol_sign', 'marpol_effect']]

    return panel_data

def save_to_excel(combined, output_path):
    """
    Save combined data (raw data) and panel data to Excel file.

    Parameters:
    - combined (pandas.DataFrame): DataFrame containing combined data.
    - panel_data (pandas.DataFrame): DataFrame containing panel data structure
    - output_path (str): Output file path for Excel file.
    """
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        combined.to_excel(writer, sheet_name='raw data', index=False)
        
        panel_data_full = generate_panel_data(combined)
        panel_data_cleaned = clean_panel_data(panel_data_full)
        
        panel_data_cleaned.to_excel(writer, sheet_name='panel data', index=False)






############ Run Functions 




if __name__ == "__main__":
    
    ## Define Input and Output paths, relevant pages of the PDF and the area where one can find those tables
    
    file_path = r"\\main.oecd.org\ASgenENV\ENVINFO\BACKUP\STATA\IPAC\CAP\Excel files\1_RawDataCAP\Extension\MARPOL_Status_2024.pdf"
    output_path = r"\\main.oecd.org\ASgenENV\ENVINFO\BACKUP\STATA\IPAC\CAP\Excel files\1_RawDataCAP\Extension\MARPOL_Status_2024.xlsx"
    table_areas = ['50,615,550,50', '50,800,550,200']
    pages = ['189', '190']

    # Step 1: Extract data from PDF
    tables = extract_tables_from_pdf(file_path, pages, table_areas)
    combined_data = pd.concat(tables, ignore_index=True)

    # Step 2: Clean and add manual data
    combined_data = clean_combined_data(combined_data)
    combined_data = add_manual_data(combined_data)

    # Step 3: Save raw and panel data to Excel
    save_to_excel(combined_data, output_path)
