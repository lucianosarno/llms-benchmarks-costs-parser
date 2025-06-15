import requests # Used for making HTTP requests to fetch web pages
from bs4 import BeautifulSoup # Used for parsing HTML content
import json # Used for saving the extracted data into a JSON file
import re # Used for regular expressions, specifically for cleaning the accuracy value
from datetime import datetime # Used for adding a timestamp to the output data

# --- Configuration ---
site_base_url = 'https://www.vals.ai' # Base URL of the website
url_main_benchmarks_page = site_base_url + '/benchmarks' # URL of the main benchmarks listing page

# --- Access Main Benchmarks Page ---
# Attempt to fetch the content of the main benchmarks page
try:
    response = requests.get(url_main_benchmarks_page)
    response.raise_for_status() # Check for bad status codes (400s or 500s) and raise an exception
    html_content_main_page = response.text # Get the HTML content as text
except requests.exceptions.RequestException as e:
    # If there's an error accessing the page, print the error and exit
    print(f"Error accessing the main page: {e}")
    exit()

# --- Parse Main Page and Collect Benchmark Links ---
# Parse the HTML content of the main page using BeautifulSoup
soup_main_page = BeautifulSoup(html_content_main_page, 'html.parser')

# Set to store unique benchmark URLs
benchmark_links = set()

# Find all <a> tags with an href attribute on the main page
all_links_on_main_page = soup_main_page.find_all('a', href=True)

# Iterate through all found links
for link in all_links_on_main_page:
    href = link['href'] # Get the value of the href attribute

    # Check if the href is a relative path starting with '/benchmarks/'
    # and is not the main benchmarks page itself
    if href and href.startswith('/benchmarks/') and href.strip('/') != 'benchmarks':
        full_url = site_base_url + href # Construct the absolute URL
        benchmark_links.add(full_url) # Add the full URL to the set

    # Also check for absolute links starting with the main page URL prefix
    # This handles cases where links might already be absolute
    elif href and href.startswith(url_main_benchmarks_page + '/') and href.strip('/') != url_main_benchmarks_page.strip('/'):
        benchmark_links.add(href) # Add the absolute URL to the set

# Convert the set of links to a list
list_benchmark_links = list(benchmark_links)

# Print the collected benchmark links
print(f"Found {len(list_benchmark_links)} benchmark links:")
for link in list_benchmark_links:
    print(link)

print("-" * 20)

# --- Data Extraction from Individual Benchmark Pages ---
# List to store all extracted model data from all benchmarks
all_benchmark_data = []

