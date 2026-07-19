from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "my_secret_key_123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        cnic TEXT,
        department TEXT,
        semester TEXT,
        enrolled_year TEXT,
        profile_photo TEXT,
        roll_no TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        bot_response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        student_name TEXT,
        message TEXT,
        reply TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS university_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        message TEXT,
        category TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
   # Quiz table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id INTEGER,
        title TEXT,
        type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # QUESTIONS TABLE (🔥 THIS WAS MISSING ISSUE)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        question TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_answer TEXT
    )
    """)

    # Results
    cur.execute("""
    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        score INTEGER,
        total INTEGER,
        percentage REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =========================
# DB CONNECT
# =========================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# ROUTER
# =========================
def route_query(query):
    query = query.lower().strip()

    # Fees
    if "fee" in query or "fees" in query or "fee structure" in query:
        return (
            "💰 University Fee Information\n\n"
            "• 1st Semester Fee: Payable in May.\n"
            "• 2nd Semester Fee: Payable in December.\n"
            "• Fee can be submitted before the due date mentioned by the university.\n"
            "• Contact the Accounts Office for fee vouchers and payment details."
        )

    # Admission
    elif "admission" in query or "apply" in query:
        return (
            "📚 Admission Information\n\n"
            "• Admissions usually open in September–October.\n"
            "• Apply through the university admission portal.\n"
            "• Required documents: CNIC/B-Form, academic certificates, photographs, and admission form."
        )

    # Courses
    elif "course" in query or "courses" in query or "subjects" in query:
        return (
            "🎓 Programs Offered\n\n"
            "• BS Computer Science (BSCS)\n"
            "• BS Artificial Intelligence (BSAI)\n"
            "• BS Data Science (BSDS)\n"
            "For complete course details, contact your department."
        )

    # Results
    elif "result" in query or "results" in query:
        return (
            "📊 Result Information\n\n"
            "Results are usually announced within 2 weeks after the completion of examinations."
        )

    # Timetable
    elif "timetable" in query or "schedule" in query or "class timing" in query:
        return (
            "🗓️ Class Schedule\n\n"
            "Please check your department notice board or university official group  for the latest timetable."
        )

    # Attendance
    elif "attendance" in query:
        return (
            "✅ Attendance Policy\n\n"
            "Students are required to maintain at least 75% attendance to be eligible for examinations."
        )

    # Contact
    elif "contact" in query or "office" in query:
        return (
            "☎️ University Contact\n\n"
            "Visit the Administration Office during working hours for assistance regarding admissions, fees, results, or other academic matters."
        )

    # Greeting
    elif query in ["hi", "hello", "hey", "assalam o alaikum", "assalamualaikum"]:
        return (
            "👋 Hello! Welcome to the University AI Assistant.\n\n"
            "How can I help you today?\n\n"
            "You can ask about:\n"
            "• Fees\n"
            "• Admissions\n"
            "• Courses\n"
            "• Results\n"
            "• Timetable\n"
            "• Attendance"
        )

    # Default
    else:
        return (
            "🤖 Sorry, I couldn't understand your question.\n\n"
            "You can ask about:\n"
            "• Fees\n"
            "• Admissions\n"
            "• Courses\n"
            "• Results\n"
            "• Timetable\n"
            "• Attendance"
        )
# =========================
# HOME
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# =========================
# CHAT API
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(force=True)
        print("Received:", data)

        user_message = data.get("query", "")

        bot_reply = route_query(user_message)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO chat_history (user_message, bot_response) VALUES (?, ?)",
            (user_message, bot_reply)
        )

        conn.commit()
        conn.close()

        return jsonify({"response": bot_reply})

    except Exception as e:
        print("CHAT ERROR:", e)
        return jsonify({"response": str(e)}), 500

# =========================
# LOGIN (ADMIN)
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "admin" and request.form.get("password") == "admin123":
            session["admin"] = True
            return redirect("/admin")
        return "❌ Invalid login"
    return render_template("login.html")
