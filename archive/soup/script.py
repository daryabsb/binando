import os
import re
import requests
from bs4 import BeautifulSoup

# Define the directory where the HTML file is located
html_file_path = 'soup/coins.html'  # Replace with your HTML file name
output_directory = 'soup/downloaded_files'  # Directory to save the downloaded files
img_directory = 'soup/img'  # Directory containing .svg files to rename



# Ensure the output directory exists
# os.makedirs(output_directory, exist_ok=True)

# Function to rename .svg files in the 'img' directory
def rename_svg_files(directory):
    # Iterate over all files in the directory
    for filename in os.listdir(directory):
        # Check if the file is a .svg file and contains 'XTVC'
        if filename.endswith('.svg') and 'XTVC' in filename:
            # Create the new file name by removing 'XTVC'
            new_filename = filename.replace('XTVC', '')
            old_file_path = os.path.join(directory, filename)
            new_file_path = os.path.join(directory, new_filename)
            
            # Rename the file
            os.rename(old_file_path, new_file_path)
            print(f'Renamed: {filename} -> {new_filename}')

# Read the HTML file
# with open(html_file_path, 'r', encoding='utf-8') as file:
#     html_content = file.read()

# # Parse the HTML content using BeautifulSoup
# soup = BeautifulSoup(html_content, 'html.parser')

# # Define the regex pattern to match the specific links
# pattern = re.compile(r'https://s3-symbol-logo\.tradingview\.com/crypto/XTVC.*?\.svg')

# # Find all links that match the pattern
# links = soup.find_all('a', href=pattern)

# # Loop through the matched links and download the files
# for link in links:
#     url = link['href']
#     # Generate the file name by removing 'XTVC' from the URL
#     file_name = url.split('/')[-1].replace('XTVC', '')
#     file_path = os.path.join(output_directory, file_name)
    
#     # Download the file
#     response = requests.get(url)
#     if response.status_code == 200:
#         with open(file_path, 'wb') as file:
#             file.write(response.content)
#         print(f'Downloaded and saved: {file_name}')
#     else:
#         print(f'Failed to download: {url}')

# print('Download process completed.')

# Call the function to rename .svg files in the 'img' directory
rename_svg_files(img_directory)
print('File renaming process completed.')