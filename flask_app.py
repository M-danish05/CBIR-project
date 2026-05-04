from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image
import base64
import io
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'cbir_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///history.db'
db = SQLAlchemy(app)

class SearchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_image = db.Column(db.String(100))
    result_label = db.Column(db.String(50))
    score = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Class names
class_names = ['dog', 'horse', 'elephant', 'butterfly', 'chicken',
               'cat', 'cow', 'sheep', 'spider', 'squirrel']

# Load features, labels and images
print("Loading database...")
features = np.load('../CBIR_FYP/features.npy')
labels = np.load('../CBIR_FYP/database_labels.npy')
images = np.load('../CBIR_FYP/database_images.npy')

# Load model
print("Loading model...")
model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
model = torch.nn.Sequential(*list(model.children())[:-1])
model.eval()

# Transform
query_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

print("System Ready!")

# Upload folder
os.makedirs('static/uploads', exist_ok=True)

@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user or (username == 'admin' and password == '1234'):
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password!'
    return render_template('login.html', error=error)

@app.route('/history')
def history():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    history = SearchHistory.query.order_by(SearchHistory.timestamp.desc()).all()
    return render_template('history.html', history=history)

@app.route('/delete_history/<int:id>')
def delete_history(id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    item = SearchHistory.query.get(id)
    if item:
        db.session.delete(item)
        db.session.commit()
    return redirect(url_for('history'))

@app.route('/clear_history')
def clear_history():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    SearchHistory.query.delete()
    db.session.commit()
    return redirect(url_for('history'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            error = 'Passwords do not match!'
        elif User.query.filter_by(username=username).first():
            error = 'Username already exists!'
        elif User.query.filter_by(email=email).first():
            error = 'Email already exists!'
        else:
            new_user = User(
                username=username,
                email=email,
                password=password
            )
            db.session.add(new_user)
            db.session.commit()
            success = 'Account created successfully! Please login.'
    return render_template('register.html', error=error, success=success)    

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/search', methods=['POST'])
def search():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    # Get uploaded image
    file = request.files['image']
    top_k = int(request.form['top_k'])

    # Save query image
    filename = 'query.jpg'
    filepath = os.path.join('static/uploads', filename)
    file.save(filepath)

    # Extract features
    query_image = Image.open(filepath).convert('RGB')
    img_tensor = query_transform(query_image).unsqueeze(0)
    with torch.no_grad():
        query_feature = model(img_tensor).squeeze().numpy()

    # Find similar images
    query_feature = query_feature.reshape(1, -1)
    similarities = cosine_similarity(query_feature, features)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    # Prepare results
    results = []
    for idx in top_indices:
        img = images[idx].transpose(1, 2, 0)
        img = (img * 255).astype(np.uint8)
        pil_img = Image.fromarray(img)
        buffer = io.BytesIO()
        pil_img.save(buffer, format='JPEG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        results.append({
            'image': img_base64,
            'label': class_names[labels[idx]],
            'score': f"{similarities[idx]:.3f}"
        })

    # Save to history
    for result in results[:3]:
        history = SearchHistory(
            query_image=filename,
            result_label=result['label'],
            score=result['score']
        )
        db.session.add(history)
    db.session.commit()

    return render_template('results.html',
                         results=results,
                         query_image=filename)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)