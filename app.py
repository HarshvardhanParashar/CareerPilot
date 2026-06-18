from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import create_database, get_connection
import pandas as pd
import matplotlib.pyplot as plt
import os
import seaborn as sns

app = Flask(__name__)
app.secret_key = "careerpilot_secret_key"
create_database()

@app.route("/")
def home():
    return render_template("home.html")


# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()

        cursor = conn.cursor()
        

        try:
            cursor.execute(
            """
            INSERT INTO users(name,email,password,role)
            VALUES(?,?,?,?)
            """,
            (name, email, password,'student')
            )

            conn.commit()

        except:
            return "Email already exists"

        finally:
            conn.close()
            
        flash("Registration successful! Please login.","success")
        return redirect(url_for("login"))

        return redirect(url_for("login"))

    return render_template("register.html")


#Routes for user login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
            """,
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_role"] = user[5]
            flash(f"Welcome {user[1]}!", "success")
           
            if user[5] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


#Dashboard route
@app.route("/dashboard")

def dashboard():
    chart_path = f"static/charts/{session['user_id']}_performance.png"

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT test_date, score, percentage
        FROM results
        WHERE user_id = ?
        ORDER BY test_date DESC
    """, conn, params=(session["user_id"],))

    conn.close()

    total_tests = len(df)

    if total_tests > 0:
        avg_score = round(df["percentage"].mean(), 2)
        highest_score = df["percentage"].max()
        latest_score = df.iloc[0]["percentage"]
    else:
        avg_score = 0
        highest_score = 0
        latest_score = 0


    plt.figure(figsize=(8, 4))

    sns.lineplot(
    data=df,
    x="test_date",
    y="percentage",
    marker="o"
)

    plt.title("Performance Trend")
    plt.xlabel("Test Date")
    plt.ylabel("Score (%)")
    plt.xticks(rotation=45)
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    if avg_score >= 75:
        insight = "🔥 Excellent performance"
    elif avg_score >= 50:
        insight = "📈 Good, but needs improvement"
    else:
        insight = "⚠ Weak performance"

    return render_template(
    "dashboard.html",
        name=session.get("name", "Student"),
        total_tests=total_tests,
        avg_score=avg_score,
        highest_score=highest_score,
        latest_score=latest_score,
        chart_url=chart_path,
        insight=insight
    )
#Logout route

@app.route("/logout")
def logout():

    session.clear()
    flash("You have been logged out successfully.","info")
    return redirect(url_for("login"))



#Admin dashboard route
@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["user_role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM results")
    total_tests = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_questions=total_questions,
        total_tests=total_tests
    )


#user route
@app.route("/users")
def users():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["user_role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,name,email,role,created_at
        FROM users
        ORDER BY id DESC
    """)

    users = cursor.fetchall()

    conn.close()

    return render_template(
        "users.html",
        users=users
    )


#Add quuestions route
@app.route("/add-question", methods=["GET", "POST"])
def add_question():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only admin can access
    if session["user_role"] != "admin":
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        main_category = request.form["main_category"]
        sub_category = request.form["sub_category"]

        question = request.form["question"]

        option_a = request.form["option_a"]
        option_b = request.form["option_b"]
        option_c = request.form["option_c"]
        option_d = request.form["option_d"]

        correct_answer = request.form["correct_answer"]

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO questions
            (
                main_category,
                sub_category,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_answer
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                main_category,
                sub_category,
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                correct_answer
            )
        )

        conn.commit()
        conn.close()

        flash("Question added successfully!", "success")

        return redirect(url_for("add_question"))

    return render_template("add_question.html")


@app.route("/questions")
def questions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["user_role"] != "admin":
        return redirect(url_for("dashboard"))

    category = request.args.get("category")

    conn = get_connection()
    cursor = conn.cursor()

    if category:

        cursor.execute("""
        SELECT
            id,
            main_category,
            sub_category,
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer
        FROM questions
        WHERE main_category = ?
        ORDER BY id DESC
        """, (category,))

    else:

        cursor.execute("""
        SELECT
            id,
            main_category,
            sub_category,
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer
        FROM questions
        ORDER BY id DESC
        """)

    questions = cursor.fetchall()

    conn.close()

    return render_template(
        "questions.html",
        questions=questions,
        selected_category=category
    )
#Delete questions route
@app.route("/delete-question/<int:id>")
def delete_question(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["user_role"] != "admin":
        return redirect(url_for("dashboard"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM questions WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    flash("Question deleted successfully!", "success")

    return redirect(url_for("questions"))


#import questions route
@app.route("/import-questions", methods=["GET", "POST"])
def import_questions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["user_role"] != "admin":
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        file = request.files["csv_file"]

        filepath = os.path.join(
            "uploads",
            file.filename
        )

        file.save(filepath)

        df = pd.read_csv(filepath)

        conn = get_connection()
        cursor = conn.cursor()

        for _, row in df.iterrows():

            cursor.execute(
                """
                INSERT INTO questions
                (
                    main_category,
                    sub_category,
                    question,
                    option_a,
                    option_b,
                    option_c,
                    option_d,
                    correct_answer
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    row["main_category"],
                    row["sub_category"],
                    row["question"],
                    row["option_a"],
                    row["option_b"],
                    row["option_c"],
                    row["option_d"],
                    row["correct_answer"]
                )
            )

        conn.commit()
        conn.close()

        flash(
            f"{len(df)} questions imported successfully!",
            "success"
        )

        return redirect(url_for("questions"))

    return render_template(
        "import_questions.html"
    )

