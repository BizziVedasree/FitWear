from flask import request, render_template, redirect, url_for, session

# Dictionary for all body shapes
shapes_data = {
    "hourglass": {
        "title": "Hourglass Body Shape",
        "image": "/static/images/hourglass.png",
        "description1": "The hourglass body shape is naturally curvy, with a well-defined waist and balanced bust and hips. This body type is best suited for fitted clothing that enhances the waistline.",
        "description2": "Choosing clothing like Wrap dresses, bodycon outfits, and structured tops help maintain the natural proportions. It’s important to avoid overly loose or boxy clothing, as they may hide the natural curves instead of complementing them."
    },
    "rectangle": {
        "title": "Rectangle Body Shape",
        "image": "/static/images/rectangle.png",
        "description1": "A rectangle body shape means the shoulders, waist, and hips are nearly the same width, creating a straight silhouette. There is little waist definition, giving an athletic or lean appearance.",
        "description2": "The main goal for this body type is to create curves by emphasizing the waist and adding volume to the bust and hips. Wearing belts, peplum tops, structured jackets, and high-waisted clothing helps enhance the waistline and add shape."
    },
    "apple": {
        "title": "Apple Body Shape",
        "image": "/static/images/apple.png",
        "description1": "An apple body shape is characterized by a fuller midsection, often with a less defined waist but slimmer arms and legs. The focus for this body type is to elongate the torso and highlight the legs.",
        "description2": "Choosing clothing with V-necks, empire waistlines, and wrap dresses helps create a more defined shape. Darker colors around the waist area and flowy tops can provide a flattering effect while directing attention to the legs with fitted bottoms"
    },
    "triangle": {
        "title": "Pear Body Shape",
        "image": "/static/images/pear.png",
        "description1": "A pear/triangle-shaped body has wider hips compared to the shoulders and a well-defined waist. The lower half of the body appears fuller, while the upper body is relatively narrow.",
        "description2": "The key to styling this body shape is to balance proportions by drawing attention to the upper body. Wearing tops with statement sleeves, off-shoulder styles, and bright colors can help create visual balance. A-line skirts and flared pants work well to complement the lower body."
    },
    "inverted-triangle": {
        "title": "Inverted Triangle "
        "            Body Shape",
        "image": "/static/images/inverted triangle.png",
        "description1": "People with an inverted triangle body shape have broader shoulders compared to their waist and hips. This creates a strong upper body, often associated with an athletic build. ",
        "description2": "The main goal when styling is to soften the upper body and add volume to the lower half. Wearing V-neck tops, wrap styles, and flared pants helps create a balanced look. Avoiding heavily structured shoulders or high-neck tops can also help in achieving a proportional appearance."
    }   
}


def init_main_routes(app):
    @app.route('/', methods=["GET"])
    def home():
        return render_template('index.html')

    @app.route('/classify', methods=["POST"])
    def classify():
        session.clear()
        session['measurements'] = {
            'bust': request.form.get('bust', ''),
            'waist': request.form.get('waist', ''),
            'hips': request.form.get('hips', ''),
            'high_hip': request.form.get('high_hip', ''),
            'height_range': request.form.get('height_range', ''),
            'size': request.form.get('size', '')
        }
        #if 'user_id' in session:
            #return redirect(url_for('dashboard', user_id=session['user_id']))
        return render_template('auth_popup.html', next=url_for('quest'))

    @app.route('/know-more/<shape>')
    def know_more(shape):
        return render_template('know-more.html', shape=shape, shape_data=shapes_data[shape])
        

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/measure', methods=["GET", "POST"])
    def measure():
        return render_template('measure.html')
    
    @app.route('/results', methods=["GET"])
    def results():
        return render_template('results.html', shape_data=shapes_data[session['shape']])