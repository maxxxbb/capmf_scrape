# 1. Necessary packages: selenium and webdriver_manager

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import time

# 1.2 Define XPaths for all 10 subindicators
base_xpath = "/html/body/sfm-root/sfm-top-image-layout/div/div[3]/sfm-analytics-home/div/div[3]/div[2]/sfm-indicators-with-fields/div/div[2]/div/sfm-dropdown-select/div/ul/li/ul/div/li[{}]/span"
subindicators_xpaths = {f"e1a{i}": base_xpath.format(i) for i in range(1, 11)}

# 2. Define Functions

def select_subindicator(subindicator_xpath):
    """
    Selects the subindicator based on the provided XPath.

    Args:
        subindicator_xpath (str): The XPath of the subindicator to be selected on the website.
    """
    
    try:
        dropdown_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/sfm-root/sfm-top-image-layout/div/div[3]/sfm-analytics-home/div/div[3]/div[2]/sfm-indicators-with-fields/div/div[2]/div/sfm-dropdown-select/div/ul')))
        dropdown_menu.click()

        subindicator_option = wait.until(EC.element_to_be_clickable((By.XPATH, subindicator_xpath)))
        subindicator_option.click()
    except Exception as e:
        print(f"Error while selecting subindicator: {e}")

def select_year_2005():
    """
    Selects the year 2005 from the dropdown menu to get Kyogo Framework subindicators
    """
    try:
        # First, click to open the dropdown
        year_dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="message-wrapper button-color"]/span')))
        year_dropdown_button.click()

        
        year_2005_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-test="dropdownMenu-cycle.2005"]')))
        year_2005_option.click()
    except Exception as e:
        print(f"Error while selecting year 2005: {e}")

def select_year_2024():
    """
    Selects the year 2024 from the dropdown menu to retreive Sendai Framework subindicators
    """
    try:
        # First, click to open the dropdown
        year_dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="message-wrapper button-color"]/span')))
        year_dropdown_button.click()

        # Then, select the year 2024
        year_2024_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@data-test="dropdownMenu-cycle.2024"]')))
        year_2024_option.click()
    except Exception as e:
        print(f"Error while selecting year 2024: {e}")

def click_table_button():
    """
    Clicks the button to display the table with subindicators.
    """
    try:
        # Use the exact XPath to locate table with subindicators
        table_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/sfm-root/sfm-top-image-layout/div/div[3]/sfm-analytics-home/div/div[5]/sfm-analytics-country-target/div/div/sfm-analytics-comparison-criteria/sfm-analytics-evolution/div/div[2]/div[1]/sfm-button-group/div/div[2]/i')))
        table_button.click()
    except Exception as e:
        print(f"Error while clicking the table button: {e}")

def extract_table_data(subindicator_name, country_code):
    """
    Extracts the data from the displayed table and returns it as a DataFrame.

    Args:
        subindicator_name (str): The name of the subindicator being extracted.
        country_code (int): The country code to be added to the DataFrame.

    Returns:
        pd.DataFrame: DataFrame containing the extracted data.
    """
    time.sleep(1)  # Give the page a little time
    try:
        country_name_element = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/sfm-root/sfm-top-image-layout/div/div[3]/sfm-analytics-home/div/div[5]/sfm-analytics-country-target/div/div/sfm-analytics-comparison-criteria/sfm-analytics-evolution/div/div[2]/div[2]/table/thead/tr/th[2]/div/div/div[2]')))
        country_name = country_name_element.text
        print(f"Extracting data for: {country_name} - {subindicator_name}")

        table = wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/sfm-root/sfm-top-image-layout/div/div[3]/sfm-analytics-home/div/div[5]/sfm-analytics-country-target/div/div/sfm-analytics-comparison-criteria/sfm-analytics-evolution/div/div[2]/div[2]/table')))
        
        table_rows = table.find_elements(By.XPATH, './/tbody/tr')

        data = []
        for row in table_rows:
            year = row.find_element(By.XPATH, './td[1]').text  # Extract the year
            value = row.find_element(By.XPATH, './td[2]').text  # Extract the value
            data.append({'Country': country_name, 'Year': year, subindicator_name: value, 'Country_Code': country_code})

        df = pd.DataFrame(data)
        print(f"Table data extracted successfully for {country_name} - {subindicator_name}.")
        return df

    except Exception as e:
        print(f"Error while extracting table data: {e}")
        return None