#Start test route
@app.route("/start-test")
def start_test():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("start_test.html")

#generate test route
@app.route("/generate-test", methods=["POST"])
def generate_test():

    if "user_id" not in session:
        return redirect(url_for("login"))

    categories = request.form.getlist("categories")

    if not categories:
        flash("Please select at least one category.", "warning")
        return redirect(url_for("start_test"))

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["?"] * len(categories))

    cursor.execute(
        f"""
        SELECT
            id,
            question,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_answer,
            main_category,
            sub_category
        FROM questions
        WHERE sub_category IN ({placeholders})
        ORDER BY RANDOM()
        LIMIT 25
        """,
        categories
    )

    questions = cursor.fetchall()

    conn.close()

    return render_template(
        "test.html",
        questions=questions,
        categories=categories
    )

#Submit test route
@app.route("/submit-test", methods=["POST"])
def submit_test():

    if "user_id" not in session:
        return redirect(url_for("login"))

    question_ids = request.form.getlist("question_ids")

    score = 0
    total_questions = len(question_ids)

    conn = get_connection()
    cursor = conn.cursor()

    for question_id in question_ids:

        selected_answer = request.form.get(
            f"answer_{question_id}"
        )

        cursor.execute(
            """
            SELECT correct_answer
            FROM questions
            WHERE id = ?
            """,
            (question_id,)
        )

        correct_answer = cursor.fetchone()[0]

        if selected_answer == correct_answer:
            score += 1

    percentage = round(
        (score / total_questions) * 100,
        2
    )

    cursor.execute(
        """
        INSERT INTO results
        (
            user_id,
            score,
            total_questions,
            percentage
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            session["user_id"],
            score,
            total_questions,
            percentage
        )
    )

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        score=score,
        total_questions=total_questions,
        percentage=percentage
    )

#History route
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            score,
            total_questions,
            percentage,
            test_date
        FROM results
        WHERE user_id = ?
        ORDER BY test_date DESC
        """,
        (session["user_id"],)
    )

    results = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        results=results
    )


#Gnerate chart route

@app.route("/analysis")
def analysis():
    chart_path = f"static/charts/{session['user_id']}_performance.png"

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT test_date, score, percentage
        FROM results
        WHERE user_id = ?
        ORDER BY test_date
    """, conn, params=(session["user_id"],))

    
    conn.close()

    if df.empty:
        flash("No test data available yet.", "warning")
        return redirect(url_for("dashboard"))

    total_tests = len(df)
    avg_score = df["percentage"].mean()
    highest_score = df["percentage"].max()
    lowest_score = df["percentage"].min()

    # ---------------------------
    # 📊 CHART GENERATION
    # ---------------------------
    import os
    import matplotlib.pyplot as plt
    import seaborn as sns

    os.makedirs("static/charts", exist_ok=True)

    chart_path = f"static/charts/{session['user_id']}_analysis.png"

    plt.figure(figsize=(9, 4))
    sns.lineplot(data=df, x="test_date", y="percentage", marker="o")

    plt.title("Full Performance Analysis")
    plt.xlabel("Test Date")
    plt.ylabel("Score %")
    plt.xticks(rotation=45)
    plt.grid(True)

    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    # ---------------------------
    # 🧠 INSIGHT ENGINE
    # ---------------------------
    if avg_score >= 75:
        insight = "🔥 Excellent consistency"
    elif avg_score >= 50:
        insight = "📈 Moderate performance, improve weak areas"
    else:
        insight = "⚠ Needs strong revision"

    return render_template(
        "analysis.html",
        total_tests=total_tests,
        avg_score=round(avg_score, 2),
        highest_score=highest_score,
        lowest_score=lowest_score,
        chart_url=chart_path,
        insight=insight
    )

if __name__ == "__main__":
    app.run(debug=True)