# =========================
# ADMIN DASHBOARD
# =========================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM university_info ORDER BY id DESC")
    announcements = cur.fetchall()

    cur.execute("SELECT * FROM chat_history ORDER BY id DESC")
    chats = cur.fetchall()

    cur.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM students")
    total_users = cur.fetchone()[0]

    conn.close()

    return render_template(
        "admin_panel.html",
        announcements=announcements,
        chats=chats,
        complaints=complaints,
        total_users=total_users
    )


# =========================
# USERS PAGE
# =========================
@app.route("/admin/users")
def admin_users():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY id ASC")
    users = cur.fetchall()

    conn.close()

    return render_template("admin_users.html", users=users)


# =========================
# ANNOUNCEMENTS PAGE
# =========================
@app.route("/admin/announcements")
def admin_announcements():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM university_info ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()

    return render_template("admin_announcements.html", data=data)
# admin/add_announcement
@app.route("/admin/add_announcement", methods=["POST"])
def add_announcement():

    title = request.form.get("title")
    message = request.form.get("message")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO university_info (title, message, category)
        VALUES (?, ?, ?)
    """, (title, message, "announcement"))

    conn.commit()
    conn.close()

    return redirect("/admin/dashboard")
# edit announcement
@app.route("/admin/edit_announcement/<int:id>", methods=["GET", "POST"])
def edit_announcement(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        message = request.form["message"]
        category = request.form["category"]

        cur.execute("""
            UPDATE university_info
            SET title=?, message=?, category=?
            WHERE id=?
        """, (title, message, category, id))

        conn.commit()
        conn.close()
        return redirect("/admin/announcements")

    # GET request
    cur.execute("SELECT * FROM university_info WHERE id=?", (id,))
    info = cur.fetchone()
    conn.close()

    return render_template("edit_info.html", info=info)


# =========================
# DELETE ANNOUNCEMENT
# =========================
@app.route("/admin/delete_announcement/<int:id>")
def delete_announcement(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM university_info WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin/announcements")


# =========================
# CHAT PAGE
# =========================
@app.route("/admin/chats")
def admin_chats():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
SELECT *
FROM chat_history
ORDER BY id ASC
""")
    chats = cur.fetchall()

    conn.close()

    return render_template("admin_chats.html", chats=chats)


# =========================
# COMPLAINTS PAGE
# =========================
@app.route("/admin/complaints")
def admin_complaints():
    if not session.get("admin"):
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM complaints ORDER BY id DESC")
    complaints = cur.fetchall()

    conn.close()

    return render_template("admin_complaints.html", complaints=complaints)


# =========================
# REPLY COMPLAINT
# =========================
@app.route("/admin/reply/<int:id>", methods=["POST"])
def admin_reply(id):
    if not session.get("admin"):
        return redirect("/login")

    reply = request.form.get("reply")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE complaints
        SET reply=?
        WHERE id=?
    """, (reply, id))

    conn.commit()
    conn.close()

    return redirect("/admin/complaints")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# TEACHER REGISTER
# =========================
@app.route("/teacher/register", methods=["GET", "POST"])
def teacher_register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        department = request.form.get("department")
        course_title = request.form.get("course_title")
        course_code = request.form.get("course_code")

        conn = get_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Check email already exists
        cur.execute(
            "SELECT id FROM teachers WHERE email=?",
            (email,)
        )

        if cur.fetchone():
            conn.close()
            return "Teacher already registered."

        cur.execute("""
            INSERT INTO teachers
            (
                name,
                email,
                password,
                department,
                course_title,
                course_code
            )
            VALUES (?,?,?,?,?,?)
        """,
        (
            name,
            email,
            password,
            department,
            course_title,
            course_code
        ))

        conn.commit()
        conn.close()

        return redirect("/teacher/login")

    return render_template("teacher_register.html")
# =========================
# TEACHER LOGIN
# =========================
from flask import Flask, render_template, request, redirect, session

# baqi code yahan se start
@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM teachers WHERE email=? AND password=?",
            (email, password)
        )

        teacher = cur.fetchone()
        conn.close()

        if teacher:
            session["teacher_id"] = teacher[0]
            session["teacher_name"] = teacher[1]
            session["teacher_email"] = teacher[2]

            return redirect("/teacher/dashboard")

        return "Invalid login"

    return render_template("teacher_login.html")
# =========================
# DASHBOARD
# =========================
@app.route("/teacher/dashboard")
def teacher_dashboard():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    return render_template("teacher_dashboard.html")

# =========================
# NOTES UPLOAD
# =========================
@app.route("/teacher/notes/start")
def notes_start():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    return redirect("/teacher/upload")
app.config["UPLOAD_FOLDER"] = "static/uploads"


@app.route("/teacher/upload", methods=["GET", "POST"])
def upload_notes():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    if request.method == "POST":

        title = request.form.get("title")
        file = request.files.get("file")

        if file and file.filename != "":

            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            file.save(path)

            conn = sqlite3.connect("database.db")
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO notes (title, file_path, teacher_id)
                VALUES (?, ?, ?)
            """, (title, path, session["teacher_id"]))

            conn.commit()
            conn.close()

            return redirect("/teacher/notes")

    return render_template("upload_notes.html")