def run_scraping(subindicators_xpaths, base_year, country_list):

    # empty list to hold all country data
    all_country_container = []

    for country_code in country_list:
        url = f'https://sendaimonitor.undrr.org/analytics/country-global-target/11/6?indicator=73&countries={country_code}'
        driver.get(url)
        click_table_button()
        # Extract data for 2015-2024 (Sendai Framework) or 2005-2015 (Kyogo Framework)
        if base_year == 2005:
            select_year_2005()
        else:
            select_year_2024()
        
        # Container df for current country
        country_df = pd.DataFrame()

        # Initialize a flag to track the first subindicator iteration
        first_iteration = True

        # Loop through the 10 subindicators (The dictionary is defined above)
        for subindicator_index, (subindicator_name, subindicator_xpath) in enumerate(subindicators_xpaths.items(), start=1):
            
            if first_iteration:
                # Click on the second subindicator first, then go back to the first : This is a workaround to avoid the issue of the table not refreshing when selecting the year dropdown
                second_subindicator_xpath = '/html/body/sfm-root/sfm-top-image-layout/div/div[3]/sfm-analytics-home/div/div[3]/div[2]/sfm-indicators-with-fields/div/div[2]/div/sfm-dropdown-select/div/ul/li/ul/div/li[2]/span'  # Assuming 'e1a2' is the second subindicator
                select_subindicator(second_subindicator_xpath)
                time.sleep(1)  # Wait for 1 second
                # Now, select the first subindicator
                select_subindicator(subindicator_xpath)
                time.sleep(1)  # Wait for 1 second

                first_iteration = False  # Set the flag to False after the first iteration
            else:
                # Normal behavior for subsequent subindicators
                select_subindicator(subindicator_xpath)

        
            df = extract_table_data(subindicator_name,country_code)  # Pass country_code to the function
            
            if df is not None:
                if country_df.empty:
                    country_df = df
                else:
                    country_df = pd.merge(country_df, df, on=['Country', 'Year', 'Country_Code'], how='outer')
            else:
                print(f"Failed to extract data for subindicator {subindicator_name} in {base_year} data and country code {country_code}.")
        
        if not country_df.empty:
            all_country_container.append(country_df)
            print(f"Full {base_year} data for country code {country_code} extracted successfully.")

    
    final_df = pd.concat(all_country_container, ignore_index=True)
    # final_df_2024.to_csv(r"V:\ENVINFO\BACKUP\STATA\IPAC\CAP\Excel files\1_RawDataCAP\Extension\DRR_Sendai_2015_2024_subindicator_e1.csv", index=False)



    return final_df


## 3. first run: 2015-2024 data for all countries

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 30)
df_2024 = run_scraping(subindicators_xpaths = subindicators_xpaths , base_year=2024 , country_list=range(1, 194))
driver.quit()

# Get missing countries for retries
extracted_country_codes = final_df_2024['Country_Code'].unique()
missing_country_codes = set(range(1, 194)) - set(extracted_country_codes)

if missing_country_codes:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 30)
    df_2024_missing = run_scraping(subindicators_xpaths = subindicators_xpaths , base_year=2024 , country_list=missing_country_codes)
    driver.quit()
    full_df_2024 = pd.concat([df_2024, df_2024_missing], ignore_index=True)
else:
    full_df_2024 = df_2024

# concat first iteration data and retry dataframe for 2015-2024 data


