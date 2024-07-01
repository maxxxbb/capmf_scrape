# install.packages("package") if necessary
library(openxlsx)
library(rvest)
library(httr)
library(tidyverse)

"

Purpose: Scrape Data for NAP Communications and NAP Submissions from the UNFCCC webpage for CAPMF update.


1, Communications

  1. Get list of countries is scraped from the Adaptation Communications Registry
  2. Define function which exctracts relevant information on NAP Communications from country website (luckily they are harmonized)
  3. Loop over list of countries and append row to dataframe
  4. Fill up missing columns
  5. Save final dataframe


2. Submission of NAPs

  1. Extract html tables from https://napcentral.org/submitted-naps and https://napcentral.org/developedcountriesnaps
  2. Merge with Communications sheet and apply


Written by Max Boehringer in June 2024.
"

# 1. DEFINING FUNCTIONS


scrape_country_list <-function(url) {
  "
  Function to extract the List of Countries which have submitted a NAP Communication
  
  Input: URL of NAP page
  
  Output: dataframe containing countrys and respective NAP URLS
  
  "
  # fetch html source code
  webpage_comm <- GET(url)

  # Check if GET request was successful
  if (status_code(webpage_comm) == 200) {
    
    # Parse HTML content
    webpage_content <- read_html(content(webpage_comm, "text"))
    
    # Use CSS selectors to select acr-party-button class - this is where the country names/URLs are stored on website
    country_nodes <- webpage_content %>% 
      html_nodes(".acr-party-button")
    
    # Extract the href attributes (URLs) and text (country names)
    country_urls <- country_nodes %>% html_attr("href")
    country_names <- country_nodes %>% html_text()
    
    # Create df to store data
    country_data <- data.frame(
      country = country_names,
      url = paste0("https://unfccc.int", country_urls),
      stringsAsFactors = FALSE
    )
    
    
    return(country_data)
  
    
  } else {
    print(paste("GET request failed with status code:", status_code(webpage_comm)))
  }
}

extract_country_table_comms <- function(country_url, retries = 2) {
  "
  Function to extract the NAP Communication data directly from the html table
  on the respective country url - UNFCCC Website.
  
  Input: country url: URL of respective country scraped from https://unfccc.int/ACR/

         retries: number of times the scrape attempt should be repeated per country (default = 2)
  
  Output: row to be appended on final dataframe containing Status, Submission Date
          and other info on a country's NAP Communication
  "
  
  for (i in 1:retries) {
    try({
      country_page <- GET(country_url)
      
      # Parse the HTML content
      country_content <- read_html(content(country_page, "text"))
      
      table_data <- NULL
      
      # Try the default table structure
      try({
        table_data <- country_content %>%
          html_node(".view-content .table-responsive table") %>%
          html_table(fill = TRUE)
      }, silent = TRUE)
      
      # If the default approach fails, try the alternate table structure - Ex Canada
      if (is.null(table_data)) {
        try({
          table_data <- country_content %>%
            html_node("table.table-hover.table-striped") %>%
            html_table(fill = TRUE)
          
          # Only keep the first entry per column for the alternate table structure
          table_data <- table_data[1, , drop = FALSE]
        }, silent = TRUE)
      }
      
      # If the data is exctracted return
      if (!is.null(table_data)) {
        return(table_data)
      }
      
      message(paste("Attempt", i, "failed for", country_url))
      
    }, silent = TRUE)
    
    # Wait 5s before trying to call website again 
    Sys.sleep(5)
  }
  
  # If no data for a country is found after retries, return NULL
  message(paste("No table found at", country_url, "after", retries, "retries"))
  return(NULL)
}

get_missing_countries <- function(all_country_data, country_data) {
  "
  Function to detect countries where data was not scraped in the first run
  
  Inputs:  all_country_data : NAPS_COMM data 
           country_data : table of all countries and corresponding urls
  
  Output: missing_countries : list of countries where first iteration of extract_country_table_comms was not successful
  
  "
  missing_countries <- country_data[!(country_data$country %in% all_country_data$`Name of Party`), ]
  return(missing_countries)
}