@app.route("/teacher/notes")
def view_notes():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT title, file_path
        FROM notes
        WHERE teacher_id=?
    """, (session["teacher_id"],))

    notes = cur.fetchall()
    conn.close()

    return render_template("view_notes.html", notes=notes)
# profile
@app.route("/teacher/profile", methods=["GET", "POST"])
def teacher_profile():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    conn = get_db()
    conn.row_factory = sqlite3.Row

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        course_title = request.form["course_title"]
        course_code = request.form["course_code"]
        department = request.form["department"]

        conn.execute("""
            UPDATE teachers
            SET
                name=?,
                email=?,
                course_title=?,
                course_code=?,
                department=?
            WHERE id=?
        """, (
            name,
            email,
            course_title,
            course_code,
            department,
            session["teacher_id"]
        ))

        conn.commit()

    teacher = conn.execute("""
        SELECT *
        FROM teachers
        WHERE id=?
    """, (session["teacher_id"],)).fetchone()

    conn.close()

    return render_template(
        "teacher_profile.html",
        teacher=teacher
    )
# =========================
# STUDENTS LIST
# =========================
@app.route("/teacher/students")
def teacher_students():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM students")
    students = cur.fetchall()

    conn.close()

    return render_template("teacher_students.html", students=students)

# attendence 
@app.route("/teacher/attendance", methods=["GET", "POST"])
def teacher_attendance():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")


    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()



    # ==========================
    # LOAD SEMESTER 7 SUBJECTS
    # ==========================

    cur.execute("""
        SELECT course_title
        FROM courses
        WHERE semester=7
        ORDER BY course_title
    """)

    subjects = cur.fetchall()



    # ==========================
    # SUBJECT SELECTED
    # ==========================

    if request.method == "POST" and "student_id" not in request.form:

        session["selected_subject"] = request.form["subject"]

        conn.close()

        return redirect("/teacher/attendance")



    # ==========================
    # SAVE ATTENDANCE
    # ==========================

    if request.method == "POST" and "student_id" in request.form:


        student_id = request.form["student_id"]

        status = request.form["status"]

        subject = session.get("selected_subject")



        cur.execute(
            "SELECT * FROM students WHERE id=?",
            (student_id,)
        )


        student = cur.fetchone()



        if student:


            cur.execute("""
                INSERT INTO attendance
                (
                    student_id,
                    teacher_id,
                    roll_no,
                    name,
                    subject,
                    date,
                    status
                )

                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    datetime('now'),
                    ?
                )

            """,

            (

                student["id"],
                session["teacher_id"],
                student["roll_no"],
                student["name"],
                subject,
                status

            ))


            conn.commit()



        conn.close()

        return redirect("/teacher/attendance")





    # ==========================
    # LOAD STUDENTS
    # ==========================

    cur.execute("""
        SELECT *
        FROM students
    """)

    students = cur.fetchall()





    # ==========================
    # LOAD RECORDS
    # ==========================

    cur.execute("""
        SELECT
            id,
            subject,
            roll_no,
            name,
            date,
            status

        FROM attendance

        ORDER BY id DESC

    """)


    records = cur.fetchall()



    conn.close()



    return render_template(
        "teacher_attendance.html",
        students=students,
        records=records,
        subjects=subjects,
        selected_subject=session.get("selected_subject","")
    )
# teacher/assignment-pane
@app.route("/teacher/assignment-panel")
def assignment_panel():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    return render_template("assignment_panel.html")
# teacher/create-assignment
@app.route("/teacher/create-assignment", methods=["GET", "POST"])
def create_assignment():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    if request.method == "POST":

        title = request.form.get("title")
        description = request.form.get("description")
        due_date = request.form.get("due_date")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO assignments (title, description, due_date)
            VALUES (?, ?, ?)
        """, (title, description, due_date))

        conn.commit()
        conn.close()

        return redirect("/teacher/assignments")

    return render_template("create_assignment.html")

