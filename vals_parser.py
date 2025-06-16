import requests # Library for making HTTP requests
from bs4 import BeautifulSoup # Library for parsing HTML content
import json # Library for working with JSON data
import re # Library for using regular expressions
from datetime import datetime # Library for getting current date and time
from selenium import webdriver # Library for browser automation
from selenium.webdriver.chrome.service import Service # Service class for Chrome driver
import time # Library for time-related functions (like pauses)
from selenium.webdriver.common.by import By # Class for locating elements by strategy

# --- Configuration ---
site_base_url = 'https://www.vals.ai' # Base URL of the target website
url_main_benchmarks_page = site_base_url + '/benchmarks' # URL for the main benchmarks listing
chromedriver_path = '/opt/chromedriver-linux64/chromedriver' # Path to the Chrome WebDriver executable

# Initialize Selenium WebDriver service
chrome_service = Service(executable_path=chromedriver_path)
# Initialize WebDriver instance
driver = webdriver.Chrome(service=chrome_service)

# --- Access Main Benchmarks Page ---
# Fetch the HTML content of the main benchmarks page using requests
try:
    response = requests.get(url_main_benchmarks_page)
    # Raise an exception for bad status codes (4xx or 5xx)
    response.raise_for_status()
    # Get the page content as text
    html_content_main_page = response.text
# Handle potential request errors (network issues, bad URL, etc.)
except requests.exceptions.RequestException as e:
    print(f"Error accessing the main page: {e}")
    exit() # Exit the script if the main page cannot be accessed

# --- Parse Main Page and Collect Benchmark Links ---
# Parse the HTML content using BeautifulSoup
soup_main_page = BeautifulSoup(html_content_main_page, 'html.parser')

# Use a set to store unique benchmark URLs found on the main page
benchmark_links = set()

# Find all anchor tags (<a>) with an href attribute
all_links_on_main_page = soup_main_page.find_all('a', href=True)

# Iterate through each found link
for link in all_links_on_main_page:
    href = link['href'] # Get the link's URL

    # Check if the link is a relative path pointing to a specific benchmark page
    if href and href.startswith('/benchmarks/') and href.strip('/') != 'benchmarks':
        # Construct the full absolute URL
        full_url = site_base_url + href
        benchmark_links.add(full_url) # Add the full URL to the set

    # Also check for absolute links that start with the main benchmarks URL prefix
    elif href and href.startswith(url_main_benchmarks_page + '/') and href.strip('/') != url_main_benchmarks_page.strip('/'):
        benchmark_links.add(href) # Add the absolute URL to the set

# Convert the set of unique links to a list for ordered processing
list_benchmark_links = list(benchmark_links)

# Print the total number of unique benchmark links found
print(f"Found {len(list_benchmark_links)} benchmark links:")
# Print each collected link
for link in list_benchmark_links:
    print(link)

print("-" * 20)

# --- Data Extraction from Individual Benchmark Pages ---
# List to store extracted data for all models across all benchmarks
all_benchmark_data = []

