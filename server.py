import http.server
import socketserver
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse
from main import process_inputs
from clothing import on_clothing_selected, selected_garment_images, clothing_df
from ui import update_image
from image_processing import load_image
import time
import requests
import base64
import json
import os
import csv

PORT = 8000
body_shape = None
model_image = None

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send_head(self):
        f = super().send_head()
        if self.path.startswith('/static/'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        return f

    def do_GET(self):
        if self.path.startswith('/proxy-image'):
            query = urlparse(self.path).query
            params = parse_qs(query)
            image_url = params.get('url', [''])[0]
            if image_url:
                try:
                    print(f"Fetching image from: {image_url}")
                    response = requests.get(image_url, stream=True, allow_redirects=True)
                    print(f"Response status code: {response.status_code}")
                    if response.status_code != 200:
                        self.send_error(HTTPStatus.BAD_REQUEST, f"Failed to fetch image: Status {response.status_code}")
                        return
                    
                    content_type = response.headers.get('Content-Type', 'image/png')
                    print(f"Content-Type: {content_type}")
                    
                    image_data = response.content
                    print(f"Image data length: {len(image_data)} bytes")
                    
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                    print(f"Base64 image length: {len(base64_image)}")
                    
                    response_data = {
                        'contentType': content_type,
                        'base64Image': base64_image
                    }
                    self.send_response(HTTPStatus.OK)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                except Exception as e:
                    print(f"Error fetching image: {str(e)}")
                    self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Error fetching image: {str(e)}")
            else:
                self.send_error(HTTPStatus.BAD_REQUEST, "No image URL provided")
            return

        if self.path == '/':
            self.path = '/static/index.html'
        elif self.path == '/contact.html':
            self.path = '/static/contact.html'
        elif self.path == '/about.html':
            self.path = '/static/about.html'
        elif self.path == '/know-more.html':
            self.path = '/static/know-more.html'

        try:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        except ConnectionResetError as e:
            print(f"ConnectionResetError occurred: {str(e)}")
            return

    def do_POST(self):
        global body_shape, model_image
        if self.path == '/upload':
            content_length = int(self.headers['Content-Length'])
            boundary = self.headers['Content-Type'].split('boundary=')[1].encode()
            form_data = self.rfile.read(content_length)

            parts = form_data.split(b'--' + boundary)
            clothing_type = None
            clothing_image = None
            params = {}

            for part in parts:
                if b'Content-Disposition' in part:
                    if b'name="clothing_type"' in part:
                        clothing_type = part.split(b'\r\n\r\n')[1].split(b'\r\n')[0].decode()
                    elif b'name="clothing_image"' in part:
                        clothing_image = part.split(b'\r\n\r\n')[1].split(b'\r\n--')[0]
                    elif b'name="' in part:
                        name = part.split(b'name="')[1].split(b'"')[0].decode()
                        value = part.split(b'\r\n\r\n')[1].split(b'\r\n')[0].decode()
                        params[name] = value

            if not clothing_type or not clothing_image:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing clothing type or image")
                return

            temp_image_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', f'custom_{int(time.time())}.png')
            os.makedirs(os.path.dirname(temp_image_path), exist_ok=True)
            with open(temp_image_path, 'wb') as f:
                f.write(clothing_image)

            garment_image = load_image(temp_image_path, remove_white_bg=False, remove_background=True)
            if garment_image is None:
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to process uploaded image")
                return

            selected_garment_images[clothing_type] = garment_image
            update_image(model_image, body_shape)

            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {
                'status': 'success',
                'image_url': f"/static/results/result.png?{int(time.time())}"
            }
            self.wfile.write(json.dumps(response_data).encode())
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = parse_qs(post_data)

        print("Received POST data:", params)

        try:
            bust = float(params.get('bust', [''])[0])
            waist = float(params.get('waist', [''])[0])
            hips = float(params.get('hips', [''])[0])
            high_hip = float(params.get('high_hip', [''])[0])
            height_range = params.get('height_range', [''])[0]
            size = params.get('size', [''])[0].upper()
            clothing_type = params.get('clothing_type', [''])[0]
            clothing_item = params.get('clothing_item', [''])[0]
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid numeric input")
            return

        body_shape, model_image, clothing_recommendations = process_inputs(bust, waist, hips, high_hip, height_range, size)
        print(f"Clothing recommendations for {body_shape}: {clothing_recommendations}")
        if body_shape is None or model_image is None:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to process inputs")
            return
        print(f"Classified body shape: {body_shape}")

        if clothing_type and clothing_item:
            on_clothing_selected(clothing_type, clothing_item, body_shape)
            update_image(model_image, body_shape,clothing_type)
            print(f"Updated with {clothing_type}: {clothing_item}")

        # Read clothing recommendations from CSV (normalize paths)
        recommendations = {
            "Tops": [],
            "Pants": [],
            "Dresses": [],
            "Skirt": []
        }
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        csv_path = os.path.join(base_dir, "data", "csv local - Sheet1-1.csv")
        try:
            with open(csv_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                #print(f"CSV Headers: {reader.fieldnames}")
                for row in reader:
                    #print(f"Processing row: Body Shape={row['Body Shape']}, Clothing Type={row['Clothing Type']}, Image Path={row['Image Path']}, Raw Data={row}")
                    if row["Body Shape"].strip().lower() == body_shape.strip().lower():
                    #if row["Body Shape"].lower() == body_shape.lower():
                        category = row["Clothing Type"]
                        image_path = row["Image Path"]  # e.g., major images\hourglass\tops\sweatheart.png
                        # Normalize path: replace backslashes with forward slashes and space with underscore
                        normalized_path = image_path.replace('\\', '/').replace('major images', 'major_images')
                        local_url = f"/static/{normalized_path}"  # e.g., /static/major_images/hourglass/tops/sweatheart.png
                        if category in recommendations:
                            recommendations[category].append({
                                "url": local_url,
                                "item": row["Clothing Item"]
                            })
                        else:
                            print(f"Warning: Unknown category {category} for body shape {body_shape}")
        except FileNotFoundError:
            print(f"Error: {csv_path} not found.")
        except Exception as e:
            print(f"Error reading CSV: {e}")

        # Generate HTML for Recommended Clothing
        recommended_html = ""
        if not recommendations:
            recommended_html = "<p>No clothing recommendations available for this body shape.</p>"
        else:
            for category, items in recommendations.items():
                if items:
                    recommended_html += f'<div class="clothing-category"><h4>{category}</h4><div class="clothing-items">'
                    for item in items:
                        recommended_html += f'<div class="clothing-item"><img src="{item["url"]}" alt="{item["item"]}" class="clothing-image" data-clothing-type="{category}" data-clothing-item="{item["item"]}"><button class="try-on-btn" data-clothing-type="{category}" data-clothing-item="{item["item"]}">Try On</button><p>{item["item"]}</p></div>'
                    recommended_html += '</div></div>'

        # Hardcoded "To Avoid" Section
        to_avoid_html = ""
        if body_shape == "Hourglass":
            to_avoid_html = """
            <div class="clothing-category"><h4>Tops</h4><div class="clothing-items"><div class="clothing-item"><p>Boxy Shirts</p></div></div></div>
            <div class="clothing-category"><h4>Pants</h4><div class="clothing-items"><div class="clothing-item"><p>Baggy Pants</p></div></div></div>
            <div class="clothing-category"><h4>Dresses</h4><div class="clothing-items"><div class="clothing-item"><p>Shapeless Dresses</p></div></div></div>
            """
        elif body_shape == "Rectangle":
            to_avoid_html = """
            <div class="clothing-category"><h4>Tops</h4><div class="clothing-items"><div class="clothing-item"><p>Tight Crop Tops</p></div></div></div>
            <div class="clothing-category"><h4>Pants</h4><div class="clothing-items"><div class="clothing-item"><p>Skinny Jeans</p></div></div></div>
            <div class="clothing-category"><h4>Dresses</h4><div class="clothing-items"><div class="clothing-item"><p>Bodycon Dresses</p></div></div></div>
            """
        elif body_shape == "Inverted Triangle":
            to_avoid_html = """
            <div class="clothing-category"><h4>Tops</h4><div class="clothing-items"><div class="clothing-item"><p>Shoulder Pads</p></div></div></div>
            <div class="clothing-category"><h4>Pants</h4><div class="clothing-items"><div class="clothing-item"><p>Tapered Pants</p></div></div></div>
            <div class="clothing-category"><h4>Dresses</h4><div class="clothing-items"><div class="clothing-item"><p>Halter Dresses</p></div></div></div>
            """
        elif body_shape == "Apple":
            to_avoid_html = """
            <div class="clothing-category"><h4>Tops</h4><div class="clothing-items"><div class="clothing-item"><p>Tight Fitted Tops</p></div></div></div>
            <div class="clothing-category"><h4>Pants</h4><div class="clothing-items"><div class="clothing-item"><p>Low-Rise Jeans</p></div></div></div>
            <div class="clothing-category"><h4>Dresses</h4><div class="clothing-items"><div class="clothing-item"><p>Clingy Dresses</p></div></div></div>
            """
        elif body_shape == "Triangle":
            to_avoid_html = """
            <div class="clothing-category"><h4>Tops</h4><div class="clothing-items"><div class="clothing-item"><p>Off-Shoulder Tops</p></div></div></div>
            <div class="clothing-category"><h4>Pants</h4><div class="clothing-items"><div class="clothing-item"><p>Skinny Jeans</p></div></div></div>
            <div class="clothing-category"><h4>Dresses</h4><div class="clothing-items"><div class="clothing-item"><p>Tight Mini Dresses</p></div></div></div>
            """
        else:
            to_avoid_html = "<p>No specific clothing items to avoid for this body shape.</p>"

        # Hardcoded "Own Your Look" Sections
        tops_html = ""
        pants_html = ""
        if body_shape == "Hourglass":
            tops_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Fitted Tops</li>
                    <li>Wrap Tops</li>
                    <li>Peplum Tops</li>
                </ul>
                <p><strong>Necklines:</strong></p>
                <ul>
                    <li>V-Neck</li>
                    <li>Sweetheart Neck</li>
                    <li>Deep Scoop Neck</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Waist-Length</li>
                    <li>Hip-Length</li>
                </ul>
                <p><strong>Sleeves:</strong></p>
                <ul>
                    <li>Cap Sleeves</li>
                    <li>Three-Quarter Sleeves</li>
                    <li>Flutter Sleeves</li>
                </ul>
                <p><strong>*AVOID:</strong> Boxy tops that hide your curves, oversized shirts that add bulk, and high necklines that shorten the torso.</p>
            </div>
            """
            pants_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>High-Waisted Jeans</li>
                    <li>Bootcut Pants</li>
                    <li>Flared Pants</li>
                </ul>
                <p><strong>Fit:</strong></p>
                <ul>
                    <li>Slim Fit</li>
                    <li>Straight Fit</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Full Length</li>
                    <li>Ankle Length</li>
                </ul>
                <p><strong>*AVOID:</strong> Baggy pants that hide your shape, low-rise jeans that disrupt your proportions, and overly tight leggings that unbalance your silhouette.</p>
            </div>
            """
        elif body_shape == "Rectangle":
            tops_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Wrap Tops</li>
                    <li>Belted Tops</li>
                    <li>Ruffled Blouses</li>
                </ul>
                <p><strong>Necklines:</strong></p>
                <ul>
                    <li>V-Neck</li>
                    <li>Scoop Neck</li>
                    <li>Boat Neck</li>
                    <li>Off the Shoulder</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Hip Length</li>
                    <li>Slightly Cropped</li>
                </ul>
                <p><strong>Sleeves:</strong></p>
                <ul>
                    <li>Bell Sleeves</li>
                    <li>Cap Sleeves</li>
                    <li>Flutter Sleeves</li>
                </ul>
                <p><strong>*AVOID:</strong> High necklines like turtlenecks that make the torso look boxy, shapeless tops that lack definition, and tops with bust embellishments that emphasize a lack of curves.</p>
            </div>
            """
            pants_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Flared Jeans</li>
                    <li>Wide-Leg Pants</li>
                    <li>High-Waisted Trousers</li>
                </ul>
                <p><strong>Fit:</strong></p>
                <ul>
                    <li>Relaxed Fit</li>
                    <li>Straight Fit</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Full Length</li>
                    <li>Cropped</li>
                </ul>
                <p><strong>*AVOID:</strong> Skinny jeans that emphasize a straight silhouette, low-rise pants that shorten the torso, and overly tight fits that lack volume.</p>
            </div>
            """
        elif body_shape == "Inverted Triangle":
            tops_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Peplum Tops</li>
                    <li>Wrap Tops</li>
                    <li>Flowy Blouses</li>
                </ul>
                <p><strong>Necklines:</strong></p>
                <ul>
                    <li>V-Neck</li>
                    <li>Scoop Neck</li>
                    <li>Deep U-Neck</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Hip Length</li>
                    <li>Tunic Length</li>
                </ul>
                <p><strong>Sleeves:</strong></p>
                <ul>
                    <li>Sleeveless</li>
                    <li>Flutter Sleeves</li>
                    <li>Long Sleeves</li>
                </ul>
                <p><strong>*AVOID:</strong> Shoulder pads that exaggerate your broad shoulders, halter tops that draw attention to the upper body, and boat necklines that widen the shoulders.</p>
            </div>
            """
            pants_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Wide-Leg Pants</li>
                    <li>Flared Jeans</li>
                    <li>Palazzo Pants</li>
                </ul>
                <p><strong>Fit:</strong></p>
                <ul>
                    <li>Relaxed Fit</li>
                    <li>Bootcut</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Full Length</li>
                    <li>Ankle Length</li>
                </ul>
                <p><strong>*AVOID:</strong> Tapered pants that make the hips look narrower, skinny jeans that unbalance your proportions, and low-rise pants that shorten the torso.</p>
            </div>
            """
        elif body_shape == "Apple":
            tops_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Empire Waist Tops</li>
                    <li>Tunics</li>
                    <li>Flowy Blouses</li>
                </ul>
                <p><strong>Necklines:</strong></p>
                <ul>
                    <li>V-Neck</li>
                    <li>Deep Scoop Neck</li>
                    <li>Wrap Neck</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Hip Length</li>
                    <li>Tunic Length</li>
                </ul>
                <p><strong>Sleeves:</strong></p>
                <ul>
                    <li>Three-Quarter Sleeves</li>
                    <li>Flutter Sleeves</li>
                    <li>Long Sleeves</li>
                </ul>
                <p><strong>*AVOID:</strong> Tight fitted tops that cling to the midsection, cropped tops that expose the waist, and high necklines that shorten the torso.</p>
            </div>
            """
            pants_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Straight-Leg Pants</li>
                    <li>Bootcut Jeans</li>
                    <li>High-Waisted Trousers</li>
                </ul>
                <p><strong>Fit:</strong></p>
                <ul>
                    <li>Relaxed Fit</li>
                    <li>Slim Fit</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Full Length</li>
                    <li>Ankle Length</li>
                </ul>
                <p><strong>*AVOID:</strong> Low-rise jeans that emphasize the midsection, skinny jeans that cling to the legs, and overly tight fits that unbalance the silhouette.</p>
            </div>
            """
        elif body_shape == "Triangle":
            tops_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Boat Neck Tops</li>
                    <li>Off-Shoulder Tops</li>
                    <li>Ruffled Blouses</li>
                </ul>
                <p><strong>Necklines:</strong></p>
                <ul>
                    <li>Boat Neck</li>
                    <li>Square Neck</li>
                    <li>Off the Shoulder</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Waist-Length</li>
                    <li>Slightly Cropped</li>
                </ul>
                <p><strong>Sleeves:</strong></p>
                <ul>
                    <li>Puff Sleeves</li>
                    <li>Bell Sleeves</li>
                    <li>Cap Sleeves</li>
                </ul>
                <p><strong>*AVOID:</strong> Tight tops that emphasize the narrower upper body, V-necks that narrow the shoulders, and sleeveless tops that lack volume.</p>
            </div>
            """
            pants_html = """
            <div class="own-your-look-category">
                <p><strong>Styles:</strong></p>
                <ul>
                    <li>Straight-Leg Pants</li>
                    <li>Bootcut Jeans</li>
                    <li>A-Line Skirts (if applicable)</li>
                </ul>
                <p><strong>Fit:</strong></p>
                <ul>
                    <li>Slim Fit</li>
                    <li>Relaxed Fit</li>
                </ul>
                <p><strong>Length:</strong></p>
                <ul>
                    <li>Full Length</li>
                    <li>Ankle Length</li>
                </ul>
                <p><strong>*AVOID:</strong> Skinny jeans that emphasize the hips, low-rise pants that shorten the torso, and overly tight fits that highlight the lower body.</p>
            </div>
            """
        else:
            tops_html = "<p>No specific styling tips available for tops.</p>"
            pants_html = "<p>No specific styling tips available for pants.</p>"

        if clothing_type and clothing_item:
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {
                'status': 'success',
                'image_url': f"/static/results/result.png?{int(time.time())}"
            }
            self.wfile.write(json.dumps(response_data).encode())
            return

        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        html_response = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Fitwear - Results</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <header>
                <nav>
                    <div class="logo">Fitwear</div>
                    <ul class="nav-links">
                        <li><a href="/">Home</a></li>
                        <li><a href="/know-more.html">Know More</a></li>
                        <li><a href="/contact.html">Contact</a></li>
                        <li><a href="/about.html">About Us</a></li>
                    </ul>
                </nav>
            </header>

            <section id="results">
                <h2>Your Body Shape: {body_shape}</h2>
                <div class="result-image">
                    <img src="/static/results/result.png?{int(time.time())}" alt="Model Image">
                </div>

                <h3>Recommended Clothing</h3>
                <div id="recommended-clothing">
                    {recommended_html}
                </div>

                <h3>Clothing to Avoid</h3>
                <div id="to-avoid">
                    {to_avoid_html}
                </div>

                <h3>Own Your Look</h3>
                <div id="own-your-look">
                    <div class="own-your-look-section">
                        <h4>Tops</h4>
                        {tops_html}
                    </div>
                    <div class="own-your-look-section">
                        <h4>Pants</h4>
                        {pants_html}
                    </div>
                </div>

                <h3>Try On Your Own Clothing</h3>
                <form id="upload-form" enctype="multipart/form-data" method="POST" action="/upload">
                    <label for="clothing_type">Clothing Type:</label>
                    <select id="clothing_type" name="clothing_type" required>
                        <option value="Tops">Tops</option>
                        <option value="Pants">Pants</option>
                        <option value="Dresses">Dresses</option>
                        <option value="Skirt">Skirt</option>
                    </select>
                    <label for="clothing_image">Upload Image:</label>
                    <input type="file" id="clothing_image" name="clothing_image" accept="image/*" required>
                    <button type="submit" class="btn">Try On</button>
                </form>
            </section>

            <script>
                document.querySelectorAll('.try-on-btn').forEach(button => {{
                    button.addEventListener('click', () => {{
                        const clothingType = button.getAttribute('data-clothing-type');
                        const clothingItem = button.getAttribute('data-clothing-item');
                        fetch('/submit', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                            body: new URLSearchParams({{
                                'bust': '{bust}',
                                'waist': '{waist}',
                                'hips': '{hips}',
                                'high_hip': '{high_hip}',
                                'height_range': '{height_range}',
                                'size': '{size}',
                                'clothing_type': clothingType,
                                'clothing_item': clothingItem
                            }})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            if (data.status === 'success') {{
                                document.querySelector('.result-image img').src = data.image_url;
                            }}
                        }})
                        .catch(error => console.error('Error:', error));
                    }});
                }});

                document.getElementById('upload-form').addEventListener('submit', (e) => {{
                    e.preventDefault();
                    const formData = new FormData(e.target);
                    fetch('/upload', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.status === 'success') {{
                            document.querySelector('.result-image img').src = data.image_url;
                        }}
                    }})
                    .catch(error => console.error('Error:', error));
                }});
            </script>
        </body>
        </html>
        """
        self.wfile.write(html_response.encode())

# Start the server
Handler = CustomHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Server running at port", PORT)
    httpd.serve_forever()