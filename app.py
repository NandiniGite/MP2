from flask import Flask, render_template, request
import csv
import pytesseract
from PIL import Image
import io
from bs4 import BeautifulSoup

app = Flask(__name__)

# Load dataset from CSV
def load_dataset(csv_file):
    dataset = {}
    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ingredient = row['Ingredients Name'].lower().strip()  # Convert to lowercase and remove leading/trailing whitespace
            natural_artificial = row['Natural/Artificial']
            processed_unprocessed = row['Processed/Unprocessed']
            
            # Check for empty strings and handle accordingly
            natural_artificial = int(natural_artificial) if natural_artificial.isdigit() else 0
            processed_unprocessed = int(processed_unprocessed) if processed_unprocessed.isdigit() else 0
            
            classification = {
                'natural': 'Natural' if natural_artificial == 0 else 'Artificial',
                'artificial': 'Artificial' if natural_artificial == 1 else 'Natural',
                'processed': 'Processed' if processed_unprocessed == 1 else 'Unprocessed'
            }
            dataset[ingredient] = classification
    return dataset

# Function to perform OCR on an image
def perform_ocr(image):
    # Open the image using PIL
    img = Image.open(io.BytesIO(image.read()))
    # Perform OCR on the opened image
    text = pytesseract.image_to_string(img)
    return text

# Function to scrape ingredient information using BeautifulSoup
def scrape_ingredient_info(search_term):
    # Load the HTML content from the file
    with open("sample.html", "r") as f:
        html_content = f.read()

    # Create a BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all <tr> elements
    all_tr = soup.find_all('tr')

    # Flag to check if search term is found
    search_found = False

    # Array to store obtained values
    obtained_values = []

    # Loop through each <tr> element
    for tr in all_tr:
        # Find all <td> elements within the <tr>
        all_td = tr.find_all('td')
        
        # Check if the search term is in any of the <td> elements
        exact_match = False
        for td in all_td:
            if search_term.lower() == td.get_text(strip=True).lower():
                exact_match = True
                break
        
        # If the exact match is found in any <td> element
        if exact_match:
            # Set the flag to True
            search_found = True
            
            # Extract the text from the first <td> element containing the search term
            search_name = search_term
            print("Search Term:", search_term)
            
            # Loop through each <td> element in the same <tr>
            for td in all_td:
                # Get all siblings of the found <td> element
                siblings = td.find_next_siblings()
                for sibling in siblings:
                    # Append the text of the sibling to the array
                    obtained_values.append(sibling.get_text(strip=True))
            
            # Break the loop after finding the search term
            break

    # If search term not found
    if not search_found:
        obtained_values = None

    return obtained_values

# Define route for homepage
@app.route('/')
def home():
    return render_template('index.html')

# Define route for handling image upload and ingredient classification
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"
    
    # List of terms to be ignored (all lowercase)
    ignored_terms = [
        'measure', 'measure', 'energy', 'energy', 'protein',
        'protien', 'total carbohydrate', 'total dietary fibre',
        'total fiber', 'fat', 'cholesterol',
        'calcium', 'iron', 'sodium', 'potassium',
        'phosphorus', 'phosphorous', 'riboflavin', 'niacin',
        'folate'
    ]

    # Perform OCR on the uploaded image
    extracted_text = perform_ocr(file)
    
    # Load dataset
    dataset = load_dataset('ingredients.csv')  # Change the file path
    
    # Extract known ingredients from OCR result and classify them
    unique_ingredients = set()  # Set to store unique ingredients
    ingredients_info = []
    for word in extracted_text.replace(',', ' ').split():  # Replace commas with whitespace and then split
        word = word.strip().lower()  # Convert to lowercase and remove leading/trailing whitespace
        if word in dataset and word not in unique_ingredients:
            # Include ingredient name and classification in the result
            ingredients_info.append({
                'ingredient': word,
                'classification': dataset[word]
            })
            unique_ingredients.add(word)  # Add ingredient to set of unique ingredients
        elif word not in unique_ingredients:
            # Check if the word is in the list of ignored terms
            if word.lower() not in ignored_terms:
                # If ingredient not found in dataset and not in ignored terms, scrape its information
                obtained_values = scrape_ingredient_info(word)
                if obtained_values is not None:
                    ingredients_info.append({
                        'ingredient': word,
                        'info': obtained_values
                    })
                    unique_ingredients.add(word)  # Add ingredient to set of unique ingredients
    
    # Display the matched ingredients and their information to the user
    return render_template('result.html', ingredients_info=ingredients_info)

if __name__ == '__main__':
    app.run(debug=True)
