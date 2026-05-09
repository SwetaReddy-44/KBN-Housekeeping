import os
import mysql.connector
from flask import Flask, render_template, request, redirect, flash, session, url_for
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "kbn_secret_key_change_in_production"

# Database configuration
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "kbn_housekeeping"

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def init_db():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            customer_name VARCHAR(255) NOT NULL,
            phone VARCHAR(50) NOT NULL,
            address TEXT NOT NULL,
            service_type VARCHAR(100) NOT NULL,
            preferred_date VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'Active',
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id INT,
            check_in VARCHAR(50),
            check_out VARCHAR(50),
            hours VARCHAR(50),
            location VARCHAR(255),
            status VARCHAR(50),
            log_date DATE,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        cursor.execute("ALTER TABLE feedbacks ADD COLUMN rating INT DEFAULT 5")
    except:
        pass # Column might already exist

    try:
        cursor.execute("ALTER TABLE bookings ADD COLUMN email VARCHAR(255)")
    except:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salaries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id INT,
            month VARCHAR(50),
            base_pay DECIMAL(10,2),
            overtime DECIMAL(10,2) DEFAULT 0.00,
            deductions DECIMAL(10,2) DEFAULT 0.00,
            status VARCHAR(50) DEFAULT 'Pending',
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"Failed to initialize database: {e}")