# Loop through each collected benchmark URL
for benchmark_url_full in list_benchmark_links:
    print(f"\nProcessing benchmark page: {benchmark_url_full}")

    # Use Selenium to access the page to handle potential dynamic content loading
    try:
        driver.get(benchmark_url_full)
        time.sleep(3) # Wait for the page to load dynamic content

        # Attempt to click the 'Accuracy' sort button if present
        try:
            accuracy_sort_btn= driver.find_element(By.XPATH, '//button[contains(text(), "Accuracy")]')
            accuracy_sort_btn.click()
            time.sleep(1) # Short pause after clicking
        except:
            # If button not found, print a warning and continue without sorting
            print("Accuracy sort button not found, continuing without sorting.")

        # Attempt to click the 'See More' button if present to load all entries
        try:
            see_more_btn = driver.find_element(By.XPATH, '//button[starts-with(text(), "See ")]')
            see_more_btn.click()
            time.sleep(1) # Short pause after clicking
        except:
            # If button not found, it might not exist or all entries are already visible
            pass

        # Get the page source *after* potential dynamic content loading by Selenium
        benchmark_html = driver.page_source
        # Note: The original requests.get call here is redundant after using Selenium
        # response = requests.get(benchmark_url_full)
        # response.raise_for_status() # Check for bad status codes - This won't reflect dynamic content
        # benchmark_html = response.text # This gets the initial HTML, not post-JS rendering

    # Handle potential errors during page access with Selenium
    except Exception as e: # Catching a general exception for Selenium/page loading issues
        print(f"Error accessing {benchmark_url_full} with Selenium: {e}")
        continue # Skip to the next URL if the current page fails to load

    # Parse the dynamically loaded HTML content using BeautifulSoup
    benchmark_soup = BeautifulSoup(benchmark_html, 'html.parser')

    # Extract the unique identifier for the current benchmark from the URL
    benchmark_id = benchmark_url_full.split('/')[-1]
    if not benchmark_id: # Handle cases with trailing slashes
        benchmark_id = benchmark_url_full.split('/')[-2]

    # List to hold data for models found on the current benchmark page
    models_on_this_page = []

    # Find the HTML container element that holds the list of model entries.
    # This is typically the parent of the first model entry link.
    first_model_link = benchmark_soup.find('a', class_='block')
    model_entries_container = None
    if first_model_link:
        model_entries_container = first_model_link.parent

    # If the container element is found
    if model_entries_container:
        # Find all individual model entry links (<a> tags) within the container
        model_entries = model_entries_container.find_all('a', class_='block')

        print(f"  Found {len(model_entries)} model entries on {benchmark_id}.")

        # --- Extract Benchmark Group (Task Type) ---
        benchmark_group = "N/A" # Default value if not found
        try:
            # Locate the element containing the 'Task Type:' label
            task_type_p = benchmark_soup.find('p', text='Task Type:')
            if task_type_p:
                # Navigate up to the container holding the label and the value
                task_type_container = task_type_p.parent
                if task_type_container:
                    # Find the specific element containing the group name (based on structure inspection)
                    group_p_tag = task_type_container.find('p', class_='text-zinc-900 text-sm tracking-0.2')
                    if group_p_tag:
                        benchmark_group = group_p_tag.text.strip() # Extract and clean the text
        except Exception as e:
            # Handle potential errors during group extraction
            print(f"  Error extracting benchmark group on {benchmark_url_full}: {e}")

        # Print extracted benchmark details
        print(f"  Benchmark Group: {benchmark_group}")
        print(f"  Benchmark ID: {benchmark_id}")

        # Loop through each individual model entry element found
        for model_link in model_entries:
            try:
                # Find the div that structures the data for a single model row
                data_div = model_link.find('div', class_='grid grid-cols-[2.5fr_1fr_1fr_1fr] py-3 bg-white border-b border-zinc-700 hover:bg-zinc-100 transition-all duration-150')

                # If the data structure div is found
                if data_div:
                    # Find the first column div containing the company logo and model name
                    col1_div = data_div.find('div', class_='flex flex-row gap-2 pl-3')

                    # Find all direct paragraph tags (<p>) within the data_div (contain Accuracy, Costs, Latency)
                    p_tags = data_div.find_all('p', recursive=False)

                    # Proceed only if the essential elements are found
                    if col1_div and len(p_tags) >= 3:
                        # Extract Company Name from the image source within the first column
                        company_img_tag = col1_div.find('img')
                        company_name = 'N/A'
                        if company_img_tag and company_img_tag.get('src'):
                            img_src = company_img_tag['src']
                            # Extract and format the company name from the image filename
                            filename = img_src.split('/')[-1]
                            company_name = filename.split('.')[0] if '.' in filename else filename
                            company_name = company_name.replace('-Instruct', '').replace('-', ' ').strip().title()
                            if company_name.lower() == 'xai':
                                company_name = 'xAI'

                        # Extract the Model Name from its specific paragraph tag within the first column
                        model_name_tag = col1_div.find('p', class_='text-slate900 text-xs md:text-xs lg:text-sm gap-1 flex-row items-center justify-center tracking-0.2')
                        model_name = model_name_tag.text.strip() if model_name_tag else 'N/A'

                        # Extract Accuracy from the first data paragraph tag
                        accuracy_tag = p_tags[0]
                        accuracy_text = accuracy_tag.get_text(strip=True) if accuracy_tag else ''
                        # Use regex to find and extract the percentage value
                        accuracy_match = re.search(r'\d+\.?\d*%', accuracy_text)
                        accuracy_str = accuracy_match.group(0) if accuracy_match else accuracy_text
                        accuracy_number_string = accuracy_str.replace('%', '')
                        # Convert the extracted number string to a float
                        try:
                            accuracy = float(accuracy_number_string)
                        except ValueError:
                            # Handle cases where conversion fails
                            print(f"Warning: Could not convert '{accuracy_number_string}' to a number for accuracy.")
                            accuracy = None

                        # Extract Costs (Input/Output) from the second data paragraph tag
                        costs_tag = p_tags[1]
                        costs_text = costs_tag.text.strip() if costs_tag else 'N/A / N/A'
                        # Split the text to separate input and output costs
                        cost_parts = costs_text.split('/')
                        cost_input = cost_parts[0].strip() if len(cost_parts) > 0 else 'N/A'
                        cost_output = cost_parts[1].strip() if len(cost_parts) > 1 else 'N/A'

                        # Extract Latency from the third data paragraph tag
                        latency_tag = p_tags[2]
                        latency_text = latency_tag.text.strip() if latency_tag else 'N/A'
                        latency_number_string = latency_text.replace(' s', '')
                         # Convert the extracted number string to a float
                        try:
                            latency = float(latency_number_string)
                        except ValueError:
                            # Handle cases where conversion fails
                            print(f"Warning: Could not convert '{latency_number_string}' to a number for latency.")
                            latency = None

                        # Compile the extracted data into a dictionary for the current model
                        model_data = {
                            'benchmark': benchmark_id,
                            'benchmark_group': benchmark_group,
                            'model': model_name,
                            'company': company_name,
                            'accuracy': accuracy,
                            'cost_input': cost_input,
                            'cost_output': cost_output,
                            'latency': latency
                        }
                        # Add the model's data to the list for this page
                        models_on_this_page.append(model_data)

            # Catch any errors that occur during the processing of a single model entry
            except Exception as e:
                print(f"    Error parsing model entry on {benchmark_url_full}: {e}")
                # Continue processing other model entries even if one fails

    # If the container for model entries was not found on the page
    else:
        print(f"  Could not find the model entries container on {benchmark_url_full}")

    # Add all collected model data from the current page to the main list
    all_benchmark_data.extend(models_on_this_page)

# --- Save Collected Data to JSON File ---
print("\nFinished processing all benchmark pages.")
print(f"Collected data for {len(all_benchmark_data)} model entries in total.")

# Prepare the final data structure including a timestamp for when the data was collected
data_with_timestamp = {
    'timestamp_utc': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), # Add current UTC timestamp
    'benchmarks': all_benchmark_data # Include the list of all extracted model data
}

# Define the output JSON filename
json_filename = 'benchmarks_data.json'

# Attempt to write the collected data to a JSON file
try:
    with open(json_filename, 'w', encoding='utf-8') as f:
        # Write the dictionary to a JSON file, ensuring proper encoding and formatting
        json.dump(data_with_timestamp, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved data to {json_filename}")
# Handle potential file writing errors
except IOError as e:
    print(f"Error saving data to {json_filename}: {e}")

print("-" * 20)
print("Script finished.")

# Close the Selenium browser instance
driver.quit()