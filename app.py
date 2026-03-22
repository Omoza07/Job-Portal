from flask import Flask, render_template, request, redirect, session
import sqlite3, os
import PyPDF2

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- RESUME PARSER ----------------
def parse_resume(filepath):
    text = ""
    try:
        with open(filepath, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
    except:
        text = "Parsing Failed"
    return text

# ---------------- HOME ----------------
@app.route('/')
def home():
    conn = get_db()
    jobs = conn.execute("SELECT * FROM jobs").fetchall()
    conn.close()
    return render_template('index.html', jobs=jobs)

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        conn.execute(
            "INSERT INTO users(name,email,password,role) VALUES (?,?,?,?)",
            (request.form['name'], request.form['email'],
             request.form['password'], request.form['role'])
        )
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (request.form['email'], request.form['password'])
        ).fetchone()
        conn.close()

        if user:
            session['user'] = user['name']
            session['user_id'] = user['id']
            session['role'] = user['role']
            return redirect('/dashboard')
        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    if session['role'] == 'employer':
        jobs = conn.execute(
            "SELECT * FROM jobs WHERE employer=?",
            (session['user'],)
        ).fetchall()

        apps = conn.execute("""
        SELECT applications.*, users.name, jobs.title 
        FROM applications
        JOIN users ON users.id = applications.user_id
        JOIN jobs ON jobs.id = applications.job_id
        """).fetchall()

        conn.close()
        return render_template('dashboard.html', jobs=jobs, apps=apps, role="employer")

    else:
        apps = conn.execute("""
        SELECT jobs.id, jobs.title, applications.status, applications.interview_date
        FROM applications
        JOIN jobs ON jobs.id = applications.job_id
        WHERE applications.user_id=?
        """, (session['user_id'],)).fetchall()

        jobs = conn.execute("SELECT * FROM jobs").fetchall()

        conn.close()
        return render_template('dashboard.html', apps=apps, jobs=jobs, role="user")

# ---------------- POST JOB ----------------
@app.route('/post_job', methods=['POST'])
def post_job():
    if 'user' not in session or session['role'] != 'employer':
        return redirect('/login')

    conn = get_db()
    conn.execute(
        "INSERT INTO jobs(title,description,employer) VALUES (?,?,?)",
        (request.form['title'], request.form['desc'], session['user'])
    )
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# ---------------- APPLY ----------------
@app.route('/apply/<int:job_id>', methods=['GET','POST'])
def apply(job_id):

    if 'user' not in session:
        return redirect('/login')

    conn = get_db()

    existing = conn.execute(
        "SELECT * FROM applications WHERE user_id=? AND job_id=?",
        (session['user_id'], job_id)
    ).fetchone()

    if existing:
        conn.close()
        return "Already Applied ✅"

    if request.method == 'POST':
        file = request.files['resume']
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        parsed_text = parse_resume(filepath)

        conn.execute(
            "INSERT INTO applications(user_id,job_id,resume,parsed_text) VALUES (?,?,?,?)",
            (session['user_id'], job_id, filepath, parsed_text)
        )
        conn.commit()
        conn.close()

        return redirect('/dashboard')

    conn.close()
    return render_template('apply.html')

# ---------------- SCHEDULE ----------------
@app.route('/schedule/<int:app_id>', methods=['GET','POST'])
def schedule(app_id):
    if request.method == 'POST':
        conn = get_db()
        conn.execute("""
        UPDATE applications
        SET interview_date=?, status='Interview Scheduled'
        WHERE id=?
        """, (request.form['date'], app_id))
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    return render_template('schedule.html')

# ---------------- ANALYTICS ----------------
@app.route('/analytics')
def analytics():
    conn = get_db()
    jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    conn.close()

    return render_template('analytics.html', jobs=jobs, apps=apps)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)