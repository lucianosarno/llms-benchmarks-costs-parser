import requests
from bs4 import BeautifulSoup
import json # Import json library for saving data
import re # Import regex for potentially cleaning accuracy data
from datetime import datetime # For adding a timestamp

url_principal = 'https://www.vals.ai/benchmarks'
try:
    response = requests.get(url_principal)
    response.raise_for_status() # Throw error for bad codes (4xx ou 5xx)
    html_content = response.text
except requests.exceptions.RequestException as e:
    print(f"Error accessing the main page: {e}")
    exit() # End script in case of error

print(f"html_content: {html_content}...")  # Print first 1000 characters for brevity
soup = BeautifulSoup(html_content, 'html.parser')
# print(f"soup (first 1000 chars of string representation): {str(soup)[:1000]}...")
benchmark_links = set() # Using 'set' to avoid duplicates
base_url_prefix = 'https://www.vals.ai/benchmarks'

# Find all links in the page
all_links = soup.find_all('a', href=True)
# print(f"all_links: {all_links[:1000]}...")  # Print first 1000 characters for brevity

for link in all_links:
    href = link['href']
    # Check if the link starts with the base URL prefix AND it's not the main page
    # Adding a small check to ensure we don't pick the main URL again
    if href.__contains__('/benchmarks/') and href != base_url_prefix and href != base_url_prefix + '/':
        # If the link is relative, we would need to construct the full URL
        # However, in this case, all links are absolute.
        full_url = href
        benchmark_links.add(full_url)

# Convert the list if wanted, but set is already good to avoid duplicates
list_benchmark_links = list(benchmark_links)

print(f"Found {len(list_benchmark_links)} benchmarks links:")
for link in list_benchmark_links:
    print(link)

print("-" * 20)

# --- Data Extraction from Benchmark Pages ---
all_benchmark_data = []

