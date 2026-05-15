from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, Response, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import db, User, StudentRecord, SystemLog
from werkzeug.security import generate_password_hash
import os
import pandas as pd
from ml_engine import train_model, generate_mock_dataset, predict_retention, batch_predict
from werkzeug.utils import secure_filename
from fpdf import FPDF
from io import BytesIO
from db_utils import log_action, setup_database
from graph_utils import generate_report_graph, generate_bulk_dashboard_graphs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey_change_in_production'

# Database Configuration (MySQL Support)
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_DB = os.getenv('MYSQL_DB', 'Memory_Retention_Predictor')

import urllib.parse

if MYSQL_USER and MYSQL_PASSWORD:
    # Use MySQL if credentials are provided (Quote password to handle special chars like @)
    encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}'
else:
    # Fallback to SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('analytics_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            log_action('User logged in')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_action('User logged out')
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('analytics_dashboard'))
    users = User.query.all()
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(20).all()
    student_records = StudentRecord.query.order_by(StudentRecord.created_at.desc()).all()
    return render_template('admin_dashboard.html', users=users, logs=logs, student_records=student_records)

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('analytics_dashboard'))
        
    username = request.form.get('new_username')
    password = request.form.get('new_password')
    role = request.form.get('role', 'staff')
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
    else:
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Account "{username}" successfully created as {role.title()}!', 'success')
        log_action(f'Created new user account: {username} ({role})')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('analytics_dashboard'))
    
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_dashboard'))
        
    user = User.query.get(user_id)
    if user:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        log_action(f'Deleted user account: {username}')
        flash(f'User "{username}" has been deleted.', 'success')
    else:
        flash('User not found.', 'error')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/clear_logs', methods=['POST'])
@login_required
def clear_logs():
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('analytics_dashboard'))
    
    SystemLog.query.delete()
    db.session.commit()
    log_action('Cleared all system logs')
    flash('All system logs have been cleared successfully.', 'success')
    return redirect(url_for('admin_dashboard'))
@app.route('/delete_record/<int:record_id>', methods=['POST'])
@login_required
def delete_record(record_id):
    if current_user.role != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('analytics_dashboard'))
    
    record = StudentRecord.query.get(record_id)
    if record:
        db.session.delete(record)
        db.session.commit()
        log_action(f'Deleted prediction record for student: {record.student_name}')
        flash('Student record deleted successfully.', 'success')
    else:
        flash('Record not found.', 'error')
        
    return redirect(url_for('admin_dashboard'))


@app.route('/upload_data', methods=['GET', 'POST'])
@login_required
def upload_data():
    if request.method == 'POST':
        if 'dataset' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['dataset']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            try:
                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Sanitize column names for internal use
                df.columns = [c.strip().lower() for c in df.columns]
                column_mapping = {'student name': 'name', 'student_name': 'name', 'student id': 'student_id', 'school': 'college'}
                df = df.rename(columns=column_mapping)
                
                success = False
                if 'retention_score' in df.columns:
                    # Train AI model
                    success, msg = train_model(df)
                    if success:
                        flash(msg, 'success')
                        log_action(f'Uploaded historical dataset ({file.filename}) and trained AI model')
                    else:
                        flash(f"Error training model: {msg}", 'error')
                else:
                    # Predict scores for the uploaded data
                    success, result = batch_predict(df)
                    if success:
                        df = result
                        flash('Predictions generated successfully for the uploaded dataset!', 'success')
                        log_action(f'Uploaded new dataset ({file.filename}) and generated AI predictions')
                    else:
                        flash(f"Error generating predictions: {result}", 'error')
                
                # Now insert the DataFrame into the database
                if success:
                    for index, row in df.iterrows():
                        record = StudentRecord(
                            user_id=current_user.id,
                            student_name=row.get('name', 'Unknown'),
                            student_id=str(row.get('student_id', 'Unknown')),
                            school=row.get('college', 'Unknown'),
                            department=row.get('department', 'Unknown'),
                            hours_studied=float(row.get('hours_studied', 0)),
                            previous_score=float(row.get('previous_score', 0)),
                            sleep_hours=float(row.get('sleep_hours', 0)),
                            predicted_retention=float(row.get('retention_score', 0)) if 'retention_score' in df.columns else None
                        )
                        db.session.add(record)
                    db.session.commit()
                
                return redirect(url_for('analytics_dashboard'))
            except Exception as e:
                flash(f'Error processing file: {e}', 'error')
        else:
            flash('Invalid file type. Please upload a CSV or Excel file.', 'error')
            
    return render_template('upload_data.html')

