from flask import Flask, render_template, request
import csv
import pytesseract
from PIL import Image
import io
import matplotlib.pyplot as plt

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
            if natural_artificial == '':
                natural_artificial = 0
            else:
                natural_artificial = int(natural_artificial)
            
            if processed_unprocessed == '':
                processed_unprocessed = 0
            else:
                processed_unprocessed = int(processed_unprocessed)
            
            classification = {
                'natural': 'Natural' if natural_artificial == 1 else 'Artificial',
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
    
    # Generate pie chart based on the classification
    classification_counts = {'Natural': 0, 'Artificial': 0, 'Processed': 0, 'Unprocessed': 0}
    for ingredient in ingredients_info:
        classification_counts[ingredient['classification']['natural']] += 1
        classification_counts[ingredient['classification']['processed']] += 1
    
    labels = classification_counts.keys()
    sizes = classification_counts.values()
    
    # Plot pie chart
    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Ingredient Classification')
    plt.savefig('static/pie_chart.png')  # Save pie chart as image
    plt.close()
    
    # Display the matched ingredients and their information to the user
    return render_template('result.html', ingredients_info=ingredients_info)

if __name__ == '__main__':
    app.run(debug=True)