scrape_nap_comms <- function(NAP_url) {
  "
  
  Function to scrape NAP comm data from the UNFCCC website.
  
  First calls on function get_country_list to retrieve all country URLs.
  Then loops over those urls and fetches the NAP comm information
  (Luckily all are saved in html table objects). Since the Website sometimes
  is not responsive this function also calls on get_missing_countries after the
  first iteration to see which countries data has not yet been retrieved and 
  tries to fill up those missing countries until all data is scraped.The new rows
  - country entries - are appended to the all_country_data dataframe 
  
  Input:
      NAP_url : UNFCCC public registry website
  
  Output:
  
      all_country_data(dataframe): contains the NAP columns : Name of Party , 
                                   Document type and title , source link , version number,
                                   enactment status and year of release.
  
  
  
  
  
  "
  country_data <- scrape_country_list(NAP_url)
  all_country_data <- data.frame()
  
  # Loop over each country and get relevant NAP Comm row
  for (i in 1:nrow(country_data)) {
    country_url <- country_data$url[i]
    print(country_url)
    country_name <- country_data$country[i]
    
    table_data <- extract_country_table_comms(country_url)
    if (!is.null(table_data) && nrow(table_data) > 0) {
      table_data$country <- country_name
      all_country_data <- bind_rows(all_country_data, table_data)
    } else {
      message(paste("No table found for", country_name))
    }
  }
  
  # Rerun the loop with missing countries until no missing countries are left
  repeat {
    missing_countries <- get_missing_countries(all_country_data, country_data)
    if (nrow(missing_countries) == 0) break
    
    for (i in 1:nrow(missing_countries)) {
      country_url <- missing_countries$url[i]
      country_name <- missing_countries$country[i]
      
      table_data <- extract_country_table_comms(country_url)
      if (!is.null(table_data) && nrow(table_data) > 0) {
        table_data$country <- country_name
        all_country_data <- bind_rows(all_country_data, table_data)
      } else {
        message(paste("No table found for", country_name))
      }
    }
  }
  
  return(all_country_data)
}

scrape_submissions <- function(SUB_url) {
  "
  Function to scrape the submissions table from the given URL
  
  Inputs:  
      SUB_url : URL of the webpage containing the submissions table
  
  Output: 
      Submissions : dataframe containing the scraped submissions table
  "
  # Read the webpage
  webpage <- read_html(SUB_url)
  
  # Extract the table without using the first row as the header
  table <- webpage %>%
    html_node("table") %>% # Adjusted to find any table; you can specify a more precise selector if needed
    html_table(fill = TRUE)
  
  if(all(startsWith(names(table), "X"))) {
    table <- table[-1, ]  # Remove the first row
    colnames(table) <- c("No.", "Country", "Region", "National Adaptation Plan", "Date Posted")  # Rename columns
  }
  
  Submissions <- table
  
  return(Submissions)
}

# 2. START SCRAPING - UNFCCC website seems to have some DDOS- attack protection 

# 2.1 Communications (Might have to be restarted once or twice until loop starts running)

NAP_url<- "https://unfccc.int/ACR"
all_country_data <- scrape_nap_comms(NAP_url)

# 2.2 Submissions

SUB_url_developed <- "https://napcentral.org/developedcountriesnaps"
SUB_url_developing <- "https://napcentral.org/submitted-naps"
submissions_developed <- scrape_submissions(SUB_url_developed)
submissions_developing <- scrape_submissions(SUB_url_developing)


# 3. Data Cleaning:

# 3.1 Communications

# Function to split rows- table format on UNFCCC website was inconsistent