@app.route("/teacher/delete-assignment/<int:id>")
def delete_assignment(id):

    print("DELETE HIT:", id)  # 🔥 check terminal

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM assignments WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/teacher/assignments")
# view assignment 
@app.route("/teacher/assignments")
def teacher_assignments():

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM assignments")
    assignments = cur.fetchall()

    print("ASSIGNMENTS:", assignments)  # 🔥 MUST SEE THIS

    conn.close()

    return render_template("teacher_assignments.html", assignments=assignments)

@app.route("/teacher/student-assignments")
def teacher_student_assignments():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    conn = get_db()

    submissions = conn.execute("""
        SELECT
            submissions.file_path,
            submissions.submitted_at,
            students.name,
            students.roll_no
        FROM submissions
        JOIN students
            ON submissions.student_id = students.id
        ORDER BY submissions.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "student_assignments.html",
        submissions=submissions
    )
# =========================
# ANNOUNCEMENTS
# =========================
@app.route("/teacher/announcements")
def teacher_announcements():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT title, message
        FROM announcements
        ORDER BY id DESC
    """)

    announcements = cur.fetchall()

    conn.close()

    return render_template(
        "teacher_announcements.html",
        announcements=announcements
    )

#teacher/doubts 
@app.route("/teacher/doubts")
def teacher_doubts():

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM doubts
        ORDER BY id DESC
    """)

    doubts = cur.fetchall()
    conn.close()

    return render_template("teacher_doubts.html", doubts=doubts)

@app.route("/teacher/reply-doubt/<int:id>", methods=["POST"])
def reply_doubt(id):

    if not session.get("teacher_id"):
        return redirect("/teacher/login")

    reply = request.form.get("reply")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        UPDATE doubts
        SET reply=?
        WHERE id=?
    """, (reply, id))

    conn.commit()
    conn.close()

    return redirect("/teacher/doubts")


# =========================
# LOGOUT
# =========================
@app.route("/teacher/logout")
def teacher_logout():
    session.clear()
    return redirect("/teacher/login")
