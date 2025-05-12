from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    #responses = db.relationship('UserResponse', backref='user', lazy=True,cascade="all, delete-orphan")

    

class UserResponse(db.Model):
    __tablename__ = 'new_response'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bust = db.Column(db.Float)
    waist = db.Column(db.Float)
    hips = db.Column(db.Float)
    #shoulder = db.Column(db.Float)
    body_shape = db.Column(db.String(50))

    #relationship
    user = db.relationship('User', backref=' new_responses')

'''class silhouette(db.Model):
    __tablename__ = 'silhouette'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Silhouette {self.name}>'

class clothes(db.Model):
    __tablename__ = 'clothes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Clothes {self.name}>'''