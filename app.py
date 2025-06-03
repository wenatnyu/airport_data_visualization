from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sys
import pandas as pd
from werkzeug.utils import secure_filename
import subprocess
from airport_data import AirportData, load_all_airports
from sqlalchemy import text
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///airports.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    try:
        with app.app_context():
            db.create_all()
            print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Username and password are required', 'error')
                return redirect(url_for('signup'))
            
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'error')
                return redirect(url_for('signup'))
            
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error during signup: {str(e)}")
            flash('An error occurred during signup. Please try again.', 'error')
            return redirect(url_for('signup'))
    return render_template('signup.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard'))
    
    if file and file.filename.endswith(('.xlsx', '.xls')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Run the conversion script
            result = subprocess.run([sys.executable, './spreadsheet/convert_to_csv.py', filepath], 
                                 capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Conversion failed: {result.stderr}")
            
            # Get all CSV files in the uploads directory
            csv_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                        if f.endswith('.csv') and f != 'raw_data.csv']
            
            return render_template('csv_list.html', csv_files=csv_files, original_file=filename)
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('dashboard'))
    
    flash('Invalid file type. Please upload an Excel file.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/view_csv/<filename>')
@login_required
def view_csv(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df = pd.read_csv(filepath)
        columns = df.columns.tolist()
        data = df.values.tolist()
        return render_template('visualize.html', filename=filename, columns=columns, data=data)
    except Exception as e:
        flash(f'Error reading CSV file: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/view_xlsx/<filename>')
@login_required
def view_xlsx(filename):
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # 读取Excel文件
        df = pd.read_excel(filepath)
        columns = df.columns.tolist()
        data = df.values.tolist()
        return render_template('visualize_xlsx.html', filename=filename, columns=columns, data=data)
    except Exception as e:
        flash(f'Error reading Excel file: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/process_selected_files', methods=['POST'])
@login_required
def process_selected_files():
    selected_files = request.form.getlist('selected_files')
    if not selected_files:
        flash('Please select at least one file', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Load selected files as AirportData objects
        airports = []
        for filename in selected_files:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            airport = AirportData(filepath)
            print(f"Processing {filename}:")
            print(f"First row of data: {airport.data[0]}")
            print(f"Data types: {[type(x) for x in airport.data[0]]}")
            airports.append(airport)
            
            # Create table for each airport
            create_airport_table(airport)
            
            # Insert data into the table
            insert_airport_data(airport)
        
        return redirect(url_for('ap_database'))
    except Exception as e:
        flash(f'Error processing files: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

def create_airport_table(airport):
    try:
        # Create table with appropriate columns
        columns = []
        # First column is date
        columns.append(f"date DATE")
        
        # Next 6 columns are integers (航班架次 and 旅客人数)
        for i in range(1, 7):
            field_name = airport.fields[i].replace(' ', '_').replace('（', '').replace('）', '').replace('吨', '')
            columns.append(f'"{field_name}" INTEGER')
        
        # Last 3 columns are floats (货邮重量)
        for i in range(7, 10):
            field_name = airport.fields[i].replace(' ', '_').replace('（', '').replace('）', '').replace('吨', '')
            columns.append(f'"{field_name}" FLOAT')
        
        with db.engine.connect() as conn:
            # First drop the table if it exists
            drop_sql = f'DROP TABLE IF EXISTS "{airport.name}"'
            print(f"Dropping table with SQL: {drop_sql}")
            conn.execute(text(drop_sql))
            conn.commit()
            
            # Then create the new table
            create_sql = f"""
            CREATE TABLE "{airport.name}" (
                {', '.join(columns)}
            )
            """
            print(f"Creating table with SQL: {create_sql}")
            conn.execute(text(create_sql))
            conn.commit()
            
            # Verify table creation
            result = conn.execute(text(f"PRAGMA table_info('{airport.name}')"))
            columns = [row[1] for row in result]
            print(f"Created table columns: {columns}")
            
    except Exception as e:
        print(f"Error creating table: {str(e)}")
        raise

def insert_airport_data(airport):
    try:
        # Convert data to list of tuples for insertion
        data_to_insert = []
        for row_idx, row in enumerate(airport.data):
            try:
                # Convert datetime to string in SQLite compatible format
                date_str = row[0].strftime('%Y-%m-%d')
                
                # Create a new tuple with the date string and the rest of the values
                # Ensure all values are of the correct type
                new_row = [date_str]
                
                # Add integer values (columns 1-6)
                for i in range(1, 7):
                    try:
                        value = int(row[i])
                        new_row.append(value)
                    except (ValueError, TypeError) as e:
                        print(f"Error converting integer at row {row_idx}, col {i}: {e}")
                        new_row.append(0)
                
                # Add float values (columns 7-9)
                for i in range(7, 10):
                    try:
                        value = float(row[i])
                        new_row.append(value)
                    except (ValueError, TypeError) as e:
                        print(f"Error converting float at row {row_idx}, col {i}: {e}")
                        new_row.append(0.0)
                
                data_to_insert.append(tuple(new_row))
            except Exception as e:
                print(f"Error processing row {row_idx}: {e}")
                continue
        
        if not data_to_insert:
            raise ValueError("No valid data to insert")
        
        # Create insert statement with proper field names
        field_names = ['date']
        for i in range(1, 7):
            field_name = airport.fields[i].replace(' ', '_').replace('（', '').replace('）', '').replace('吨', '')
            field_names.append(f'"{field_name}"')
        for i in range(7, 10):
            field_name = airport.fields[i].replace(' ', '_').replace('（', '').replace('）', '').replace('吨', '')
            field_names.append(f'"{field_name}"')
        
        # Create parameterized query
        params = [f":param{i}" for i in range(len(field_names))]
        insert_sql = f'INSERT INTO "{airport.name}" ({", ".join(field_names)}) VALUES ({", ".join(params)})'
        
        print(f"SQL: {insert_sql}")
        print(f"First row to insert: {data_to_insert[0]}")
        
        # Insert data using executemany
        with db.engine.connect() as conn:
            # Then insert new data
            for row in data_to_insert:
                param_dict = {f"param{i}": value for i, value in enumerate(row)}
                conn.execute(text(insert_sql), param_dict)
            conn.commit()
            
    except Exception as e:
        print(f"Error in insert_airport_data: {str(e)}")
        raise

@app.route('/ap_database')
@login_required
def ap_database():
    # Get list of tables (airports)
    with db.engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = []
        for row in result:
            table_name = row[0]
            # Get table schema
            schema = conn.execute(text(f"PRAGMA table_info('{table_name}')"))
            fields = [col[1] for col in schema]
            tables.append({'name': table_name, 'fields': fields})
    
    return render_template('ap_database.html', tables=tables)

@app.route('/execute_query', methods=['POST'])
@login_required
def execute_query():
    query = request.form.get('query', '').strip()
    if not query:
        flash('Please enter a query', 'error')
        return redirect(url_for('ap_database'))
    
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            results = [row for row in result]
            
            # Get tables for the template
            tables_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = []
            for row in tables_result:
                table_name = row[0]
                schema = conn.execute(text(f"PRAGMA table_info('{table_name}')"))
                fields = [col[1] for col in schema]
                tables.append({'name': table_name, 'fields': fields})
            
            return render_template('ap_database.html', 
                                tables=tables,
                                results=results,
                                columns=columns)
    except Exception as e:
        flash(f'Error executing query: {str(e)}', 'error')
        return redirect(url_for('ap_database'))

@app.route('/line_chart')
@login_required
def line_chart():
    # Get list of tables and their fields
    with db.engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = []
        all_fields = set()
        
        for row in result:
            table_name = row[0]
            # 跳过 user 表
            if table_name == 'user':
                continue
                
            # Get table schema
            schema = conn.execute(text(f"PRAGMA table_info('{table_name}')"))
            fields = [col[1] for col in schema]
            tables.append({'name': table_name, 'fields': fields})
            # 添加所有字段到集合中
            all_fields.update(fields)
        
        # 找出所有表格共有的字段
        common_fields = []
        for field in all_fields:
            # 检查该字段是否在所有表格中都存在
            if all(field in table['fields'] for table in tables):
                common_fields.append(field)
        
        print(f"Tables: {[t['name'] for t in tables]}")  # 调试信息
        print(f"Common fields: {common_fields}")  # 调试信息
    
    return render_template('line_chart.html', tables=tables, common_fields=common_fields)

@app.route('/get_chart_data', methods=['POST'])
@login_required
def get_chart_data():
    try:
        data = request.get_json()
        tables = data.get('tables', [])
        field = data.get('field')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not all([tables, field, start_date, end_date]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Query data for each table
        datasets = []
        all_dates = set()  # 用于收集所有日期
        
        with db.engine.connect() as conn:
            # 首先获取所有日期
            for table in tables:
                query = text(f"""
                    SELECT DISTINCT date
                    FROM "{table}"
                    WHERE date BETWEEN :start_date AND :end_date
                    ORDER BY date
                """)
                
                result = conn.execute(query, {
                    'start_date': start_date,
                    'end_date': end_date
                })
                
                for row in result:
                    all_dates.add(row[0])
            
            # 将日期转换为列表并排序
            all_dates = sorted(list(all_dates))
            
            # 然后获取每个表的数据
            for table in tables:
                query = text(f"""
                    SELECT date, "{field}"
                    FROM "{table}"
                    WHERE date BETWEEN :start_date AND :end_date
                    ORDER BY date
                """)
                
                result = conn.execute(query, {
                    'start_date': start_date,
                    'end_date': end_date
                })
                
                # 创建日期到值的映射，确保值为数值类型
                date_value_map = {}
                for row in result:
                    try:
                        # 尝试将值转换为浮点数
                        value = float(row[1]) if row[1] is not None else None
                        date_value_map[row[0]] = value
                    except (ValueError, TypeError):
                        print(f"Warning: Could not convert value {row[1]} to number for table {table}")
                        date_value_map[row[0]] = None
                
                # 为所有日期创建数据点，如果某天没有数据则使用null
                values = []
                for date in all_dates:
                    values.append(date_value_map.get(date))
                
                datasets.append({
                    'label': table,
                    'data': values
                })
        
        print(f"Generated datasets: {datasets}")  # 调试信息
        return jsonify({
            'labels': all_dates,
            'datasets': datasets
        })
        
    except Exception as e:
        print(f"Error in get_chart_data: {str(e)}")  # 添加错误日志
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize the database
    init_db()
    app.run(debug=True) 