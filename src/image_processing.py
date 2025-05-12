from PIL import Image
import numpy as np
from rembg import remove
import requests
from io import BytesIO

def load_image(image_path, remove_white_bg=False, remove_background=False):
    try:
        if image_path.startswith("http://") or image_path.startswith("https://"):
            print(f"Fetching image from URL: {image_path}")
            response = requests.get(image_path, stream=True)
            print(f"Response status code: {response.status_code}")
            if response.status_code != 200:
                raise Exception(f"Failed to fetch image: Status {response.status_code}")
            image = Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            print(f"Loading image from file: {image_path}")
            image = Image.open(image_path).convert("RGBA")

        if "final.png" in image_path.lower():
            image = image.resize((300, 600), Image.LANCZOS)

        if remove_background:
            input_np = np.array(image)
            output_np = remove(input_np)
            image = Image.fromarray(output_np)
            if image.mode != "RGBA" or not any(pixel[3] == 0 for pixel in image.getdata()):
                print(f"Warning: Background removal failed for {image_path}, falling back to white background removal.")
                remove_white_bg = True

        if remove_white_bg:
            datas = image.getdata()
            new_data = []
            for item in datas:
                if item[0] == 255 and item[1] == 255 and item[2] == 255:
                    new_data.append((255, 255, 255, 0))
                else:
                    new_data.append(item)
            image.putdata(new_data)

        return image
    except requests.exceptions.RequestException as e:
        print(f"Request Error loading image from {image_path}: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return None
    except Exception as e:
        print(f"General Error processing image: {e}")
        return None

def optimize_resize(image, target_width, target_height):
    original_width, original_height = image.size
    print(f"Original image dimensions: {original_width}x{original_height}")
    # Constrain to model image size (300x600)
    max_width = 300
    max_height = 600
    target_width = min(target_width, max_width)
    target_height = min(target_height, max_height)
    resized_image = image.resize((target_width, target_height), Image.LANCZOS)
    print(f"Resized image dimensions (constrained): {resized_image.width}x{resized_image.height}")
    return resized_image

def overlay_images(model_img, garment_images, body_shape, selected_type=None):
    print(f"Model image dimensions: {model_img.width}x{model_img.height}")
    temp_img = model_img.copy()

    # Define body shape adjustments
    body_shape_adjustments = {
        "Triangle": {"neck_y_factor": 0.10, "chest_y_factor": 0.17, "waist_y_factor": 0.42, "hip_y_factor": 0.65, "feet_y_factor": 1.0},
        "Hourglass": {"neck_y_factor": 0.05, "chest_y_factor": 0.20, "waist_y_factor": 0.45, "hip_y_factor": 0.70, "feet_y_factor": 1.0},
        "Rectangle": {"neck_y_factor": 0.10, "chest_y_factor": 0.17, "waist_y_factor": 0.42, "hip_y_factor": 0.65, "feet_y_factor": 1.0},
        "Inverted Triangle": {"neck_y_factor": 0.10, "chest_y_factor": 0.17, "waist_y_factor": 0.42, "hip_y_factor": 0.65, "feet_y_factor": 1.0},
        "Apple": {"neck_y_factor": 0.10, "chest_y_factor": 0.17, "waist_y_factor": 0.42, "hip_y_factor": 0.65, "feet_y_factor": 1.0},
        "Shape not classified": {"neck_y_factor": 0.10, "chest_y_factor": 0.17, "waist_y_factor": 0.42, "hip_y_factor": 0.65, "feet_y_factor": 1.0}
    }

    adjustments = body_shape_adjustments.get(body_shape, body_shape_adjustments["Shape not classified"])

    # Calculate silhouette points
    neck_y = int(model_img.height * adjustments["neck_y_factor"])
    chest_y = int(model_img.height * adjustments["chest_y_factor"])
    waist_y = int(model_img.height * adjustments["waist_y_factor"])
    hip_y = int(model_img.height * adjustments["hip_y_factor"])
    feet_y = int(model_img.height * adjustments["feet_y_factor"])

    print(f"Silhouette points - Neck: {neck_y}, Chest: {chest_y}, Waist: {waist_y}, Hips: {hip_y}, Feet: {feet_y}")

    # Define dimensions before using them in garment_positions
    standard_width_tops = model_img.width
    default_top_height = min(waist_y - neck_y + 60, model_img.height - neck_y)
    standard_width_bottoms = model_img.width + 15 # Constrain to silhouette width
    standard_height_bottoms = min(feet_y - waist_y + 80, model_img.height - waist_y)

    # Calculate constrained dress height and width
    dress_height = min(feet_y - neck_y, model_img.height - neck_y)
    standard_width_dresses = model_img.width  # Match silhouette width
    center_x_dresses = model_img.width // 2 - standard_width_dresses // 2

    # Skirt height from waist to feet, width matches silhouette
    skirt_height = min(feet_y - waist_y, model_img.height - waist_y)

    garment_positions = {
        "Tops": (model_img.width // 2 - standard_width_tops // 2, neck_y, standard_width_tops, default_top_height),
        "Pants": (model_img.width // 2 - standard_width_bottoms // 2, waist_y - 40, standard_width_bottoms, standard_height_bottoms),
        "Skirt": (model_img.width // 2 - standard_width_bottoms // 2, waist_y, standard_width_bottoms, skirt_height),  # From waist to feet
        "Dresses": (center_x_dresses, neck_y, standard_width_dresses, dress_height),
        "Anarkali": (model_img.width // 2 - standard_width_dresses // 2, neck_y, standard_width_dresses, dress_height),
        "Kurta": (model_img.width // 2 - standard_width_tops // 2, neck_y, standard_width_tops, default_top_height),
        "Lehenga": (model_img.width // 2 - standard_width_bottoms // 2, waist_y, standard_width_bottoms, skirt_height)
    }

    # Create a local copy of garment_images to avoid modifying the global dict directly
    local_garment_images = garment_images.copy()

    # Manage clothing type conflicts based on selected_type
    if selected_type:
        print(f"Applying conflict resolution for selected type: {selected_type}")
        if selected_type == "Dresses":
            local_garment_images["Tops"] = None
            local_garment_images["Pants"] = None
            local_garment_images["Skirt"] = None
        elif selected_type == "Pants":
            local_garment_images["Skirt"] = None
            local_garment_images["Dresses"] = None
        elif selected_type == "Skirt":
            local_garment_images["Pants"] = None
            local_garment_images["Dresses"] = None
            # Only allow Tops to coexist with Skirt
            if "Tops" in garment_images and garment_images["Tops"] is not None:
                local_garment_images["Tops"] = garment_images["Tops"]
            else:
                local_garment_images["Tops"] = None
        elif selected_type == "Tops":
            local_garment_images["Dresses"] = None
            # Allow Tops + Pants or Tops + Skirt
            if "Pants" in garment_images and garment_images["Pants"] is not None:
                local_garment_images["Pants"] = garment_images["Pants"]
            if "Skirt" in garment_images and garment_images["Skirt"] is not None:
                local_garment_images["Skirt"] = garment_images["Skirt"]
        # Explicitly clear Skirt when Tops is selected unless Tops + Skirt is intended
        if selected_type == "Tops" and "Skirt" in local_garment_images and local_garment_images["Skirt"] is not None and "Tops" not in garment_images:
            local_garment_images["Skirt"] = None

    # Overlay only the remaining non-None images
    for clothing_type, garment_img in local_garment_images.items():
        if garment_img is not None:
            x, y, width, height = garment_positions[clothing_type]
            print(f"Overlaying {clothing_type} at position ({x}, {y}) with size {width}x{height}")
            resized_garment = optimize_resize(garment_img, width, height)
            print(f"Garment image dimensions after resize: {resized_garment.width}x{resized_garment.height}")
            resized_garment = resized_garment.convert("RGBA")  # Ensure RGBA mode
            temp_img.paste(resized_garment, (x, y), resized_garment)  # Use alpha channel
            print(f"Pasted {clothing_type} with alpha: {resized_garment.mode}")

    return temp_img