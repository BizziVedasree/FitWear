import pandas as pd
import os
from .image_processing import load_image

# Ensure clothing_df is initialized at module import
print("Initializing clothing.py module...")  # Debug start
base_dir = os.path.abspath(os.path.dirname(__file__) + '/..')  # Up to performance/ from src/
print(f"Base directory set to: {base_dir}")  # Debug base_dir
csv_path = os.path.join(base_dir, "data", "csv local - Sheet1-1.csv")
clothing_df = None
print(f"Attempting to load CSV from: {csv_path}")  # Debug path
try:
    with open(csv_path, 'r') as f:  # Test if file is readable
        clothing_df = pd.read_csv(csv_path)
    print(f"Clothing DataFrame initialized with {len(clothing_df)} rows from {csv_path}")
except FileNotFoundError:
    print(f"Error: CSV file not found at {csv_path}. Please verify the file exists at {base_dir}\\data\\.")
except PermissionError:
    print(f"Error: Permission denied to access {csv_path}. Check file permissions.")
except pd.errors.EmptyDataError:
    print(f"Error: CSV file at {csv_path} is empty.")
except Exception as e:
    print(f"Unexpected error initializing clothing_df: {e}")

# Dictionary to store selected garment images
selected_garment_images = {
    "Tops": None,
    "Pants": None,
    "Skirt": None,
    "Dresses": None,
    "Anarkali": None,
    "Kurta": None,
    "Lehenga": None
}

def get_clothing_recommendations(body_shape):
    recommendations = {
        "Tops": [],
        "Pants": [],
        "Dresses": [],
        "Skirt": []
    }
    if clothing_df is not None:
        filtered_df = clothing_df[clothing_df["Body Shape"].str.lower() == body_shape.lower()]
        for _, row in filtered_df.iterrows():
            category = row["Clothing Type"]
            if category in recommendations:
                recommendations[category].append(row["Clothing Item"])
    else:
        print("clothing_df is not initialized")
    return recommendations

def on_clothing_selected(clothing_type, clothing_item, body_shape):
    global selected_garment_images
    if clothing_df is not None:
        query = clothing_df[
            (clothing_df["Body Shape"].str.lower() == body_shape.lower()) &
            (clothing_df["Clothing Type"] == clothing_type) &
            (clothing_df["Clothing Item"] == clothing_item)
        ]
        print(f"Querying clothing_df for {body_shape}, {clothing_type}, {clothing_item}: {query}")
        
        if not query.empty:
            image_path = query["Image Path"].iloc[0]
            print(f"Image Path is {image_path}")
            
            # Use global base_dir and append static
            global base_dir
            static_dir = os.path.join(base_dir, "static")
            full_path = os.path.abspath(os.path.join(static_dir, image_path.replace('\\', '/').replace('major images', 'major_images')))
            print(f"Attempting to load image from: {full_path}")
            
            garment_image = load_image(full_path, remove_white_bg=False, remove_background=True)
            if garment_image is None:
                print(f"Failed to load image for {clothing_type}: {clothing_item}")
            else:
                selected_garment_images[clothing_type] = garment_image
                print(f"Successfully loaded {clothing_type}: {clothing_item}")
        else:
            print(f"No matching clothing item found for {body_shape}, {clothing_type}, {clothing_item}")
    else:
        print("clothing_df is not initialized")

if __name__ == "__main__":
    pass