import os
from body_shape import classify_body_shape
from image_processing import load_image, overlay_images
from clothing import get_clothing_recommendations, on_clothing_selected
from ui import update_image, display_recommendations

def process_inputs(bust, waist, hips, high_hip, height_range, size):
    body_shape = classify_body_shape(bust, waist, high_hip, hips)
    print(f"\nYour classified body shape: {body_shape}")

    # Set base directory to project root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    body_shape_to_silhouette = {
        "Triangle": os.path.join(base_dir, "images", "Pear final.png"),
        "Apple": os.path.join(base_dir, "images", "Apple final.png"),
        "Hourglass": os.path.join(base_dir, "images", "Hourglass final.png"),
        "Pear": os.path.join(base_dir, "images", "Pear final.png"),
        "Rectangle": os.path.join(base_dir, "images", "Rectangle final.png"),
        "Inverted Triangle": os.path.join(base_dir, "images", "Triangle final.png"),
        "Shape not classified": os.path.join(base_dir, "images", "Rectangle final.png")
    }
    model_image_path = body_shape_to_silhouette.get(body_shape, os.path.join(base_dir, "images", "Rectangle final.png"))
    model_image = load_image(model_image_path)
    if model_image is None:
        print(f"Error: Could not load model image at {model_image_path}. Exiting.")
        return None, None, None
    print(f"\nYour model_image_path: {model_image_path}")

    results_path = os.path.join(base_dir, "static", "results")
    if os.path.exists(results_path) and not os.path.isdir(results_path):
        print(f"Error: {results_path} exists as a file, not a directory. Renaming it.")
        os.rename(results_path, results_path + "_old")
    os.makedirs(results_path, exist_ok=True)

    model_image.save(os.path.join(results_path, "result.png"))
    print("Initial silhouette saved to static/results/result.png")

    clothing_recommendations = get_clothing_recommendations(body_shape)
    display_recommendations(clothing_recommendations)
    return body_shape, model_image, clothing_recommendations

def main():
    try:
        bust = float(input("Enter Bust (in inches): "))
        waist = float(input("Enter Waist (in inches): "))
        hips = float(input("Enter Hips (in inches): "))
        high_hip = float(input("Enter High Hip (in inches): "))
        height_range = input("Enter your height range (e.g., 5-5.5): ")
        size = input("Enter your size (e.g., M): ")
    except ValueError:
        print("Error: Please enter valid numeric values for measurements.")
        return

    body_shape, model_image, clothing_recommendations = process_inputs(bust, waist, hips, high_hip, height_range, size)
    if body_shape is None or model_image is None:
        return

    while True:
        print("\nSelect a clothing item to try on (e.g., 'Blouse' for Tops):")
        for clothing_type, items in clothing_recommendations.items():
            if len(items) > 0:
                print(f"{clothing_type}: {', '.join(items)}")
                selected_item = input(f"Enter {clothing_type} item (or 'quit' to exit): ")
                if selected_item.lower() == 'quit':
                    break
                if selected_item:
                    on_clothing_selected(clothing_type, selected_item, body_shape)
                    update_image(model_image, body_shape)
        if selected_item.lower() == 'quit':
            break

if __name__ == "__main__":
    main()