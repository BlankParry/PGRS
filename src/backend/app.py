from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from nlp import preprocess_text, categorize_complaint, assign_priority, analyze_sentiment
from datetime import datetime, timedelta
from functools import wraps

import nltk

# Download necessary NLTK resources
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('vader_lexicon')

app = Flask(__name__)

# Set up the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:1234@localhost/complaint_system'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

db = SQLAlchemy(app)

# Initialize database
with app.app_context():
    db.create_all()

# Define models for the database
class Citizen(db.Model):
    __tablename__ = 'citizens'

    citizen_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(200), nullable=True)
    gender = db.Column(db.String(10), nullable=True)

class Complaint(db.Model):
    __tablename__ = 'complaints'

    complaint_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey('citizens.citizen_id'), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.department_id'), nullable=False)
    priority = db.Column(db.Enum('LOW', 'MEDIUM', 'HIGH'), nullable=False)
    date_submitted = db.Column(db.Date, nullable=True)

    # Define relationships properly
    citizen = db.relationship('Citizen', backref=db.backref('complaints', lazy=True))
    department = db.relationship('Department', backref=db.backref('complaints', lazy=True))

class Department(db.Model):
    __tablename__ = 'departments'

    department_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    contact_person = db.Column(db.String(50))
    contact_number = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    address = db.Column(db.String(100))