# --- Authentication Setup ---
# A hashed admin password for the college project. 
ADMIN_PASSWORD_HASH = generate_password_hash("admin")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to access the admin portal.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            flash("Logged in successfully!", "success")
            return redirect(url_for('admin_bookings'))
        else:
            flash("Incorrect password.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))
# --------------------------


# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# About Us Page
@app.route('/about')
def about():
    return render_template('about.html')

# Employees Page (ADMIN ONLY)
@app.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form.get('name')
        status = request.form.get('status', 'Active')
        join_date = request.form.get('join_date')
        if conn and name and join_date:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO employees (name, status, join_date) VALUES (%s, %s, %s)", (name, status, join_date))
            conn.commit()
            cursor.close()
            flash("Employee added successfully!", "success")
        else:
            flash("Name and Join Date are required.", "error")
        return redirect(url_for('employees'))

    employees_list = []
    total_staff = 0
    active_now = 0
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employees ORDER BY join_date DESC")
        employees_list = cursor.fetchall()
        cursor.close()
        conn.close()
        
        total_staff = len(employees_list)
        active_now = sum(1 for e in employees_list if e['status'] == 'Active')

    return render_template('employees.html', employees=employees_list, total_staff=total_staff, active_now=active_now)

@app.route('/employee/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Employee removed successfully.", "success")
    return redirect(url_for('employees'))

# Attendance Page (ADMIN ONLY)
@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    conn = get_db_connection()
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        ci_h = request.form.get('check_in_h')
        ci_m = request.form.get('check_in_m')
        ci_a = request.form.get('check_in_a')
        check_in = f"{ci_h}:{ci_m} {ci_a}" if (ci_h and ci_m and ci_a) else '--'
        
        co_h = request.form.get('check_out_h')
        co_m = request.form.get('check_out_m')
        co_a = request.form.get('check_out_a')
        check_out = f"{co_h}:{co_m} {co_a}" if (co_h and co_m and co_a) else '--'
        
        hours = request.form.get('hours', '--')
        location = request.form.get('location', '--')
        status = request.form.get('status', 'Present')
        log_date = request.form.get('log_date')
        if conn and employee_id:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT status FROM employees WHERE id=%s", (employee_id,))
            emp = cursor.fetchone()
            if not emp or emp['status'] != 'Active':
                flash("Cannot log attendance for inactive or on-leave employees.", "error")
                cursor.close()
                return redirect(url_for('attendance'))
                
            cursor = conn.cursor()
            cursor.execute("INSERT INTO attendance (employee_id, check_in, check_out, hours, location, status, log_date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (employee_id, check_in, check_out, hours, location, status, log_date))
            conn.commit()
            cursor.close()
            flash("Attendance logged successfully!", "success")
        return redirect(url_for('attendance'))

    attendance_logs = []
    employees_list = []
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, e.name as employee_name
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            ORDER BY a.log_date DESC, a.id DESC
        """)
        attendance_logs = cursor.fetchall()
        
        from datetime import datetime
        def format_time(time_str):
            if not time_str or time_str == '--':
                return '--'
            time_str = str(time_str)
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                return time_str
            try:
                if len(time_str) >= 5 and ':' in time_str:
                    parts = time_str.split(':')
                    t = datetime.strptime(f"{parts[0]}:{parts[1]}", '%H:%M')
                    return t.strftime('%I:%M %p')
            except:
                pass
            return time_str

        for log in attendance_logs:
            log['check_in'] = format_time(log.get('check_in')) if log.get('check_in') else '--'
            log['check_out'] = format_time(log.get('check_out')) if log.get('check_out') else '--'

        cursor.execute("SELECT id, name FROM employees WHERE status = 'Active'")
        employees_list = cursor.fetchall()
        cursor.close()
        conn.close()

    return render_template('attendance.html', attendance_logs=attendance_logs, employees=employees_list)

@app.route('/attendance/delete/<int:id>', methods=['POST'])
@login_required
def delete_attendance(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM attendance WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Attendance record removed.", "success")
    return redirect(url_for('attendance'))

@app.route('/attendance/edit/<int:id>', methods=['POST'])
@login_required
def edit_attendance(id):
    conn = get_db_connection()
    if request.method == 'POST':
        ci_h = request.form.get('check_in_h')
        ci_m = request.form.get('check_in_m')
        ci_a = request.form.get('check_in_a')
        check_in = f"{ci_h}:{ci_m} {ci_a}" if (ci_h and ci_m and ci_a) else '--'
        
        co_h = request.form.get('check_out_h')
        co_m = request.form.get('check_out_m')
        co_a = request.form.get('check_out_a')
        check_out = f"{co_h}:{co_m} {co_a}" if (co_h and co_m and co_a) else '--'
        
        hours = request.form.get('hours', '--')
        location = request.form.get('location', '--')
        status = request.form.get('status', 'Present')
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE attendance SET check_in=%s, check_out=%s, hours=%s, location=%s, status=%s WHERE id=%s",
                           (check_in, check_out, hours, location, status, id))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Attendance record updated.", "success")
    return redirect(url_for('attendance'))

# Salary Page (ADMIN ONLY)
@app.route('/salary', methods=['GET', 'POST'])
@login_required
def salary():
    conn = get_db_connection()
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        month = request.form.get('month')
        base_pay = request.form.get('base_pay', 0)
        overtime = request.form.get('overtime', 0)
        deductions = request.form.get('deductions', 0)
        status = request.form.get('status', 'Pending')
        if conn and employee_id:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO salaries (employee_id, month, base_pay, overtime, deductions, status) VALUES (%s, %s, %s, %s, %s, %s)",
                           (employee_id, month, base_pay, overtime, deductions, status))
            conn.commit()
            cursor.close()
            flash("Salary record added!", "success")
        return redirect(url_for('salary'))

    salary_records = []
    employees_list = []
    total_payout = 0
    cleared_pct = 0
    
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.*, e.name as employee_name, 
                   (s.base_pay + s.overtime - s.deductions) as net_salary
            FROM salaries s
            JOIN employees e ON s.employee_id = e.id
            ORDER BY s.id DESC
        """)
        salary_records = cursor.fetchall()
        
        cursor.execute("SELECT id, name FROM employees WHERE status = 'Active'")
        employees_list = cursor.fetchall()
        cursor.close()
        conn.close()
        
        total_payout = sum(float(r['net_salary']) for r in salary_records if r['status'] == 'Paid')
        total_records = len(salary_records)
        paid_records = sum(1 for r in salary_records if r['status'] == 'Paid')
        cleared_pct = int((paid_records / total_records * 100)) if total_records > 0 else 0

    return render_template('salary.html', salaries=salary_records, employees=employees_list, total_payout=total_payout, cleared_pct=cleared_pct)

@app.route('/salary/edit/<int:id>', methods=['POST'])
@login_required
def edit_salary(id):
    conn = get_db_connection()
    if request.method == 'POST':
        base_pay = float(request.form.get('base_pay', 0))
        overtime = float(request.form.get('overtime', 0))
        deductions = float(request.form.get('deductions', 0))
        status = request.form.get('status', 'Pending')
        net_salary = base_pay + overtime - deductions
        if conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE salaries SET base_pay=%s, overtime=%s, deductions=%s, net_salary=%s, status=%s WHERE id=%s",
                           (base_pay, overtime, deductions, net_salary, status, id))
            conn.commit()
            cursor.close()
            flash("Salary record updated.", "success")
    return redirect(url_for('salary'))

@app.route('/salary/delete/<int:id>', methods=['POST'])
@login_required
def delete_salary(id):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM salaries WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Salary record removed.", "success")
    return redirect(url_for('salary'))

# Services Page (Public)
@app.route('/services')
def services():
    return render_template('services.html')

# Bookings Page (Customer Side)
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form.get('customer_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        service = request.form.get('service', '').strip()
        date = request.form.get('date', '').strip()

        # Input Validation
        if not name or not email or not phone or not address or not service or not date:
            flash("All fields are required. Please fill them out completely.", "error")
            return redirect('/booking')
            
        if len(phone) != 10 or not phone.isdigit():
            flash("Please enter a valid 10-digit phone number.", "error")
            return redirect('/booking')
            
        import re
        if not re.match(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", email):
            flash("Please enter a valid email address (lowercase only).", "error")
            return redirect('/booking')

        # Save to MySQL database
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                sql = "INSERT INTO bookings (customer_name, email, phone, address, service_type, preferred_date) VALUES (%s, %s, %s, %s, %s, %s)"
                val = (name, email, phone, address, service, date)
                cursor.execute(sql, val)
                conn.commit()
                cursor.close()
                conn.close()
                flash("Booking successful! Our team will contact you shortly.", "success")
            else:
                flash("Sorry, there was an error connecting to the database.", "error")
        except Exception as e:
            print(f"Database error: {e}")
            flash("Sorry, there was an error processing your booking. Please try again.", "error")

        return redirect('/booking')

    return render_template('booking.html')

# Gallery Page (Public)
@app.route('/gallery')
def gallery():
    return render_template('gallery.html')


# Admin Side - View Bookings (ADMIN ONLY)
@app.route('/admin/bookings')
@login_required
def admin_bookings():
    bookings = []
    try:
        # Fetch all bookings from the MySQL database
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM bookings ORDER BY created_at DESC')
            bookings = cursor.fetchall()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")

    return render_template('admin_bookings.html', bookings=bookings)

# User Feedback Page (Public)
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        rating = request.form.get('rating', '5')
        
        if not name or not message:
            flash("Name and message are required.", "error")
            return redirect(url_for('feedback'))
            
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO feedbacks (name, email, message, rating) VALUES (%s, %s, %s, %s)", (name, email, message, rating))
                conn.commit()
                cursor.close()
                conn.close()
                flash("Thank you for your feedback!", "success")
            else:
                flash("Database connection error.", "error")
        except Exception as e:
            print(f"Feedback error: {e}")
            flash("Sorry, error processing feedback.", "error")
            
        return redirect(url_for('feedback'))
    return render_template('feedback.html')

# Admin Side - View Feedbacks (ADMIN ONLY)
@app.route('/admin/feedbacks')
@login_required
def admin_feedbacks():
    feedbacks = []
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM feedbacks ORDER BY created_at DESC')
            feedbacks = cursor.fetchall()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"Error reading feedbacks: {e}")
    return render_template('admin_feedbacks.html', feedbacks=feedbacks)


# Reports Page (ADMIN ONLY)
@app.route('/reports')
@login_required
def reports():
    conn = get_db_connection()
    stats = {
        'total_bookings': 0,
        'total_employees': 0,
        'active_employees': 0,
        'total_paid': 0
    }
    if conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) as c FROM bookings")
            stats['total_bookings'] = cursor.fetchone()['c']
        except:
            pass # Ignore if bookings table doesn't exist yet
            
        cursor.execute("SELECT COUNT(*) as c FROM employees")
        stats['total_employees'] = cursor.fetchone()['c']
        
        cursor.execute("SELECT COUNT(*) as c FROM employees WHERE status='Active'")
        stats['active_employees'] = cursor.fetchone()['c']
        
        cursor.execute("SELECT SUM(base_pay + overtime - deductions) as total FROM salaries WHERE status='Paid'")
        res = cursor.fetchone()
        stats['total_paid'] = res['total'] if res and res['total'] else 0
        
        try:
            cursor.execute("SELECT service_type, COUNT(*) as count FROM bookings GROUP BY service_type ORDER BY count DESC")
            stats['service_counts'] = cursor.fetchall()
            
            cursor.execute("SELECT address, COUNT(*) as count FROM bookings GROUP BY address ORDER BY count DESC LIMIT 10")
            top_locations = cursor.fetchall()
            for loc in top_locations:
                cursor.execute("SELECT customer_name, email, phone, service_type, preferred_date FROM bookings WHERE address = %s", (loc['address'],))
                loc['details'] = cursor.fetchall()
            stats['top_locations'] = top_locations
            
            cursor.execute("""
                SELECT customer_name, phone, COUNT(*) as total_bookings, 
                       GROUP_CONCAT(DISTINCT service_type SEPARATOR ', ') as services,
                       MIN(created_at) as first_booking, MAX(created_at) as latest_booking
                FROM bookings 
                GROUP BY customer_name, phone 
                ORDER BY total_bookings DESC 
                LIMIT 10
            """)
            stats['frequent_customers'] = cursor.fetchall()
        except:
            stats['service_counts'] = []
            stats['top_locations'] = []
            stats['frequent_customers'] = []
            
        cursor.close()
        conn.close()
    return render_template('reports.html', stats=stats)


if __name__ == '__main__':
    app.run(debug=True)
