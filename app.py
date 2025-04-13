from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import psycopg2
import psycopg2.extras
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os

load_dotenv()  # This loads the variables from the .env file

DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask(__name__)
app.secret_key = 'karthik57'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            account_type TEXT,
            phone TEXT,
            business_type TEXT,
            location TEXT,
            bio TEXT,
            price TEXT,
            profile_pic TEXT
        );
    ''')
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id SERIAL PRIMARY KEY,
                to_user TEXT NOT NULL,
                from_user TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                reply TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                reported_user TEXT NOT NULL,
                reported_by TEXT NOT NULL,
                reason TEXT NOT NULL
            );
        """)
        conn.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'adime' and password == 'adime123':
            session['username'] = username
            return redirect(url_for('admin_dashboard'))

        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()
            if user:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return "Invalid username or password"
    return render_template('login.html')

@app.route('/home')
def home():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT business_type FROM users WHERE account_type='business'")
        services_from_db = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT username FROM users WHERE account_type='business'")
        business_usernames = [row[0] for row in cursor.fetchall()]

    predefined_services = [
        'House Cleaning', 'Kitchen Cleaning', 'Bathroom Cleaning', 'Room Cleaning',
        'Plumbing', 'Motor Repair', 'Electrician', 'Two wheeler', 'Three wheeler',
        'Four wheeler', 'Heavy Vehicle'
    ]
    all_services = list(set(services_from_db + predefined_services))
    random.shuffle(all_services)
    random_services = all_services[:6]
    service_images = {
        'House Cleaning': 'house_cleaning.jpg',
        'Kitchen Cleaning': 'kitchen_cleaning.jpg',
        'Bathroom Cleaning': 'bathroom_cleaning.jpg',
        'Room Cleaning': 'house_cleaning.jpg',
        'Plumbing': 'plumbing.jpg',
        'Motor Repair': 'house_cleaning.png',
        'Electrician': 'electrician.jpg',
        'Two wheeler': 'two_wheeler.jpg',
        'Three wheeler': 'three_wheeler.jpg',
        'Four wheeler': 'four_wheeler.jpg',
        'Heavy Vehicle': 'heavy_vechile.jpg'
    }
    random_service_images = {service: service_images.get(service, '') for service in random_services}
    return render_template('home.html', services=random_services, service_images=random_service_images, business_usernames=business_usernames)

@app.route('/admin')
def admin_dashboard():
      if 'username' not in session or session['username'] != 'adime':
          return redirect(url_for('login'))

      with get_db_connection() as conn:
          cursor = conn.cursor()
          
          # Changed SQL queries to use %s placeholders for PostgreSQL compatibility
          cursor.execute("SELECT * FROM users WHERE username != %s", ('adime',))
          users = cursor.fetchall()

          cursor.execute("SELECT reported_user, COUNT(*) as report_count FROM reports GROUP BY reported_user")
          reported_users = cursor.fetchall()

      return render_template('adime.html', users=users, reported_users=reported_users)

@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    if 'username' not in session or session['username'] != 'adime':
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("DELETE FROM users WHERE username = %s", (username,))
        conn.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup/business', methods=['GET', 'POST'])
def signup_business():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        business_type = request.form['business_type']
        location = request.form['location']
        bio = request.form.get('bio', '')
        price = request.form.get('price', '')
        profile_pic_file = request.files.get('profile_pic')
        filename = ''
        if profile_pic_file and allowed_file(profile_pic_file.filename):
            filename = secure_filename(profile_pic_file.filename)
            profile_pic_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Updated query to use %s placeholders for PostgreSQL
            cursor.execute("INSERT INTO users (username, password, account_type, phone, business_type, location, bio, price, profile_pic) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                           (username, password, 'business', phone, business_type, location, bio, price, filename))
            conn.commit()
        return redirect(url_for('login'))
    return render_template('signup_business.html')
@app.route('/signup/user', methods=['GET', 'POST'])
def signup_user():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        profile_pic_file = request.files.get('profile_pic')
        filename = ''
        if profile_pic_file and allowed_file(profile_pic_file.filename):
            filename = secure_filename(profile_pic_file.filename)
            profile_pic_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Updated query to use %s placeholder for PostgreSQL
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                error = "Username already exists. Please choose a different one."
            else:
                try:
                    # Updated query to use %s placeholder for PostgreSQL
                    cursor.execute("INSERT INTO users (username, password, account_type, phone, profile_pic) VALUES (%s, %s, %s, %s, %s)", 
                                   (username, password, 'user', phone, filename))
                    conn.commit()
                    return redirect(url_for('login'))
                except psycopg2.IntegrityError:
                    error = "An error occurred. Please try again."
    return render_template('signup_user.html', error=error)

@app.route('/profile')
@app.route('/profile/<username>')
def profile(username=None):
    if username is None:
        if 'username' not in session:
            return redirect(url_for('login'))
        username = session['username']

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT * FROM feedback WHERE to_user = %s", (username,))
        feedback = cursor.fetchall()

        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT * FROM reports WHERE reported_user = %s", (username,))
        reports = cursor.fetchall()

        is_owner = session.get('username') == username
        is_admin = session.get('username') == 'adime'

        has_rated = False
        if 'username' in session:
            # Updated query to use %s placeholder for PostgreSQL
            cursor.execute("SELECT * FROM feedback WHERE to_user = %s AND from_user = %s", (username, session['username']))
            has_rated = cursor.fetchone() is not None

    return render_template('profile.html', user=user, feedback=feedback, reports=reports,
                           is_owner=is_owner, is_admin=is_admin, has_rated=has_rated)
@app.route('/reply_comment/<int:feedback_id>', methods=['POST'])
def reply_comment(feedback_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    reply = request.form['reply']
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("UPDATE feedback SET reply = %s WHERE id = %s", (reply, feedback_id))
        conn.commit()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT to_user FROM feedback WHERE id = %s", (feedback_id,))
        username = cursor.fetchone()['to_user']
    return redirect(url_for('profile', username=username))

@app.route('/rate_comment/<username>', methods=['POST'])
def rate_comment(username):
    if 'username' not in session:
        return redirect(url_for('login'))
    current_user = session['username']
    rating = int(request.form['rating'])
    comment = request.form['comment']

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT * FROM feedback WHERE to_user = %s AND from_user = %s", (username, current_user))
        existing = cursor.fetchone()
        if existing:
            return "You already rated. Delete to re-rate."
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("INSERT INTO feedback (to_user, from_user, rating, comment) VALUES (%s, %s, %s, %s)",
                       (username, current_user, rating, comment))
        conn.commit()
    return redirect(url_for('profile', username=username))

@app.route('/delete_rating/<username>', methods=['POST'])
def delete_rating(username):
    if 'username' not in session:
        return redirect(url_for('login'))
    current_user = session['username']
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("DELETE FROM feedback WHERE to_user = %s AND from_user = %s", (username, current_user))
        conn.commit()
    return redirect(url_for('profile', username=username))

@app.route('/report_user/<username>', methods=['POST'])
def report_user(username):
    if 'username' not in session:
        return redirect(url_for('login'))

    reported_by = session['username']
    reason = request.form['reason']

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("INSERT INTO reports (reported_user, reported_by, reason) VALUES (%s, %s, %s)",
                       (username, reported_by, reason))
        conn.commit()

    return redirect(url_for('profile', username=username))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            new_bio = request.form.get('bio', '')
            new_price = request.form.get('price', '')
            # Updated query to use %s placeholder for PostgreSQL
            cursor.execute("UPDATE users SET bio = %s, price = %s WHERE username = %s", 
                           (new_bio, new_price, username))
            conn.commit()
            return redirect(url_for('profile'))

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

    return render_template('edit_profile.html', user=user)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT DISTINCT business_type FROM users WHERE account_type = 'business' AND LOWER(business_type) LIKE %s", 
                       ('%' + query + '%',))
        service_results = cursor.fetchall()

        cursor.execute("""SELECT * FROM users 
                          WHERE account_type = 'business' 
                          AND (LOWER(username) LIKE %s OR LOWER(location) LIKE %s OR LOWER(business_type) LIKE %s)""",
                       ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
        business_results = cursor.fetchall()
    
    return render_template('search.html', query=query, service_results=service_results, business_results=business_results)

@app.route('/suggest')
def suggest():
    term = request.args.get('term', '').lower()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT DISTINCT business_type FROM users WHERE LOWER(business_type) LIKE %s", ('%' + term + '%',))
        services = [row['business_type'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT username FROM users WHERE LOWER(username) LIKE %s", ('%' + term + '%',))
        users = [row['username'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT location FROM users WHERE LOWER(location) LIKE %s", ('%' + term + '%',))
        locations = [row['location'] for row in cursor.fetchall()]
    
    return jsonify(list(set(services + users + locations)))


@app.route('/service/<service_name>')
def service(service_name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Updated query to use %s placeholder for PostgreSQL
        cursor.execute("SELECT * FROM users WHERE account_type = 'business' AND business_type = %s", (service_name,))
        businesses = cursor.fetchall()
    
    return render_template('service.html', businesses=businesses, service_name=service_name)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