@app.route('/generate_mock', methods=['POST'])
@login_required
def generate_mock():
    df = generate_mock_dataset()
    success, msg = train_model(df)
    if success:
        for index, row in df.iterrows():
            record = StudentRecord(
                user_id=current_user.id,
                student_name=row.get('name', 'Unknown'),
                student_id=str(row.get('student_id', 'Unknown')),
                school=row.get('school', 'Unknown'),
                department=row.get('department', 'Unknown'),
                hours_studied=float(row.get('hours_studied', 0)),
                previous_score=float(row.get('previous_score', 0)),
                sleep_hours=float(row.get('sleep_hours', 0)),
                predicted_retention=float(row.get('retention_score', 0))
            )
            db.session.add(record)
        db.session.commit()
        flash('Mock dataset generated and AI model trained successfully!', 'success')
        log_action('Generated mock data and trained AI model')
    else:
        flash(f"Error training model: {msg}", 'error')
    return redirect(url_for('analytics_dashboard'))

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    prediction = None
    form_data = None
    if request.method == 'POST':
        try:
            student_name = request.form.get('student_name', '')
            student_id = request.form.get('student_id', '')
            school = request.form.get('school', '')
            department = request.form.get('department', '')
            
            hours = float(request.form.get('hours_studied', 0))
            score = float(request.form.get('previous_score', 0))
            sleep = float(request.form.get('sleep_hours', 0))
            
            prediction = predict_retention(hours, score, sleep)
            
            # Save to database
            record = StudentRecord(
                user_id=current_user.id,
                student_name=student_name,
                student_id=student_id,
                school=school,
                department=department,
                hours_studied=hours,
                previous_score=score,
                sleep_hours=sleep,
                predicted_retention=prediction
            )
            db.session.add(record)
            db.session.commit()
            
            form_data = {
                'student_name': student_name,
                'student_id': student_id,
                'school': school,
                'department': department,
                'hours_studied': hours,
                'previous_score': score,
                'sleep_hours': sleep
            }
            log_action(f'Performed and saved prediction for: {student_name}')
            
            return render_template('predict.html', prediction=prediction, form_data=form_data, record_id=record.id)
        except ValueError:
            flash('Invalid input for numeric fields.', 'error')
            
    return render_template('predict.html', prediction=prediction, form_data=form_data)

