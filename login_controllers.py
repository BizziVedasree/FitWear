from flask import request, render_template, redirect, url_for, session, current_app
from models import db, User, UserResponse

def init_login_routes(app):
    '''@app.route('/login', methods=["GET", "POST"])
    def login():
        with current_app.app_context():
            if request.method == "POST":
                uname = request.form.get('username')
                pwd = request.form.get('pwd') 
                user = User.query.filter_by(username=uname, password=pwd).first()
                if user:
                    session['user_id'] = user.id
                    return redirect(session.get('next', url_for('results')))
                #return render_template('login', msg='Invalid credentials')
            session['next'] = request.args.get('next', url_for('dashboard', user_id=0))
            return render_template('login.html')

    @app.route('/signup', methods=["GET", "POST"])
    def signup():
        with current_app.app_context():
            if request.method == "POST":
                uname = request.form.get('username')
                pwd = request.form.get('pwd')
                if User.query.filter_by(username=uname).first():
                    return render_template('signup.html', msg='Username exists')
                new_user = User(username=uname, password=pwd)
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                return redirect(session.get('next', url_for('dashboard', user_id=new_user.id)))
            session['next'] = request.args.get('next', url_for('dashboard', user_id=0))
            return render_template('signup.html')'''

    @app.route('/login', methods=["GET", "POST"])
    def login():
        with current_app.app_context():
            if request.method == "POST":
                uname = request.form.get('username')
                if not uname:
                    return render_template('login.html', msg='Username is required')
                if User.query.filter_by(username=uname).first():
                    return render_template('login.html', msg='Username already taken')
                new_user = User(username=uname, password='')
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                measurements = session.get('measurements', {})
                if measurements:
                    try:
                        bust = float(measurements.get('bust', 0))
                        waist = float(measurements.get('waist', 0))
                        hips = float(measurements.get('hips', 0))
                        high_hip = float(measurements.get('high_hip', 0))
                        from src.body_shape import classify_body_shape
                        body_shape = classify_body_shape(bust, waist, high_hip, hips)
                        response = UserResponse(
                            user_id=new_user.id,
                            bust=bust,
                            waist=waist,
                            hips=hips,
                            #shoulder=0,  # No shoulder input
                            body_shape=body_shape
                        )
                        db.session.add(response)
                        db.session.commit()
                    except ValueError:
                        pass
                 
                return redirect(url_for('dashboard', user_id=new_user.id))
            session['next'] = request.args.get('next', url_for('dashboard', user_id=0))
            return render_template('login.html')
        
    @app.route('/signup', methods=["GET", "POST"])
    def signup():
        with current_app.app_context():
            if request.method == "POST":
                uname = request.form.get('username')
                if not uname:
                    return render_template('quest.html', msg='Username is required')
                if User.query.filter_by(username=uname).first():
                    return render_template('quest.html', msg='Username already taken')
                new_user = User(username=uname, password='')
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                measurements = session.get('measurements', {})
                if measurements:
                    try:
                        bust = float(measurements.get('bust', 0))
                        waist = float(measurements.get('waist', 0))
                        hips = float(measurements.get('hips', 0))
                        high_hip = float(measurements.get('high_hip', 0))
                        from src.body_shape import classify_body_shape
                        body_shape = classify_body_shape(bust, waist, high_hip, hips)
                        response = UserResponse(
                            user_id=new_user.id,
                            bust=bust,
                            waist=waist,
                            hips=hips,
                            #shoulder=0,  # No shoulder input
                            body_shape=body_shape
                        )
                        db.session.add(response)
                        db.session.commit()
                    except ValueError:
                        pass
                 
                return redirect(url_for('dashboard', user_id=new_user.id))
            session['next'] = request.args.get('next', url_for('dashboard', user_id=0))
            return render_template('signup.html')
    
    @app.route('/quest', methods=["GET", "POST"])
    def quest():
        with current_app.app_context():
            if request.method == "POST":
                uname = request.form.get('username')
                if not uname:
                    return render_template('quest.html', msg='Username is required')
                if User.query.filter_by(username=uname).first():
                    return render_template('quest.html', msg='Username already taken')
                new_user = User(username=uname, password='')
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                measurements = session.get('measurements', {})
                if measurements:
                    try:
                        bust = float(measurements.get('bust', 0))
                        waist = float(measurements.get('waist', 0))
                        hips = float(measurements.get('hips', 0))
                        high_hip = float(measurements.get('high_hip', 0))
                        from src.body_shape import classify_body_shape
                        body_shape = classify_body_shape(bust, waist, high_hip, hips)
                        response = UserResponse(
                            user_id=new_user.id,
                            bust=bust,
                            waist=waist,
                            hips=hips,
                            #shoulder=0,  # No shoulder input
                            body_shape=body_shape
                        )
                        db.session.add(response)
                        db.session.commit()
                    except ValueError:
                        pass
                 
                return redirect(url_for('dashboard', user_id=new_user.id))
            session['next'] = request.args.get('next', url_for('dashboard', user_id=0))
            return render_template('quest.html')