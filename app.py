from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    roll_no = db.Column(db.String(50))
    course_name = db.Column(db.String(100))
    batch_year = db.Column(db.Integer)
    cv_filename = db.Column(db.String(200))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

# Create tables
with app.app_context():
    db.create_all()
    # Get or update admin user
    admin_user = User.query.filter_by(username='admin').first()
    new_password = 'Adm!n2023@Secure#'  # Replace with your desired new password
    
    if not admin_user:
        admin_user = User(
            username='admin',
            password=generate_password_hash(new_password)
        )
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created successfully!')
    else:
        admin_user.password = generate_password_hash(new_password)
        db.session.commit()
        print('Admin password updated successfully!')

# Auth decorator
def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

# Routes
@app.route('/')
def index():
    students = Student.query.all()
    return render_template('index.html', students=students)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['logged_in'] = True
            session['username'] = username  # Store username in session for clarity
            return redirect(url_for('admin'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)  # Clear username from session
    return redirect(url_for('index'))

@login_required
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        course_name = request.form['course_name']
        batch_year = int(request.form['batch_year'])
        cv = request.files['cv']
        if cv and cv.filename.endswith('.pdf'):
            filename = secure_filename(cv.filename)
            cv.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_student = Student(
                name=name, 
                roll_no=roll_no,
                course_name=course_name,
                batch_year=batch_year,
                cv_filename=filename
            )
            db.session.add(new_student)
            db.session.commit()
            flash('Student added!')
    students = Student.query.all()
    return render_template('admin.html', students=students)

@login_required
@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.roll_no = request.form['roll_no']
        student.course_name = request.form['course_name']
        student.batch_year = int(request.form['batch_year'])
        
        # Handle new CV file if uploaded
        if 'cv' in request.files:
            cv = request.files['cv']
            if cv and cv.filename.endswith('.pdf'):
                # Delete old CV file if it exists
                if student.cv_filename:
                    old_cv_path = os.path.join(app.config['UPLOAD_FOLDER'], student.cv_filename)
                    if os.path.exists(old_cv_path):
                        os.remove(old_cv_path)
                
                # Save new CV file
                filename = secure_filename(cv.filename)
                cv.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                student.cv_filename = filename

        db.session.commit()
        flash('Student updated successfully!')
        return redirect(url_for('admin'))
    
    return render_template('edit_student.html', student=student)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)


