from flask import render_template, request, session, redirect, url_for, current_app, jsonify
from models import db, User, UserResponse
import pandas as pd
import os
import re
import time
from src.image_processing import load_image, overlay_images
from src.ui import update_image
from src.clothing import get_clothing_recommendations, on_clothing_selected, selected_garment_images

def init_user_routes(app):
    @app.route('/dashboard/<int:user_id>', methods=["GET", "POST"])
    def dashboard(user_id):
        with current_app.app_context():
            if 'user_id' not in session or session['user_id'] != user_id:
                return redirect(url_for('login', next=request.url))
            user = User.query.get(user_id)
            response = UserResponse.query.filter_by(user_id=user_id).first()
            body_shape = response.body_shape if response else None
            recommendations = {'Tops': [], 'Pants': [], 'Dresses': [], 'Skirt': []}
            clothing_names = {'Tops': [], 'Pants': [], 'Dresses': [], 'Skirt': []}
            combined_recommendations = {'Tops': [], 'Pants': [], 'Dresses': [], 'Skirt': []}

            if body_shape:
                from src.clothing import get_clothing_recommendations
                clothing_items = get_clothing_recommendations(body_shape)
                print(f"Body Shape: {body_shape}")
                print(f"Clothing Recommendations: {clothing_items}")
                csv_path = r"C:\Users\Hp\Desktop\Activeee\data\csv local - Sheet1-1.csv"
                print(f"Attempting to load CSV from: {csv_path}")
                if not os.path.exists(csv_path):
                    print(f"CSV file does not exist at: {csv_path}")
                    return render_template(
                        'user_dashboard.html',
                        user_id=user_id,
                        body_shape=body_shape,
                        recommendations=combined_recommendations,
                        silhouette_image=None
                    )
                try:
                    df = pd.read_csv(csv_path)
                    print(f"CSV loaded successfully, rows: {len(df)}")
                    print(f"CSV Columns: {df.columns.tolist()}")
                    print(f"CSV Body Shapes: {df['Body Shape'].unique().tolist()}")
                    print(f"CSV Clothing Types: {df['Clothing Type'].unique().tolist()}")
                    df['Clothing Type'] = df['Clothing Type'].str.capitalize()
                    df['Clothing Type'] = df['Clothing Type'].replace({
                        'Top': 'Tops',
                        'Pant': 'Pants',
                        'Dress': 'Dresses',
                        'Skirt': 'Skirt',
                        'Dressess': 'Dresses'
                    })
                    df['Body Shape'] = df['Body Shape'].str.capitalize()
                    matching_items = df[df['Body Shape'] == body_shape.capitalize()]
                    print(f"Matching Items for {body_shape}: {matching_items[['Clothing Type', 'Clothing Item', 'Image Path']].to_dict('records')}")
                    project_root = r"C:\Users\Hp\Desktop\Activeee"
                    for _, row in matching_items.iterrows():
                        clothing_type = row['Clothing Type']
                        image_path_raw = row['Image Path'].strip()
                        filename = os.path.basename(image_path_raw)
                        filename = filename.replace('dressess', 'dresses')
                        file_path = os.path.normpath(os.path.join(project_root, image_path_raw))
                        print(f"Checking file: {file_path}")
                        if os.path.exists(file_path):
                            image_path = f"/{image_path_raw}"
                            if clothing_type in recommendations:
                                recommendations[clothing_type].append(image_path)
                                clothing_names[clothing_type].append(row['Clothing Item'])
                                combined_recommendations[clothing_type].append((image_path, row['Clothing Item']))
                        else:
                            print(f"Image not found: {file_path}")
                    print(f"Final Recommendations: {recommendations}")
                    print(f"Clothing Names: {clothing_names}")
                    print(f"Combined Recommendations: {combined_recommendations}")
                except Exception as e:
                    print(f"Error loading CSV: {e}")

            # Pre-load silhouette at 300x600 for initial display
            silhouette_image = None
            if body_shape:
                body_shape_to_silhouette = {
                    "Triangle": os.path.join(app.config['IMAGES_FOLDER'], "Pear final.png"),
                    "Apple": os.path.join(app.config['IMAGES_FOLDER'], "Apple final.png"),
                    "Hourglass": os.path.join(app.config['IMAGES_FOLDER'], "Hourglass final.png"),
                    "Rectangle": os.path.join(app.config['IMAGES_FOLDER'], "Rectangle final.png"),
                    "Inverted Triangle": os.path.join(app.config['IMAGES_FOLDER'], "Triangle final.png")
                }
                model_image_path = body_shape_to_silhouette.get(body_shape, os.path.join(app.config['IMAGES_FOLDER'], "Rectangle final.png"))
                silhouette_image = load_image(model_image_path)
                if silhouette_image:
                    results_path = os.path.join(project_root, 'static', 'results')
                    os.makedirs(results_path, exist_ok=True)
                    silhouette_image.save(os.path.join(results_path, "silhouette.png"))
                    silhouette_image = f"/static/results/silhouette.png?{int(time.time())}"
                else:
                    print(f"Silhouette not loaded: {model_image_path}")

            # Handle POST for Try On
            if request.method == "POST":
                action = request.form.get('action')
                print(f"Received POST action: {action}")
                if action == 'try_on':
                    clothing_type = request.form.get('clothing_type')
                    clothing_item = request.form.get('clothing_item')
                    print(f"Try On - clothing_type: {clothing_type}, clothing_item: {clothing_item}")
                    if clothing_type and clothing_item:
                        # Load silhouette
                        body_shape_to_silhouette = {
                            "Triangle": os.path.join(app.config['IMAGES_FOLDER'], "Pear final.png"),
                            "Apple": os.path.join(app.config['IMAGES_FOLDER'], "Apple final.png"),
                            "Hourglass": os.path.join(app.config['IMAGES_FOLDER'], "Hourglass final.png"),
                            "Rectangle": os.path.join(app.config['IMAGES_FOLDER'], "Rectangle final.png"),
                            "Inverted Triangle": os.path.join(app.config['IMAGES_FOLDER'], "Triangle final.png")
                        }
                        model_image_path = body_shape_to_silhouette.get(body_shape, os.path.join(app.config['IMAGES_FOLDER'], "Rectangle final.png"))
                        print(f"Loading silhouette from: {model_image_path}")
                        model_image = load_image(model_image_path)
                        if model_image:
                            print(f"Silhouette loaded successfully")
                            # Select clothing image
                            project_root = r"C:\Users\Hp\Desktop\Activeee"
                            csv_path = r"C:\Users\Hp\Desktop\Activeee\data\csv local - Sheet1-1.csv"
                            df = pd.read_csv(csv_path)
                            print(f"Querying DataFrame for: clothing_type={clothing_type}, clothing_item={clothing_item}, body_shape={body_shape}")
                            matching_rows = df[(df['Clothing Type'].str.capitalize() == clothing_type.capitalize()) & 
                                             (df['Clothing Item'].str.strip() == clothing_item.strip()) & 
                                             (df['Body Shape'].str.capitalize() == body_shape.capitalize())]
                            print(f"Matching rows: {matching_rows}")
                            if not matching_rows.empty:
                                matching_row = matching_rows.iloc[0]
                                image_path_raw = matching_row['Image Path'].strip()
                                clothing_image_path = os.path.normpath(os.path.join(project_root, image_path_raw))
                                print(f"Loading clothing image from: {clothing_image_path}")
                                clothing_image = load_image(clothing_image_path, remove_background=True)
                                if clothing_image:
                                    print(f"Clothing image loaded successfully")
                                    on_clothing_selected(clothing_type, clothing_item, body_shape)
                                    # Use selected_garment_images to persist and manage multiple garments
                                    selected_garment_images[clothing_type] = clothing_image
                                    result_image = overlay_images(model_image, selected_garment_images, body_shape, selected_type=clothing_type)
                                    if result_image:
                                        results_path = os.path.join(project_root, 'static', 'results')
                                        os.makedirs(results_path, exist_ok=True)
                                        result_image.save(os.path.join(results_path, "result.png"))
                                        print(f"Overlay saved to: {os.path.join(results_path, 'result.png')}")
                                        return jsonify({'status': 'success', 'image_url': f"/static/results/result.png?{int(time.time())}"})
                                    else:
                                        print("Overlay failed")
                                        return jsonify({'status': 'error', 'message': 'Overlay processing failed'})
                                else:
                                    print(f"Clothing image not loaded: {clothing_image_path}")
                                    return jsonify({'status': 'error', 'message': f'Clothing image not found: {clothing_image_path}'})
                            else:
                                print(f"No matching row found for clothing_type={clothing_type}, clothing_item={clothing_item}, body_shape={body_shape}")
                                return jsonify({'status': 'error', 'message': 'No matching clothing item found in CSV'})
                        else:
                            print(f"Silhouette not loaded: {model_image_path}")
                            return jsonify({'status': 'error', 'message': f'Silhouette not found: {model_image_path}'})
                    else:
                        return jsonify({'status': 'error', 'message': 'Missing clothing type or item'})
                elif action == 'upload':
                    if 'clothing_image' in request.files:
                        file = request.files['clothing_image']
                        clothing_type = request.form.get('clothing_type').capitalize()  # Normalize to uppercase
                        if file.filename != '':
                            base_dir = os.path.abspath(os.path.dirname(__file__))
                            temp_path = os.path.join(base_dir, 'static', 'uploads', f'custom_{int(time.time())}.png')
                            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                            file.save(temp_path)
                            garment_image = load_image(temp_path, remove_background=True)
                            if garment_image:
                                # Clear other garment types to process only the uploaded image
                                selected_garment_images.clear()
                                selected_garment_images[clothing_type] = garment_image
                                print(f"Selected garment images after upload: {selected_garment_images}")
                                body_shape_to_silhouette = {
                                    "Triangle": os.path.join(app.config['IMAGES_FOLDER'], "Pear final.png"),
                                    "Apple": os.path.join(app.config['IMAGES_FOLDER'], "Apple final.png"),
                                    "Hourglass": os.path.join(app.config['IMAGES_FOLDER'], "Hourglass final.png"),
                                    "Rectangle": os.path.join(app.config['IMAGES_FOLDER'], "Rectangle final.png"),
                                    "Inverted Triangle": os.path.join(app.config['IMAGES_FOLDER'], "Triangle final.png")
                                }
                                model_image_path = body_shape_to_silhouette.get(body_shape, os.path.join(app.config['IMAGES_FOLDER'], "Rectangle final.png"))
                                model_image = load_image(model_image_path)
                                if model_image:
                                    # Ensure update_image returns the overlaid image
                                    result_image = update_image(model_image, body_shape, clothing_type)
                                    if result_image:
                                        project_root = r"C:\Users\Hp\Desktop\Activeee"
                                        results_path = os.path.join(project_root, 'static', 'results')
                                        os.makedirs(results_path, exist_ok=True)
                                        result_image.save(os.path.join(results_path, "result.png"))
                                        print(f"Overlaid image saved to {os.path.join(results_path, 'result.png')}")
                                        timestamp = int(time.time())
                                        temp_path = os.path.join(base_dir, 'static', 'uploads', f'custom_{timestamp}.png')
                                        original_image_url = f"/static/uploads/custom_{timestamp}.png"  # Use the temp_path as a relative URL
                                        return jsonify({'status': 'success', 'image_url': f"/static/results/result.png?{timestamp}", 'original_image_url': original_image_url})
                                    else:
                                        print("Overlay failed in update_image")
                                        return jsonify({'status': 'error', 'message': 'Overlay processing failed'})
                                else:
                                    return jsonify({'status': 'error', 'message': f'Silhouette not found: {model_image_path}'})
                            else:
                                return jsonify({'status': 'error', 'message': 'Failed to process uploaded image'})
                        else:
                            return jsonify({'status': 'error', 'message': 'No valid file uploaded'})
                    else:
                        return jsonify({'status': 'error', 'message': 'No file uploaded'})

            return render_template(
                'user_dashboard.html',
                user_id=user_id,
                body_shape=body_shape,
                recommendations=combined_recommendations,
                silhouette_image=silhouette_image
            )

if __name__ == "__main__":
    pass