split_rows_based_on_spaces <- function(df, threshold = 5) {
" Splitx DataFrame Rows into multiple based on Spaces
  
  This function takes a dataframe and splits its rows into two new rows if any cell
  in the row contains a string with spaces exceeding the specified threshold. 
  Each new row will contain one part of the split string.
  
    Inputs: 
          - df: NAP dataframe with some inconsistent row entries.
        - threshold:  minimum number of consecutive spaces required to split the string. Default is 5.
   
    Output: 
          -dataframe with rows split into two where strings with spaces exceeding the threshold were found.
  "  

  split_row <- function(row) {
    split_detected <- FALSE
    new_rows <- list()
    
    for (col in names(row)) {
      parts <- strsplit(as.character(row[[col]]), sprintf(" {%d,}", threshold))[[1]]
      if (length(parts) > 1) {
        split_detected <- TRUE
        new_rows[[col]] <- parts
      } else {
        new_rows[[col]] <- rep(as.character(row[[col]]), 2)
      }
    }
    
    if (split_detected) {
      # Create two new rows
      new_row_1 <- sapply(names(new_rows), function(col) new_rows[[col]][1])
      new_row_2 <- sapply(names(new_rows), function(col) new_rows[[col]][length(new_rows[[col]])])
      return(rbind(new_row_1, new_row_2))
    } else {
      return(matrix(row, nrow = 1))
    }
  }
  
  split_data <- do.call(rbind, apply(df, 1, split_row))
  return(as.data.frame(split_data, stringsAsFactors = FALSE))
}


all_country_data <- all_country_data %>%
  distinct() %>%
  arrange("Name of Party")

nap_comms <- split_rows_based_on_spaces(all_country_data, threshold = 5)
names(nap_comms)[names(nap_comms) == "Hyperlinks to corresponding documents containing the adaptation communications**"] <- "link"
nap_comms <- nap_comms %>% select(-country)
names(nap_comms)[names(nap_comms) == "Name of Party"] <- "Country"
NAP_comms <- nap_comms %>% mutate(year = format(as.Date(`Submission date`, format = "%d/%m/%Y"), "%Y"))

#3.2 Submissions - concatenate both tables


submissions_developed <- submissions_developed %>%
  mutate(`LDC/SIDS` = NA, Source = "Developed")  %>%
  mutate(`No.` = as.integer(`No.`))

submissions_developing <- submissions_developing %>%
  mutate(Source = "Developing")


#### Fix Paraguay - inconsistent table format

submissions_developing <- submissions_developing[submissions_developing$Country != "Paraguay", ]


new_rows <- data.frame(
  `No.` = c(39,39),
  Country = c("Paraguay", "Paraguay"),
  Region = c("Latin America and the Caribbean", "Latin America and the Caribbean"),
  "LDC/SIDS" = NA,
  `National Adaptation Plan` = c("First NAP Spanish", "Updated NAP Spanish"),
  `Date Posted` = c("May 3, 2020", "July 14, 2022"),
  Source = c("Developing", "Developing"),
  stringsAsFactors = FALSE,
  check.names = FALSE
)

submissions_developing <- rbind(submissions_developing, new_rows)

### Extract year

Submissions <- bind_rows(submissions_developed, submissions_developing) %>%
  select(-`No.`) %>%
  arrange(Country) %>%
  mutate(`Date Posted` = parse_date_time(`Date Posted`, orders = c("dmy", "mdy", "ymd", "d B Y", "B d, Y")),
       Year = year(`Date Posted`))

  




# Save Excel workbook 
wb <- createWorkbook()

# Add a worksheet named 'Communications' and write the NAP_comms dataframe to it
addWorksheet(wb, "Communications")
writeData(wb, "Communications", NAP_comms)


# Add a worksheet named 'Submissions' and write the Submissions dataframe to it
addWorksheet(wb, "Submissions")
writeData(wb, "Submissions", Submissions)

# Save the workbook to a file named 'NAP.xlsx'
saveWorkbook(wb, "\\\\main.oecd.org\\ASgenENV\\ENVINFO\\BACKUP\\STATA\\IPAC\\CAP\\Excel files\\1_RawDataCAP\\2024\\NAP.xlsx", overwrite = TRUE)