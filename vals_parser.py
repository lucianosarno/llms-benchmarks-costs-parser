import requests
from bs4 import BeautifulSoup

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