class ComplaintLog(db.Model):
    __tablename__ = 'complaint_log'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id'), nullable=False)
    status = db.Column(db.Enum('In-progress', 'Resolved', 'Not resolved'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    remarks = db.Column(db.Text)

    # Relationship to link logs to the complaint
    complaint = db.relationship('Complaint', backref=db.backref('logs', cascade='all, delete-orphan'))

class Feedback(db.Model):
    __tablename__ = 'feedback'

    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id'), nullable=False)
    rating = db.Column(db.Integer, db.CheckConstraint('rating BETWEEN 1 AND 5'))
    comments = db.Column(db.Text)
    date_provided = db.Column(db.Date)

    # Relationship to link feedback to complaint
    complaint = db.relationship('Complaint', backref=db.backref('feedback', cascade='all, delete-orphan'))

# Validation functions
def validate_email(email):
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    import re
    pattern = r'^\d{10}$'
    return re.match(pattern, phone) is not None

# Helper functions for navigation protection
def citizen_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'citizen_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('citizen_login'))
        return f(*args, **kwargs)
    return decorated_function

def department_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'department_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('department_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    # Only redirect to dashboards for direct access to root URL
    if 'citizen_id' in session and request.path == '/':
        return redirect(url_for('citizen_dashboard'))
    if 'department_id' in session and request.path == '/':
        return redirect(url_for('department_dashboard'))
    return render_template('index.html')

@app.route('/home')
def home():
    # Clear any existing session
    session.clear()
    # Always render index.html without redirecting to dashboard
    return render_template('index.html')

# Citizen Registration Route
@app.route('/citizen/register', methods=['GET', 'POST'])
def citizen_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact_number = request.form['contact_number']
        address = request.form['address']
        # Remove gender field if it's not in your database model
        # gender = request.form['gender']  

        # Check if email or contact number already exists
        if Citizen.query.filter_by(email=email).first():
            return render_template('citizen_register.html', error="Email already registered")
        if Citizen.query.filter_by(contact_number=contact_number).first():
            return render_template('citizen_register.html', error="Contact number already registered")

        # Create new citizen without gender field
        new_citizen = Citizen(
            name=name,
            email=email,
            contact_number=contact_number,
            address=address
        )

        try:
            db.session.add(new_citizen)
            db.session.commit()
            return redirect(url_for('citizen_login'))
        except Exception as e:
            db.session.rollback()
            return render_template('citizen_register.html', error="Registration failed. Please try again.")

    return render_template('citizen_register.html')

# Citizen Login Route
@app.route('/citizen-login', methods=['GET', 'POST'])
def citizen_login():
    if request.method == 'POST':
        email = request.form.get('email')
        contact_number = request.form.get('contact_number')

        citizen = Citizen.query.filter_by(email=email, contact_number=contact_number).first()
        if citizen:
            session['citizen_id'] = citizen.citizen_id
            session['last_activity'] = datetime.now().timestamp()
            flash('Login successful!', 'success')
            return redirect(url_for('citizen_dashboard'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('citizen_login'))

    return render_template('login.html')

# Citizen Dashboard Route
@app.route('/citizen-dashboard')
@citizen_login_required
def citizen_dashboard():
    citizen = Citizen.query.get(session['citizen_id'])
    if not citizen:
        session.clear()
        flash('Account not found', 'error')
        return redirect(url_for('citizen_login'))
    
    complaints = Complaint.query.filter_by(citizen_id=citizen.citizen_id).all()
    return render_template('citizen_dashboard.html', citizen=citizen, complaints=complaints)

# Register Complaint Route
@app.route('/register-complaint', methods=['GET', 'POST'])
@citizen_login_required
def register_complaint():
    if request.method == 'POST':
        description = request.form.get('description')
        
        if not description:
            flash('Please provide a complaint description', 'error')
            return redirect(url_for('register_complaint'))
        
        try:
            # Process complaint using NLP
            processed_text = preprocess_text(description)
            category, department_id = categorize_complaint(processed_text)
            priority = assign_priority(processed_text)
            
            # Create new complaint
            complaint = Complaint(
                citizen_id=session['citizen_id'],
                description=description,
                category=category,
                department_id=department_id,
                priority=priority,
                date_submitted=datetime.now().date()
            )
            
            db.session.add(complaint)
            db.session.commit()
            
            flash('Complaint registered successfully!', 'success')
            return redirect(url_for('citizen_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering complaint: {str(e)}', 'error')
            return redirect(url_for('register_complaint'))
    
    citizen = Citizen.query.get(session['citizen_id'])
    return render_template('register_complaint.html', citizen=citizen)

# View Complaint Route
@app.route('/view-complaint/<int:complaint_id>')
@citizen_login_required
def view_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    if complaint.citizen_id != session['citizen_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('citizen_dashboard'))
    
    # Get department name from the department_id
    department_names = {
        1: "Sanitation",
        2: "Water",
        3: "Infrastructure",
        4: "Public Safety",
        5: "General"
    }
    
    department_name = department_names.get(complaint.department_id, "Unknown Department")
    
    return render_template('view_complaint.html', 
                         complaint=complaint,
                         department_name=department_name)

# Department Registration Route
@app.route('/department-register', methods=['GET', 'POST'])
def department_register():
    if request.method == 'POST':
        name = request.form.get('name')
        contact_person = request.form.get('contact_person')
        contact_number = request.form.get('contact_number')
        email = request.form.get('email')
        address = request.form.get('address')

        if not all([name, contact_person, contact_number, email, address]):
            flash('All fields are required', 'error')
            return redirect(url_for('department_register'))

        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('department_register'))

        if not validate_phone(contact_number):
            flash('Please enter a valid contact number', 'error')
            return redirect(url_for('department_register'))

        try:
            department = Department(
                name=name,
                contact_person=contact_person,
                contact_number=contact_number,
                email=email,
                address=address
            )
            db.session.add(department)
            db.session.commit()
            flash('Department registered successfully!', 'success')
            return redirect(url_for('department_login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('department_register'))

    return render_template('department_register.html')

# Department Login Route
@app.route('/department-login', methods=['GET', 'POST'])
def department_login():
    if request.method == 'POST':
        email = request.form.get('email')
        contact_number = request.form.get('contact_number')

        department = Department.query.filter_by(
            email=email, 
            contact_number=contact_number
        ).first()

        if department:
            session['department_id'] = department.department_id
            session['last_activity'] = datetime.now().timestamp()
            flash('Login successful!', 'success')
            return redirect(url_for('department_dashboard'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('department_login'))

    return render_template('department_login.html')

# Department Dashboard Route
@app.route('/department-dashboard')
@department_login_required
def department_dashboard():
    department = Department.query.get(session['department_id'])
    if not department:
        session.clear()
        flash('Department not found', 'error')
        return redirect(url_for('department_login'))

    # Get status filter from query parameters
    status = request.args.get('status', 'all')
    
    # Base query
    complaints_query = Complaint.query.filter_by(department_id=department.department_id)
    
    # Apply status filter if not 'all'
    if status != 'all':
        complaints_query = complaints_query.join(ComplaintLog).filter(ComplaintLog.status == status)
    
    complaints = complaints_query.all()
    
    # Add latest status to each complaint
    for complaint in complaints:
        latest_log = ComplaintLog.query.filter_by(complaint_id=complaint.complaint_id).order_by(ComplaintLog.timestamp.desc()).first()
        complaint.latest_status = latest_log.status if latest_log else 'Pending'

    return render_template('department_dashboard.html',
                         department_name=department.name,
                         complaints=complaints,
                         selected_status=status)

# Update Complaint Status Route
@app.route('/update-complaint-status/<int:complaint_id>', methods=['POST'])
@department_login_required
def update_complaint_status(complaint_id):
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        
        # Security check
        if complaint.department_id != session['department_id']:
            flash('Unauthorized access', 'error')
            return redirect(url_for('department_dashboard'))

        status = request.form.get('status')
        remarks = request.form.get('remarks')

        # Validate status
        valid_statuses = ['In-progress', 'Resolved', 'Not resolved']
        if status not in valid_statuses:
            flash('Invalid status value', 'error')
            return redirect(url_for('department_dashboard'))

        # Validate remarks
        if not remarks or len(remarks.strip()) < 5:
            flash('Please provide meaningful remarks', 'error')
            return redirect(url_for('department_dashboard'))

        # Create log entry
        log = ComplaintLog(
            complaint_id=complaint_id,
            status=status,
            remarks=remarks,
            timestamp=datetime.now()
        )
        
        db.session.add(log)
        db.session.commit()

        flash('Status updated successfully', 'success')
        return redirect(url_for('department_dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'error')
        return redirect(url_for('department_dashboard'))

# Feedback Routes
@app.route('/feedback-form/<int:complaint_id>')
@citizen_login_required
def feedback_form(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    # Check if this complaint belongs to the logged-in citizen
    if complaint.citizen_id != session['citizen_id']:
        flash('Unauthorized access', 'error')
        return redirect(url_for('citizen_dashboard'))
    
    return render_template('feedback_form.html', complaint=complaint)

@app.route('/submit-feedback/<int:complaint_id>', methods=['POST'])
@citizen_login_required
def submit_feedback(complaint_id):
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        
        # Check if this complaint belongs to the logged-in citizen
        if complaint.citizen_id != session['citizen_id']:
            flash('Unauthorized access', 'error')
            return redirect(url_for('citizen_dashboard'))
        
        # Check if feedback already exists
        existing_feedback = Feedback.query.filter_by(complaint_id=complaint_id).first()
        if existing_feedback:
            flash('Feedback has already been submitted for this complaint', 'warning')
            return redirect(url_for('citizen_dashboard'))
        
        rating = request.form.get('rating')
        comments = request.form.get('comments')
        
        if not rating or not comments:
            flash('Please provide both rating and comments', 'error')
            return redirect(url_for('feedback_form', complaint_id=complaint_id))
        
        # Create new feedback entry
        feedback = Feedback(
            complaint_id=complaint_id,
            rating=int(rating),
            comments=comments,
            date_provided=datetime.now().date()
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('citizen_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('citizen_dashboard'))

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Add session protection
@app.before_request
def before_request():
    if 'last_activity' in session:
        # Session timeout after 30 minutes of inactivity
        last_activity = datetime.fromtimestamp(session['last_activity'])
        if datetime.now() - last_activity > timedelta(minutes=30):
            session.clear()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('index'))
    session['last_activity'] = datetime.now().timestamp()

if __name__ == "__main__":
    app.run(debug=True, port=5001) 