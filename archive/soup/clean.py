import json
import re
import os

# Path to the input JSON file
input_json_file = 'soup/crypto_data.json'  # Replace with your JSON file name

# Path to the output JSON file
output_json_file = 'soup/cleaned_crypto_data.json'

# Function to clean up keys
def clean_key(key):
    # Remove spaces, convert to lowercase, and replace spaces with underscores
    key = key.lower().replace(' ', '_')
    # Remove special characters (e.g., '%', '\n')
    key = re.sub(r'[^a-zA-Z0-9_]', '', key)
    return key

# Function to clean up values
def clean_value(value):
    if isinstance(value, str):
        # Remove newlines and extra spaces
        value = re.sub(r'\s+', ' ', value).strip()
        # Convert numeric values (e.g., "83,956.98 USD" -> 83956.98)
        if re.match(r'^-?\d+(,\d+)*(\.\d+)?\s*[A-Za-z]*$', value):
            value = value.replace(',', '')  # Remove commas
            value = re.sub(r'[^0-9.-]', '', value)  # Remove non-numeric characters
            if '.' in value:
                return float(value)  # Convert to float
            else:
                return int(value)  # Convert to int
    return value

# Function to extract the ticker from the SVG filename
def extract_ticker(svg_path):
    if not svg_path:  # Handle None or empty string
        return None
    # Extract the filename from the path
    filename = os.path.basename(svg_path)
    # Extract the ticker (part after 'XTVC' and before '.svg')
    match = re.search(r'XTVC(.*?)\.svg', filename)
    if match:
        return match.group(1)
    return None

# Read the data from the input JSON file
with open(input_json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Clean up the data
cleaned_data = []
for entry in data:
    cleaned_entry = {}
    for key, value in entry.items():
        cleaned_key = clean_key(key)
        cleaned_value = clean_value(value)
        cleaned_entry[cleaned_key] = cleaned_value

    # Extract the ticker from the SVG filename in the svg_path field
    svg_path = entry.get('SVG Path', '')  # Default to empty string if key is missing
    ticker = extract_ticker(svg_path)
    cleaned_entry['ticker'] = ticker

    cleaned_data.append(cleaned_entry)

# Save the cleaned data to the output JSON file
with open(output_json_file, 'w', encoding='utf-8') as f:
    json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

print(f"Cleaned data saved to {output_json_file}")