for benchmark_url in list_benchmark_links:
    print(f"\nProcessing benchmark page: {benchmark_url}")

    try:
        response = requests.get(benchmark_url)
        response.raise_for_status() # Throw error for bad codes
        benchmark_html = response.text
    except requests.exceptions.RequestException as e:
        print(f"Error accessing {benchmark_url}: {e}")
        continue # Skip to the next URL if there's an error

    benchmark_soup = BeautifulSoup(benchmark_html, 'html.parser')

    # Extract benchmark identifier from URL (e.g., 'legal-qa' from '.../benchmarks/legal-qa')
    benchmark_id = benchmark_url.split('/')[-1]
    if not benchmark_id: # Handle potential trailing slash
         benchmark_id = benchmark_url.split('/')[-2]
    # print(f"  Benchmark ID: {benchmark_id}") # Already printed above

    models_on_this_page = []

    # Find the container that holds the list of model rows (the <a> tags with class="block")
    # Based on the HTML, the <a> tags are direct children of a <div>
    # which is a sibling to the header <div>, both within a parent div.
    # A robust way is to find the first <a> with class 'block' and get its parent.
    first_model_link = benchmark_soup.find('a', class_='block')

    model_entries_container = None
    if first_model_link:
        model_entries_container = first_model_link.parent # The parent of the first <a> should be the container

    if model_entries_container:
        # Find all individual model entries (the <a> tags)
        model_entries = model_entries_container.find_all('a', class_='block')

        print(f"  Found {len(model_entries)} model entries on {benchmark_id}.")

        for model_link in model_entries:
            try:
                # Data is inside the first div within the <a> tag
                # Using the class name from the provided HTML snippet
                data_div = model_link.find('div', class_='grid grid-cols-[2.5fr_1fr_1fr_1fr] py-3 bg-white border-b border-zinc-700 hover:bg-zinc-100 transition-all duration-150')

                if data_div:
                    # Locate the sub-sections within the data_div
                    # The structure is:
                    # div (col 1: Rank, Company Logo, Model Name)
                    # p (col 2: Accuracy)
                    # p (col 3: Cost Input / Cost Output)
                    # p (col 4: Latency)

                    # Find Column 1 div
                    col1_div = data_div.find('div', class_='flex flex-row gap-2 pl-3') # The first div child

                    # Find the direct p tags for Accuracy, Costs, Latency
                    # Use recursive=False to only get direct children
                    p_tags = data_div.find_all('p', recursive=False)

                    if col1_div and len(p_tags) >= 3: # Ensure required elements are found
                        # Extract Company Name from SVG src (from Column 1 div)
                        company_img_tag = col1_div.find('img')
                        company_name = 'N/A'
                        if company_img_tag and company_img_tag.get('src'):
                            img_src = company_img_tag['src']
                            # Extract filename without extension, e.g., 'OpenAI' from '/Icons/OpenAI.svg'
                            filename = img_src.split('/')[-1]
                            company_name = filename.split('.')[0] if '.' in filename else filename
                            # Clean up common patterns like '-Instruct', and format nicely
                            company_name = company_name.replace('-Instruct', '').replace('-', ' ').strip().title()
                            if company_name.lower() == 'xai': # Special case for xAI
                                company_name = 'xAI'


                        # Extract Model Name (from Column 1 div)
                        # It's the p tag inside col1_div with specific classes
                        model_name_tag = col1_div.find('p', class_='text-slate900 text-xs md:text-xs lg:text-sm gap-1 flex-row items-center justify-center tracking-0.2')
                        model_name = model_name_tag.text.strip() if model_name_tag else 'N/A'

                        # Extract Accuracy (from the first direct p tag)
                        accuracy_tag = p_tags[0]
                        accuracy_text = accuracy_tag.get_text(strip=True) if accuracy_tag else ''
                        # The accuracy value is usually a number followed by %. Use regex to be robust.
                        accuracy_match = re.search(r'\d+\.?\d*%', accuracy_text)
                        accuracy = accuracy_match.group(0) if accuracy_match else accuracy_text # Fallback if regex fails


                        # Extract Costs (from the second direct p tag)
                        costs_tag = p_tags[1]
                        costs_text = costs_tag.text.strip() if costs_tag else 'N/A / N/A'
                        cost_parts = costs_text.split('/')
                        cost_input = cost_parts[0].strip() if len(cost_parts) > 0 else 'N/A'
                        cost_output = cost_parts[1].strip() if len(cost_parts) > 1 else 'N/A'

                        # Extract Latency (from the third direct p tag)
                        latency_tag = p_tags[2]
                        latency = latency_tag.text.strip() if latency_tag else 'N/A'


                        # Create a dictionary for this model
                        model_data = {
                            'benchmark': benchmark_id, # Add the benchmark identifier
                            'model': model_name,
                            'company': company_name,
                            'accuracy': accuracy,
                            'cost_input': cost_input,
                            'cost_output': cost_output,
                            'latency': latency
                        }
                        models_on_this_page.append(model_data)

                    else:
                         # Optional: print warning if structure doesn't match expected
                         # print(f"    Warning: Could not find expected structure within data_div for a model entry on {benchmark_url}")
                         # if data_div: print(data_div.prettify())
                         pass # Skip this entry if structure is unexpected


            except Exception as e:
                # Catch any errors during parsing a single model entry
                print(f"    Error parsing model entry on {benchmark_url}: {e}")
                # Continue to the next model entry even if one fails

    else:
        print(f"  Could not find the model entries container (first <a>.block parent) on {benchmark_url}")


    # Add the extracted models from this page to the main list
    all_benchmark_data.extend(models_on_this_page)

# --- Save Data to JSON ---
print("\nFinished processing all benchmark pages.")
print(f"Collected data for {len(all_benchmark_data)} model entries in total.")

# Add a timestamp to the data for context
data_with_timestamp = {
    'timestamp_utc': datetime.utcnow().isoformat(), # Use UTC timestamp
    'benchmarks': all_benchmark_data
}

json_filename = 'benchmarks_data.json'

try:
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data_with_timestamp, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved data to {json_filename}")
except IOError as e:
    print(f"Error saving data to {json_filename}: {e}")

print("-" * 20)
print("Script finished.")