# Loop through each collected benchmark URL
for benchmark_url_full in list_benchmark_links:
    print(f"\nProcessing benchmark page: {benchmark_url_full}")

    # Attempt to fetch the content of the current benchmark page
    try:
        response = requests.get(benchmark_url_full)
        response.raise_for_status() # Check for bad status codes
        benchmark_html = response.text # Get the HTML content
    except requests.exceptions.RequestException as e:
        # If error, print error and skip to the next URL
        print(f"Error accessing {benchmark_url_full}: {e}")
        continue

    # Parse the HTML content of the benchmark page
    benchmark_soup = BeautifulSoup(benchmark_html, 'html.parser')

    # Extract the benchmark identifier from the URL (e.g., 'legal-qa')
    benchmark_id = benchmark_url_full.split('/')[-1]
    if not benchmark_id: # Handle potential trailing slash in the URL
        benchmark_id = benchmark_url_full.split('/')[-2]
    # print(f"  Benchmark ID: {benchmark_id}") # Commented out to avoid double print

    # List to hold data for models found on the current page
    models_on_this_page = []

    # Find the main HTML element that contains the list of model entries.
    # Based on inspection, each model entry is an <a> tag with class 'block',
    # and these <a> tags are direct children of a <div>. We find the container
    # by locating the first model <a> tag and getting its parent.
    first_model_link = benchmark_soup.find('a', class_='block')

    model_entries_container = None
    if first_model_link:
        model_entries_container = first_model_link.parent # The parent div containing all model links

    # If the container is found
    if model_entries_container:
        # Find all individual model entry <a> tags within the container
        model_entries = model_entries_container.find_all('a', class_='block')

        print(f"  Found {len(model_entries)} model entries on {benchmark_id}.")

        # Loop through each individual model entry link
        for model_link in model_entries:
            try:
                # Find the <div> within the <a> tag that holds the structured data for the model row
                # Using the specific class name identified from HTML inspection
                data_div = model_link.find('div', class_='grid grid-cols-[2.5fr_1fr_1fr_1fr] py-3 bg-white border-b border-zinc-700 hover:bg-zinc-100 transition-all duration-150')

                # If the data div is found
                if data_div:
                    # The data (Accuracy, Costs, Latency) are in direct <p> tags following the first <div>.
                    # The first <div> contains the Rank, Company Logo, and Model Name.
                    # Find the first column <div> that contains logo and model name
                    col1_div = data_div.find('div', class_='flex flex-row gap-2 pl-3')

                    # Find all direct child <p> tags within the data_div (these hold Accuracy, Costs, Latency)
                    p_tags = data_div.find_all('p', recursive=False)

                    # Ensure we found the necessary elements before attempting extraction
                    if col1_div and len(p_tags) >= 3:
                        # Extract Company Name from the src attribute of the <img> tag in the first column div
                        company_img_tag = col1_div.find('img')
                        company_name = 'N/A' # Default value
                        if company_img_tag and company_img_tag.get('src'):
                            img_src = company_img_tag['src']
                            # Extract the filename from the source path (e.g., 'OpenAI.svg' from '/Icons/OpenAI.svg')
                            filename = img_src.split('/')[-1]
                            # Extract the company name from the filename (e.g., 'OpenAI' from 'OpenAI.svg')
                            company_name = filename.split('.')[0] if '.' in filename else filename
                            # Clean up the name and format it (e.g., 'xAI' from 'xAI', 'Meta' from 'Meta-Llama')
                            company_name = company_name.replace('-Instruct', '').replace('-', ' ').strip().title()
                            if company_name.lower() == 'xai': # Correct capitalization for xAI
                                company_name = 'xAI'

                        # Extract the Model Name from the specific <p> tag in the first column div
                        model_name_tag = col1_div.find('p', class_='text-slate900 text-xs md:text-xs lg:text-sm gap-1 flex-row items-center justify-center tracking-0.2')
                        model_name = model_name_tag.text.strip() if model_name_tag else 'N/A' # Extract text or use default


                        # Extract Accuracy from the first direct <p> tag
                        accuracy_tag = p_tags[0]
                        accuracy_text = accuracy_tag.get_text(strip=True) if accuracy_tag else ''
                        # Use regex to find the percentage value, which is more reliable than just stripping text
                        accuracy_match = re.search(r'\d+\.?\d*%', accuracy_text)
                        accuracy = accuracy_match.group(0) if accuracy_match else accuracy_text # Use regex match or full text
                        accuracy_number_string = accuracy.replace('%', '')
                        try:
                            accuracy = float(accuracy_number_string)
                        except ValueError:
                            print(f"Warning: Could not convert '{accuracy_number_string}' to a number.")
                            accuracy = None                       

                        # Extract Costs (Input/Output) from the second direct <p> tag
                        costs_tag = p_tags[1]
                        costs_text = costs_tag.text.strip() if costs_tag else 'N/A / N/A'
                        # Split the text by '/' to separate input and output costs
                        cost_parts = costs_text.split('/')
                        cost_input = cost_parts[0].strip() if len(cost_parts) > 0 else 'N/A'
                        cost_output = cost_parts[1].strip() if len(cost_parts) > 1 else 'N/A'

                        # Extract Latency from the third direct <p> tag
                        latency_tag = p_tags[2]
                        latency = latency_tag.text.strip() if latency_tag else 'N/A' # Extract text or use default
                        latency_number_string = latency.replace(' s', '')
                        try:
                            latency = float(latency_number_string)
                        except ValueError:
                            print(f"Warning: Could not convert '{latency_number_string}' to a number.")
                            latency = None   

                        # Create a dictionary for the current model's data
                        model_data = {
                            'benchmark': benchmark_id, # Include the benchmark identifier for context
                            'model': model_name,
                            'company': company_name,
                            'accuracy': accuracy,
                            'cost_input': cost_input,
                            'cost_output': cost_output,
                            'latency': latency
                        }
                        # Add the model's data to the list for this page
                        models_on_this_page.append(model_data)

                    # Optional: Print a warning if the expected structure isn't found for a model row
                    # else:
                    #      print(f"    Warning: Could not find expected structure within data_div for a model entry on {benchmark_url_full}")


            except Exception as e:
                # Catch any errors during the parsing of a single model entry
                print(f"    Error parsing model entry on {benchmark_url_full}: {e}")
                # Continue to the next model entry even if one fails

    # If the container for model entries was not found on the page
    else:
        print(f"  Could not find the model entries container on {benchmark_url_full}")


    # Add all collected model data from the current page to the main list
    all_benchmark_data.extend(models_on_this_page)

# --- Save Collected Data to JSON File ---
print("\nFinished processing all benchmark pages.")
print(f"Collected data for {len(all_benchmark_data)} model entries in total.")

# Prepare the final data structure including a timestamp
data_with_timestamp = {
    'timestamp_utc': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), # Add current UTC timestamp
    'benchmarks': all_benchmark_data # Include the list of all extracted model data
}

# Define the output JSON filename
json_filename = 'benchmarks_data.json'

# Attempt to write the data to the JSON file
try:
    with open(json_filename, 'w', encoding='utf-8') as f:
        # Dump the Python dictionary to a JSON file, ensuring non-ASCII chars are handled
        # and formatting with indentation for readability
        json.dump(data_with_timestamp, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved data to {json_filename}")
except IOError as e:
    # If there's an error writing the file, print the error
    print(f"Error saving data to {json_filename}: {e}")

print("-" * 20)
print("Script finished.")