full_df_2024 = full_df_2024.sort_values(by=['Country', 'Year'], inplace=True)
full_df_2024.to_csv(r"V:\ENVINFO\BACKUP\STATA\IPAC\CAP\Excel files\1_RawDataCAP\Extension\DRR_Sendai_2015_2024_subindicators.csv", index=False)




### 4. Now 2005-2015 data (Kyogo Framework): Webpage does not allow for scraping all years in one go

## first run: 2015-2024 data

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 30)
df_2005 = run_scraping(subindicators_xpaths = subindicators_xpaths , base_year=2005 , country_list=range(1, 194))
driver.quit()

# Get missing countries for retries
extracted_country_codes = df_2005['Country_Code'].unique()
missing_country_codes = set(range(1, 194)) - set(extracted_country_codes)

if missing_country_codes:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 30)
    df_2005_missing = run_scraping(subindicators_xpaths = subindicators_xpaths , base_year=2005 , country_list=missing_country_codes)
    driver.quit()
    full_df_2005 = pd.concat([df_2005, df_2005_missing], ignore_index=True)
else:
    full_df_2005 = df_2005

# concat first iteration data and retry dataframe for 2015-2024 data


full_df_2005.sort_values(by=['Country', 'Year'], inplace=True)
final_df_2005 = full_df_2005[full_df_2005['Year'] != "2015"]


### 5. Combine both dataframes and save to xlsx


final_df = pd.concat([final_df_2005, final_df_2024])
final_df = final_df.sort_values(by=["Country", "Year"])
final_df["Year"] = pd.to_numeric(final_df["Year"], errors='coerce').astype(int)

# save to Excel


with pd.ExcelWriter(r"V:\ENVINFO\BACKUP\STATA\IPAC\CAP\Excel files\1_RawDataCAP\Extension\DRR_Sendai_Kyogo_Subindicators_E1.xlsx", engine='xlsxwriter') as writer:
    final_df.to_excel(writer, sheet_name='Data', index=False)
    
    readme_text = (
        "Data Source:\n"
        "This dataset is extracted from the Sendai Monitor (UNDRR) website, which provides data on subindicators related to disaster risk reduction strategies.\n"
        "Link: https://sendaimonitor.undrr.org/analytics/country-global-target/20/6?indicator=73 \n\n"
        "Data is scraped in this Python script: \\\\main.oecd.org\\ASgenENV\\ENVINFO\\BACKUP\\STATA\\IPAC\\CAP\\Others\\Scraping_Scripts\\DRR_subindicators.py\n"
        "Beware: Script runs a long time (~5h). Python version used was 3.11.7 \n"          
        "The data for the years 2005-2015 (Kyogo Framework) and 2015-2024 (Sendai Framework) were extracted separately and then combined.\n\n"
        "Variables:\n"
        "   • Country\n"
        "   • Year\n"
        "   • e1a[i]: Subindicator data for each subindicator (e1a1 to e1a10).\n\n"
        "Notes on subindicators:\n"
        "• 1: Have objectives and measures aimed at reducing existing risk\n"
        "• 2: Have objectives and measures aimed at preventing the creation of risk\n"
        "• 3: Have objectives and measures aimed at strengthening economic, social, health, and environmental resilience\n"
        "• 4: Have time frames, targets, and indicators\n"
        "• 5: Address Priority 1 recommendations and suggestions\n"
        "• 6: Address Priority 2 recommendations and suggestions\n"
        "• 7: Address Priority 3 recommendations and suggestions\n"
        "• 8: Address Priority 4 recommendations and suggestions\n"
        "• 9: Interacted at all levels with development and poverty eradication plans and policy, notably with the SDGs.\n"
        "• 10: Promote coherence, interaction, and compliance with CC adaptation and mitigation plans, with the Paris Agreement\n\n"
        "Please refer to the 'Data' sheet for the processed data."
    )
    
    workbook = writer.book
    readme_sheet = workbook.add_worksheet('Readme')
    cell_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
    readme_sheet.merge_range('A1:F40', readme_text, cell_format)
    readme_sheet.set_column('A:F', 20)

