import os
import logging
import base64
import io
import uuid
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from PIL import Image
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Import model functionalities
from model import load_model, preprocess_image, predict_disease
from models import db, User, Scan

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Configure the database
db_url = os.environ.get("DATABASE_URL")
print(f"Database URL: {db_url}")
if not db_url:
    raise ValueError("DATABASE_URL environment variable not set")
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the model on startup
model_package = load_model()

# Dictionary of apple diseases and descriptions
APPLE_DISEASES = {
    'apple_scab': {
        'name': 'Apple Scab',
        'description': 'A fungal disease caused by Venturia inaequalis. It creates olive-green to brown spots on leaves and fruits.',
        'treatment': 'Apply fungicides in early spring. Prune infected branches and remove fallen leaves to reduce spore sources.'
    },
    'black_rot': {
        'name': 'Black Rot',
        'description': 'A fungal disease caused by Botryosphaeria obtusa. It causes circular lesions on leaves and rotting of fruits.',
        'treatment': 'Remove and destroy infected plant parts. Apply appropriate fungicides during the growing season.'
    },
    'cedar_apple_rust': {
        'name': 'Cedar Apple Rust',
        'description': 'A fungal disease that requires both cedar and apple trees to complete its life cycle. It causes bright orange-yellow spots on leaves.',
        'treatment': 'Plant resistant apple varieties. Remove nearby cedar trees if possible. Apply fungicides in spring.'
    },
    'healthy': {
        'name': 'Healthy',
        'description': 'The plant shows no signs of disease.',
        'treatment': 'Continue regular care and preventive practices to keep the plant healthy.'
    }
}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create all tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic form validation
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard page"""
    # Get user's scan history, ordered by most recent
    scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.scanned_at.desc()).all()
    return render_template('dashboard.html', scans=scans)

@app.route('/predict', methods=['POST'])
def predict():
    """Process the uploaded image and return prediction results"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files and 'imageData' not in request.form:
            return jsonify({'error': 'No image provided'}), 400
        
        # Flag to track if we need to save the image
        save_image = False
        image_filename = None
        
        # Process image from form data (base64) if provided
        if 'imageData' in request.form:
            image_data = request.form['imageData'].split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            save_image = True
        # Otherwise process uploaded file
        else:
            image_file = request.files['image']
            image = Image.open(image_file)
            save_image = True
        
        # Preprocess the image for feature extraction
        features = preprocess_image(image)
        
        # Make prediction
        predicted_class, confidence = predict_disease(model_package, features)
        
        # Get disease information
        disease_info = APPLE_DISEASES.get(predicted_class, {
            'name': 'Unknown',
            'description': 'No information available for this condition.',
            'treatment': 'Consult with a plant pathologist.'
        })
        
        # Save the scan if user is logged in
        if current_user.is_authenticated and save_image:
            # Generate a unique filename
            image_filename = f"{uuid.uuid4()}.jpg"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            
            # Save the image
            image.save(image_path)
            
            # Create scan record
            scan = Scan(
                user_id=current_user.id,
                image_filename=image_filename,
                disease=predicted_class,
                confidence=confidence
            )
            db.session.add(scan)
            db.session.commit()
        
        # Return result
        return jsonify({
            'disease': predicted_class,
            'confidence': float(confidence),
            'disease_name': disease_info['name'],
            'description': disease_info['description'],
            'treatment': disease_info['treatment']
        })
    
    except Exception as e:
        logging.error(f"Error during prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/scan_details/<int:scan_id>')
@login_required
def scan_details(scan_id):
    """View details of a specific scan"""
    # Get the scan, ensuring it belongs to the current user
    scan = Scan.query.filter_by(id=scan_id, user_id=current_user.id).first_or_404()
    
    # Get disease information
    disease_info = APPLE_DISEASES.get(scan.disease, {
        'name': 'Unknown',
        'description': 'No information available for this condition.',
        'treatment': 'Consult with a plant pathologist.'
    })
    
    return render_template('scan_details.html', scan=scan, disease_info=disease_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