@app.route('/download_single_report/<int:record_id>')
@login_required
def download_single_report(record_id):
    record = StudentRecord.query.get_or_404(record_id)
    
    # Security Check: Ensure user owns the record
    if record.user_id != current_user.id and current_user.role != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('analytics_dashboard'))
    
    # Generate Plot using helper
    img_stream = generate_report_graph(record)

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_fill_color(30, 41, 59) # Dark blue header
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 25, "Retention Prediction Report", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)
    
    # Student Info
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(190, 10, "  Student Profile", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", '', 11)
    pdf.cell(95, 8, f"  Name: {record.student_name}", ln=0)
    pdf.cell(95, 8, f"ID: {record.student_id}", ln=1)
    pdf.cell(95, 8, f"  College: {record.school}", ln=0)
    pdf.cell(95, 8, f"Department: {record.department}", ln=1)
    
    pdf.ln(10)
    
    # Metrics
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(190, 10, "  Academic Metrics & Prediction", ln=True, fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", '', 11)
    pdf.cell(63, 8, f"  Hours Studied: {record.hours_studied}", ln=0)
    pdf.cell(63, 8, f"Previous Score: {record.previous_score}", ln=0)
    pdf.cell(63, 8, f"Sleep Hours: {record.sleep_hours}", ln=1)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(16, 185, 129) # Success green
    pdf.cell(190, 10, f"  PREDICTED RETENTION SCORE: {round(record.predicted_retention, 2)}%", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(5)
    
    # Image
    temp_img_path = f"temp_plot_{record_id}.png"
    with open(temp_img_path, "wb") as f:
        f.write(img_stream.getbuffer())
    
    pdf.image(temp_img_path, x=15, y=pdf.get_y(), w=180)
    
    # Clean up
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)

    # Footer
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(190, 10, "Generated by AI-Based Memory Retention Predictor System", align='C')

    response_stream = BytesIO()
    pdf_bytes = pdf.output()
    response_stream.write(pdf_bytes)
    response_stream.seek(0)
    
    return send_file(
        response_stream,
        as_attachment=True,
        download_name=f"{record.student_name.replace(' ', '_')}_Prediction_Report.pdf",
        mimetype='application/pdf'
    )

@app.route('/download_bulk_report')
@login_required
def download_bulk_report():
    if current_user.role == 'admin':
        records = StudentRecord.query.order_by(StudentRecord.created_at.desc()).all()
    else:
        records = StudentRecord.query.filter_by(user_id=current_user.id).order_by(StudentRecord.created_at.desc()).all()
        
    if not records:
        flash('No dataset available to download.', 'error')
        return redirect(url_for('analytics_dashboard'))

    # Build dataframe from records
    data = []
    for r in records:
        data.append({
            'student_id': r.student_id,
            'name': r.student_name,
            'department': r.department,
            'college': r.school,
            'hours_studied': r.hours_studied,
            'previous_score': r.previous_score,
            'sleep_hours': r.sleep_hours,
            'retention_score': r.predicted_retention
        })
    df = pd.DataFrame(data)

    # Generate Graphs
    graphs = generate_bulk_dashboard_graphs(df)

    # Generate PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page 1: Summary & Graphs
    pdf.add_page()
    pdf.set_fill_color(30, 41, 59)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 25, "Bulk Student Analytics Report", ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(20)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Statistical Overview", ln=True)
    pdf.ln(5)
    
    # Save temp images for PDF
    for key, buf in graphs.items():
        temp_path = f"temp_bulk_{key}.png"
        with open(temp_path, "wb") as f:
            f.write(buf.getbuffer())
        pdf.image(temp_path, x=15, w=180)
        os.remove(temp_path)
        pdf.ln(5)

    # Page 2: Detailed Student Table
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "Individual Student Records", ln=True)
    pdf.ln(5)
    
    # Table Header
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(10, 10, "No", 1, 0, 'C', True)
    pdf.cell(40, 10, "Student ID", 1, 0, 'C', True)
    pdf.cell(60, 10, "Name", 1, 0, 'C', True)
    pdf.cell(50, 10, "Department", 1, 0, 'C', True)
    pdf.cell(30, 10, "Retention %", 1, 1, 'C', True)
    
    # Table Content
    pdf.set_font("Arial", '', 9)
    for i, row in df.iterrows():
        # Ensure we don't overflow the page
        if pdf.get_y() > 260:
            pdf.add_page()
            # Redraw header
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(241, 245, 249)
            pdf.cell(10, 10, "No", 1, 0, 'C', True)
            pdf.cell(40, 10, "Student ID", 1, 0, 'C', True)
            pdf.cell(60, 10, "Name", 1, 0, 'C', True)
            pdf.cell(50, 10, "Department", 1, 0, 'C', True)
            pdf.cell(30, 10, "Retention %", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 9)

        pdf.cell(10, 8, str(i+1), 1, 0, 'C')
        pdf.cell(40, 8, str(row.get('student_id', 'N/A'))[:15], 1, 0, 'C')
        pdf.cell(60, 8, str(row.get('name', 'N/A'))[:25], 1, 0, 'L')
        pdf.cell(50, 8, str(row.get('department', 'N/A'))[:20], 1, 0, 'C')
        pdf.cell(30, 8, f"{round(row['retention_score'], 1)}%", 1, 1, 'C')

    response_stream = BytesIO()
    pdf_bytes = pdf.output()
    response_stream.write(pdf_bytes)
    response_stream.seek(0)
    
    log_action('Downloaded bulk PDF analytics report')
    
    return send_file(
        response_stream,
        as_attachment=True,
        download_name="Bulk_Student_Analytics_Report.pdf",
        mimetype='application/pdf'
    )

@app.route('/analytics_dashboard')
@login_required
def analytics_dashboard():
    chart_data = None
    table_rows = []
    
    if current_user.role == 'admin':
        # Admins see everything for collaborative analysis
        records = StudentRecord.query.order_by(StudentRecord.created_at.desc()).all()
    else:
        # Staff see only their own data
        records = StudentRecord.query.filter_by(user_id=current_user.id).order_by(StudentRecord.created_at.desc()).all()
        
    if records:
        chart_data = {
            'labels': [r.student_name for r in records],
            'hours_studied': [r.hours_studied for r in records],
            'sleep_hours': [r.sleep_hours for r in records],
            'previous_score': [r.previous_score for r in records],
            'retention_score': [r.predicted_retention for r in records]
        }
        for r in records:
            table_rows.append({
                'name': r.student_name,
                'student_id': r.student_id,
                'college': r.school,
                'department': r.department,
                'retention_score': r.predicted_retention
            })

    return render_template('analytics_dashboard.html', chart_data=chart_data, table_rows=table_rows)

@app.route('/clear_data', methods=['POST'])
@login_required
def clear_data():
    records = StudentRecord.query.filter_by(user_id=current_user.id).all()
    for r in records:
        db.session.delete(r)
    db.session.commit()
    log_action('Cleared all personal dashboard data')
        
    flash('Dashboard data has been cleared.', 'success')
    return redirect(url_for('analytics_dashboard'))

if __name__ == '__main__':
    setup_database(app)
    app.run(debug=True, port=5000)
