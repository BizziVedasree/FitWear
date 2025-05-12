from .image_processing import overlay_images
import os
from .clothing import on_clothing_selected, selected_garment_images, clothing_df

def update_image(model_image, body_shape, selected_type=None):
    print(f"Updating image for body shape: {body_shape}")
    print(f"Selected garment images: {selected_garment_images}")
    print(f"Model image dimensions: {model_image.size if model_image else 'None'}")

    # Use the full selected_garment_images dictionary
    if any(img is not None for img in selected_garment_images.values()):  # Check if any garment is loaded
        print(f"Overlaying {body_shape} with garment images")
        overlaid_image = overlay_images(model_image, selected_garment_images, body_shape, selected_type)  # Pass selected_type
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Integration'))  # Changed to Integration
        results_path = os.path.join(base_dir, "static", "results")
        os.makedirs(results_path, exist_ok=True)
        overlaid_image.save(os.path.join(results_path, "result.png"))
        print(f"Overlaid image saved to {os.path.join(results_path, 'result.png')}")
        return overlaid_image  # Return the overlaid image
    else:
        print("No garment image selected, saving model image without overlay")
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Integration'))  # Changed to Integration
        results_path = os.path.join(base_dir, "static", "results")
        os.makedirs(results_path, exist_ok=True)
        model_image.save(os.path.join(results_path, "result.png"))
        print(f"Model image saved to {os.path.join(results_path, 'result.png')} without overlay")
        return model_image  # Return the model image if no overlay

def display_recommendations(recommendations):
    formatted_recommendations = {}
    for category, items in recommendations.items():
        if items:  # Only include categories with items
            formatted_recommendations[category] = items
    return formatted_recommendations  # Return a dictionary for web rendering