# =========================
# REGISTER
# =========================
@app.route("/student/register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        cnic = request.form.get("cnic")
        department = request.form.get("department")
        semester = request.form.get("semester")
        enrolled_year = request.form.get("enrolled_year")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        # AUTO ROLL NO
        cur.execute("SELECT COUNT(*) FROM students")
        count = cur.fetchone()[0] + 1
        roll_no = f"2K23/MKCS/{count:02d}"

        cur.execute("""
            INSERT INTO students (
                name, email, password, cnic,
                department, semester, enrolled_year,
                profile_photo, roll_no
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, password, cnic,
            department, semester, enrolled_year,
            "", roll_no
        ))

        conn.commit()
        conn.close()

        return redirect("/student/login")

    return render_template("student_register.html")
import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.utils import secure_filename


# =========================
# DATABASE
# =========================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# STUDENT LOGIN
# =========================
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():

    if request.method == "POST":

        roll_no = request.form["roll_no"]
        password = request.form["password"]

        conn = get_db()

        student = conn.execute(
            """
            SELECT *
            FROM students
            WHERE roll_no=? AND password=?
            """,
            (roll_no, password)
        ).fetchone()

        conn.close()

        if student:

            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            session["roll_no"] = student["roll_no"]
            session["semester"] = student["semester"]

            return redirect("/student/dashboard")

        flash("Invalid Roll Number or Password")

    return render_template("student_login.html")


# =========================
# STUDENT DASHBOARD
# =========================
@app.route("/student/dashboard")
def student_dashboard():

    if "student_id" not in session:
        return redirect("/student/login")

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id=?",
        (session["student_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "student_dashboard.html",
        student=student
    )


# =========================
# STUDENT PROFILE
# =========================
@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():

    if "student_id" not in session:
        return redirect("/student/login")

    student_id = session["student_id"]

    conn = get_db()

    if request.method == "GET":

        student = conn.execute(
            "SELECT * FROM students WHERE id=?",
            (student_id,)
        ).fetchone()

        conn.close()

        return render_template(
            "student_profile.html",
            student=student
        )

    name = request.form["name"]
    email = request.form["email"]
    cnic = request.form["cnic"]
    department = request.form["department"]
    semester = request.form["semester"]
    enrolled_year = request.form["enrolled_year"]
    password = request.form["password"]

    photo = request.files.get("profile_photo")

    if photo and photo.filename:

        filename = secure_filename(photo.filename)

        upload_folder = os.path.join("static", "uploads")

        os.makedirs(upload_folder, exist_ok=True)

        photo.save(os.path.join(upload_folder, filename))

        image = "uploads/" + filename

        conn.execute("""
            UPDATE students
            SET
            name=?,
            email=?,
            cnic=?,
            department=?,
            semester=?,
            enrolled_year=?,
            password=?,
            profile_photo=?
            WHERE id=?
        """,
        (
            name,
            email,
            cnic,
            department,
            semester,
            enrolled_year,
            password,
            image,
            student_id
        ))

    else:

        conn.execute("""
            UPDATE students
            SET
            name=?,
            email=?,
            cnic=?,
            department=?,
            semester=?,
            enrolled_year=?,
            password=?
            WHERE id=?
        """,
        (
            name,
            email,
            cnic,
            department,
            semester,
            enrolled_year,
            password,
            student_id
        ))

    conn.commit()

    student = conn.execute(
        "SELECT * FROM students WHERE id=?",
        (student_id,)
    ).fetchone()

    conn.close()

    flash("Profile Updated Successfully")

    return render_template(
        "student_profile.html",
        student=student
    )


# =========================
# STUDENT ATTENDANCE
# =========================
@app.route("/student/attendance")
def student_attendance():

    if "student_id" not in session:
        return redirect("/student/login")


    conn = get_db()


    attendance = conn.execute("""
        SELECT

            c.course_title,


            COUNT(a.id) AS total_classes,


            SUM(
                CASE 
                    WHEN LOWER(a.status) = 'present'
                    THEN 1
                    ELSE 0
                END
            ) AS present,


            SUM(
                CASE 
                    WHEN LOWER(a.status) = 'absent'
                    THEN 1
                    ELSE 0
                END
            ) AS absent


        FROM student_courses sc


        JOIN courses c
        ON c.id = sc.course_id


        LEFT JOIN attendance a
        ON a.student_id = ?
        AND a.subject = c.course_title


        WHERE sc.student_id = ?


        GROUP BY c.id

    """,
    (
        session["student_id"],
        session["student_id"]
    )).fetchall()



    print("ATTENDANCE:", attendance)


    conn.close()


    return render_template(
        "student_attendance.html",
        attendance=attendance
    )
# =========================
# COURSE SELECTION
# =========================
@app.route("/student/course-selection", methods=["GET", "POST"])
def student_course_selection():

    if "student_id" not in session:
        return redirect("/student/login")

    conn = get_db()

    if request.method == "POST":

        conn.execute(
            "DELETE FROM student_courses WHERE student_id=?",
            (session["student_id"],)
        )

        course_ids = request.form.getlist("courses")

        for cid in course_ids:

            conn.execute("""
                INSERT INTO student_courses
                (student_id, course_id)
                VALUES (?,?)
            """,
            (
                session["student_id"],
                cid
            ))

        conn.commit()

        flash("Courses Selected Successfully")


    courses = conn.execute("""
        SELECT *
        FROM courses
        WHERE semester=?
        ORDER BY course_title
    """,
    (session["semester"],)
    ).fetchall()


    selected = conn.execute("""
        SELECT course_id
        FROM student_courses
        WHERE student_id=?
    """,
    (session["student_id"],)
    ).fetchall()


    selected = [
        x["course_id"] 
        for x in selected
    ]


    conn.close()


    return render_template(
        "student_course_selection.html",
        courses=courses,
        selected=selected
    )
# =========================
# VIEW SELECTED COURSES
# =========================

# =========================
# VIEW SELECTED COURSES
# =========================

@app.route("/student/selected-courses")
def student_selected_courses():

    if "student_id" not in session:
        return redirect("/student/login")


    conn = get_db()


    courses = conn.execute("""
        SELECT 
            courses.course_title,
            courses.course_code,
            courses.credit_hours,
            courses.semester

        FROM courses

        JOIN student_courses

        ON courses.id = student_courses.course_id

        WHERE student_courses.student_id=?
        AND courses.semester=?

    """,
    (
        session["student_id"],
        session["semester"]
    )
    ).fetchall()


    conn.close()


    return render_template(
        "selected_courses.html",
        courses=courses
    )
# =========================
# STUDENT ASSIGNMENTS
# =========================

@app.route("/student/assignments")
def student_assignments():

    if "student_id" not in session:
        return redirect("/student/login")

    conn = get_db()

    assignments = conn.execute("""
        SELECT 
            id,
            title,
            description,
            due_date,
            created_at
        FROM assignments
        ORDER BY id DESC
    """).fetchall()


    submissions = conn.execute("""
        SELECT assignment_id
        FROM submissions
        WHERE student_id=?
    """,
    (session["student_id"],)
    ).fetchall()


    submitted_ids = [
        row["assignment_id"]
        for row in submissions
    ]


    conn.close()


    return render_template(
        "assignments.html",
        assignments=assignments,
        submitted_ids=submitted_ids
    )



# =========================
# SUBMIT ASSIGNMENT
# =========================

@app.route(
    "/student/submit-assignment/<int:assignment_id>",
    methods=["POST"]
)
def submit_assignment(assignment_id):


    if "student_id" not in session:
        return redirect("/student/login")


    file = request.files.get("file")


    if not file or file.filename == "":
        flash("Please select a file")
        return redirect("/student/assignments")


    filename = secure_filename(
        file.filename
    )


    upload_folder = "uploads"

    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    filepath = os.path.join(
        upload_folder,
        filename
    )


    file.save(filepath)



    conn = get_db()


    # Check duplicate submission

    existing = conn.execute("""
        SELECT *
        FROM submissions
        WHERE assignment_id=?
        AND student_id=?
    """,
    (
        assignment_id,
        session["student_id"]
    )
    ).fetchone()



    if existing:

        conn.execute("""
            UPDATE submissions
            SET file_path=?,
                submitted_at=datetime('now')
            WHERE assignment_id=?
            AND student_id=?
        """,
        (
            filepath,
            assignment_id,
            session["student_id"]
        ))


    else:

        conn.execute("""
            INSERT INTO submissions
            (
                assignment_id,
                student_id,
                file_path,
                submitted_at
            )
            VALUES
            (?,?,?,datetime('now'))
        """,
        (
            assignment_id,
            session["student_id"],
            filepath
        ))


    conn.commit()
    conn.close()


    flash(
        "Assignment submitted successfully!"
    )


    return redirect(
        "/student/assignments"
    )
# =========================
# STUDENT AI CHAT
# =========================

@app.route("/student/chat")
def student_chat():

    if "student_id" not in session:
        return redirect("/student/login")

    return render_template(
        "chat.html"
    )
# =========================
# ASK TEACHER
# =========================

@app.route("/student/ask-teacher")
def ask_teacher():

    if "student_id" not in session:
        return redirect("/student/login")


    conn = get_db()


    teachers = conn.execute("""
        SELECT
            id,
            name,
            email,
            department,
            course_title,
            course_code
        FROM teachers
       ORDER BY id ASC
    """).fetchall()


    conn.close()


    return render_template(
        "ask_teacher.html",
        teachers=teachers
    )
# =========================
# ASK DOUBT
# =========================

@app.route(
    "/student/ask-teacher/<int:teacher_id>",
    methods=["GET","POST"]
)
def ask_teacher_question_route(teacher_id):


    if "student_id" not in session:
        return redirect("/student/login")



    if request.method == "POST":


        question = request.form["question"]


        conn = get_db()


        conn.execute("""
            INSERT INTO doubts
            (
                student_id,
                student_name,
                teacher_id,
                question,
                status
            )
            VALUES
            (?,?,?,?,?)
        """,
        (
            session["student_id"],
            session["student_name"],
            teacher_id,
            question,
            "pending"
        ))


        conn.commit()
        conn.close()


        flash(
            "Question sent successfully!"
        )


        return redirect(
            "/student/my-doubts"
        )



    return render_template(
        "ask_doubt.html"
    )
# =========================
# MY DOUBTS
# =========================

@app.route("/student/my-doubts")
def my_doubts():


    if "student_id" not in session:
        return redirect("/student/login")


    conn = get_db()


    doubts = conn.execute("""
        SELECT *
        FROM doubts
        WHERE student_id=?
        ORDER BY id DESC
    """,
    (
        session["student_id"],
    )
    ).fetchall()


    conn.close()


    return render_template(
        "my_doubts.html",
        doubts=doubts
    )
# =========================
# STUDENT NOTES
# =========================

@app.route("/student/notes")
def student_notes():

    if "student_id" not in session:
        return redirect("/student/login")


    conn = get_db()


    notes = conn.execute("""
        SELECT *
        FROM notes
        ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "notes.html",
        notes=notes
    )
# =========================
# SUBMIT COMPLAINT
# =========================

@app.route("/student/complaint", methods=["POST"])
def submit_complaint():


    if "student_id" not in session:
        return redirect("/student/login")


    message = request.form.get("message")


    conn = get_db()


    conn.execute("""
        INSERT INTO complaints
        (
            student_id,
            message,
            status
        )
        VALUES
        (?,?,?)
    """,
    (
        session["student_id"],
        message,
        "Pending"
    ))


    conn.commit()
    conn.close()


    flash(
        "Complaint submitted successfully!"
    )


    return redirect(
        "/student/my-complaints"
    )
# =========================
# MY COMPLAINTS
# =========================

@app.route("/student/my-complaints")
def my_complaints():


    if "student_id" not in session:
        return redirect("/student/login")


    conn = get_db()


    complaints = conn.execute("""
        SELECT *
        FROM complaints
        WHERE student_id=?
        ORDER BY id DESC
    """,
    (
        session["student_id"],
    )
    ).fetchall()


    conn.close()


    return render_template(
        "student_complaints.html",
        complaints=complaints
    )
@app.route("/student/complaints")
def complaints_redirect():

    if "student_id" not in session:
        return redirect("/student/login")


    return redirect(
        "/student/my-complaints"
    )
# =========================
# ANNOUNCEMENTS
# =========================

@app.route("/student/announcements")
def student_announcements():


    if "student_id" not in session:
        return redirect("/student/login")


    conn = get_db()


    announcements = conn.execute("""
        SELECT
            title,
            message
        FROM university_info
        WHERE category='announcement'
        ORDER BY id DESC
    """).fetchall()


    conn.close()


    return render_template(
        "announcements.html",
        announcements=announcements
    )
# =========================
# LOGOUT
# =========================
# =========================
# LOGOUT
# =========================

@app.route("/student/logout")
def student_logout():

    session.clear()

    flash(
        "Logged out successfully!"
    )

    return redirect(
        "/student/login"
    )
# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)