import os
import requests
from bs4 import BeautifulSoup

# Path to the HTML file
html_file_path = 'soup/table.html'  # Replace with your HTML file name

# Path to the Django static folder for coins
static_coins_folder = os.path.join('static', 'coins')  # Adjust as needed

# Ensure the static coins folder exists
os.makedirs(static_coins_folder, exist_ok=True)

# Read the HTML file
with open(html_file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Find the table
table = soup.find('table', class_='table-Ngq2xrcG')

# Extract headers
headers = [th.text.strip() for th in table.find('thead').find_all('th')]
headers.append('SVG Path')  # Add a new header for the SVG file path

# Extract rows
rows = table.find('tbody').find_all('tr')

# Create a list to store the data
data = []

# Loop through each row and extract data
for row in rows:
    cells = row.find_all('td')
    row_data = {}
    for i, cell in enumerate(cells):
        # Clean up the cell text
        cell_text = cell.text.strip().replace('\u202f', ' ')  # Replace narrow no-break space
        row_data[headers[i]] = cell_text

    # Extract the SVG file URL from the <img> tag
    img_tag = row.find('img', class_='logo-PsAlMQQF')
    if img_tag and 'src' in img_tag.attrs:
        svg_url = img_tag['src']
        # Download the SVG file
        svg_filename = os.path.basename(svg_url)  # Extract the file name from the URL
        svg_file_path = os.path.join(static_coins_folder, svg_filename)
        
        # Download and save the SVG file
        response = requests.get(svg_url)
        if response.status_code == 200:
            with open(svg_file_path, 'wb') as svg_file:
                svg_file.write(response.content)
            print(f"Downloaded and saved: {svg_filename}")
        else:
            print(f"Failed to download: {svg_url}")
            svg_filename = None

        # Add the SVG file path (relative to the static folder) to the row data
        row_data['SVG Path'] = os.path.join('coins', svg_filename) if svg_filename else None
    else:
        row_data['SVG Path'] = None

    data.append(row_data)

# Print the extracted data
for entry in data:
    print(entry)

# Save the data to a file (e.g., JSON)
import json

with open('soup/crypto_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Data saved to crypto_data.json")