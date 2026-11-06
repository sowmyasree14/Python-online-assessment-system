import csv
import io
import json
import os
import hmac
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask, abort, flash, make_response, redirect, render_template,
    request, session, url_for
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-local-secret")

database_url = os.environ.get("DATABASE_URL", "sqlite:///assessment.db")
# Render and some providers may supply the legacy postgres:// prefix.
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
db = SQLAlchemy(app)


# The code examples are rendered with Jinja's automatic HTML escaping.
# Each question has four options and one correct answer (0-based index).
QUESTIONS = [
    {
        "id": 1, "topic": "Variables", "question": "What is the output of this code?",
        "code": 'name = "Python"\nprint(name)',
        "options": ['name', 'Python', '"Python"', 'Error'],
        "answer": 1, "explanation": "The variable name stores the string Python, which print displays."
    },
    {
        "id": 2, "topic": "Data types", "question": "What is the data type of the value 3.14?",
        "code": "value = 3.14\nprint(type(value).__name__)",
        "options": ["int", "float", "str", "bool"],
        "answer": 1, "explanation": "A number with a decimal part is a float."
    },
    {
        "id": 3, "topic": "Operators", "question": "What does the // operator do in Python?",
        "code": "print(17 // 5)",
        "options": ["Normal division", "Exponentiation", "Floor division", "Remainder"],
        "answer": 2, "explanation": "Floor division returns the quotient rounded down; 17 // 5 is 3."
    },
    {
        "id": 4, "topic": "Strings", "question": "What is printed by the following code?",
        "code": 'word = "Python"\nprint(word[0])',
        "options": ["P", "y", "Python", "Error"],
        "answer": 0, "explanation": "String indexing starts at zero, so word[0] is P."
    },
    {
        "id": 5, "topic": "Lists", "question": "Which method adds an item to the end of a list?",
        "code": "numbers = [1, 2]\nnumbers._____ (3)",
        "options": ["add", "append", "insert_end", "extend_one"],
        "answer": 1, "explanation": "append() adds one item to the end of a list."
    },
    {
        "id": 6, "topic": "Tuples", "question": "Which statement about tuples is correct?",
        "code": "point = (4, 7)",
        "options": [
            "Tuples are mutable", "Tuples cannot contain numbers",
            "Tuples are immutable", "Tuples use curly braces"
        ],
        "answer": 2, "explanation": "A tuple is immutable: its elements cannot be reassigned after creation."
    },
    {
        "id": 7, "topic": "Dictionaries", "question": "How do you access the value associated with the key 'city'?",
        "code": 'person = {"name": "Asha", "city": "Hyderabad"}',
        "options": ["person.city", 'person["city"]', "person( city )", "person[1]"],
        "answer": 1, "explanation": "Dictionary values are accessed by their keys, commonly using square brackets."
    },
    {
        "id": 8, "topic": "Conditionals", "question": "What is the output?",
        "code": "age = 18\nif age >= 18:\n    print('Adult')\nelse:\n    print('Minor')",
        "options": ["Minor", "Adult", "18", "No output"],
        "answer": 1, "explanation": "18 >= 18 is true, so the if branch runs."
    },
    {
        "id": 9, "topic": "Loops", "question": "How many times does this loop print a number?",
        "code": "for i in range(2, 6):\n    print(i)",
        "options": ["3", "4", "5", "6"],
        "answer": 1, "explanation": "range(2, 6) generates 2, 3, 4, and 5: four values."
    },
    {
        "id": 10, "topic": "While loop", "question": "What is the final value of count?",
        "code": "count = 0\nwhile count < 3:\n    count += 1\nprint(count)",
        "options": ["2", "3", "4", "0"],
        "answer": 1, "explanation": "The loop increments count until it reaches 3."
    },
    {
        "id": 11, "topic": "Functions", "question": "Which keyword is used to define a function?",
        "code": "_____ greet():\n    print('Hello')",
        "options": ["func", "define", "def", "function"],
        "answer": 2, "explanation": "Python functions are defined using the def keyword."
    },
    {
        "id": 12, "topic": "Return values", "question": "What does this function return?",
        "code": "def add(a, b):\n    return a + b\n\nresult = add(2, 5)",
        "options": ["2", "5", "7", "None"],
        "answer": 2, "explanation": "The return statement sends a + b back to the caller, so the result is 7."
    },
    {
        "id": 13, "topic": "Built-in functions", "question": "What does len() return?",
        "code": 'items = ["pen", "book", "bag"]\nprint(len(items))',
        "options": ["The last item", "The number of items", "The index of an item", "The list's data type"],
        "answer": 1, "explanation": "len() returns the number of elements in a collection; here it is 3."
    },
    {
        "id": 14, "topic": "Type conversion", "question": "What is the result of int('25')?",
        "code": "number = int('25')\nprint(number + 5)",
        "options": ["255", "30", "25.5", "TypeError"],
        "answer": 1, "explanation": "int('25') converts the string to integer 25, then 5 is added."
    },
    {
        "id": 15, "topic": "Boolean values", "question": "Which value represents logical false in Python?",
        "code": "is_ready = _____",
        "options": ["false", "FALSE", "False", "0.0.0"],
        "answer": 2, "explanation": "Python's Boolean literals are capitalized: True and False."
    },
    {
        "id": 16, "topic": "Membership", "question": "What is the output?",
        "code": 'print("py" in "python")',
        "options": ["True", "False", "py", "Error"],
        "answer": 0, "explanation": "The substring py occurs at the beginning of python."
    },
    {
        "id": 17, "topic": "Exceptions", "question": "Which block handles an exception?",
        "code": "try:\n    result = 10 / 0\n_____ ZeroDivisionError:\n    print('Cannot divide by zero')",
        "options": ["catch", "except", "error", "finally"],
        "answer": 1, "explanation": "An except block catches and handles a matching exception."
    },
    {
        "id": 18, "topic": "Modules", "question": "Which statement imports Python's math module?",
        "code": "_____ math\nprint(math.sqrt(16))",
        "options": ["include math", "using math", "import math", "module math"],
        "answer": 2, "explanation": "The import statement makes a module available in your program."
    },
    {
        "id": 19, "topic": "Sets", "question": "What does this code print?",
        "code": "values = {1, 2, 2, 3}\nprint(len(values))",
        "options": ["4", "3", "2", "Error"],
        "answer": 1, "explanation": "A set stores unique values, so the duplicate 2 is kept only once."
    },
    {
        "id": 20, "topic": "List comprehension", "question": "What is the value of squares?",
        "code": "squares = [n * n for n in range(1, 4)]",
        "options": ["[1, 2, 3]", "[1, 4, 9]", "[1, 4, 9, 16]", "[2, 4, 6]"],
        "answer": 1, "explanation": "The comprehension squares 1, 2, and 3, producing [1, 4, 9]."
    },
]


class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(120), nullable=False)
    student_email = db.Column(db.String(254), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    answers_json = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False,
                             default=lambda: datetime.now(timezone.utc))


def public_questions():
    return [
        {key: value for key, value in question.items() if key not in ("answer", "explanation")}
        for question in QUESTIONS
    ]


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    return render_template("index.html", question_count=len(QUESTIONS))


@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    if request.method == "GET":
        return render_template("assessment.html", questions=public_questions())

    name = request.form.get("student_name", "").strip()
    email = request.form.get("student_email", "").strip().lower()

    if not name or len(name) > 120:
        flash("Please enter a valid name (up to 120 characters).", "error")
        return redirect(url_for("assessment"))
    if not email or len(email) > 254 or "@" not in email:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("assessment"))

    # One attempt per email address. This is a basic identity check, not proctoring.
    existing = Attempt.query.filter(func.lower(Attempt.student_email) == email).first()
    if existing:
        return render_template("already_submitted.html", attempt=existing)

    submitted_answers = {}
    score = 0
    for question in QUESTIONS:
        selected = request.form.get(f"q{question['id']}", "")
        try:
            selected_index = int(selected)
        except (TypeError, ValueError):
            selected_index = -1

        if selected_index not in range(len(question["options"])):
            selected_index = -1

        submitted_answers[str(question["id"])] = selected_index
        if selected_index == question["answer"]:
            score += 1

    attempt = Attempt(
        student_name=name,
        student_email=email,
        score=score,
        total=len(QUESTIONS),
        answers_json=json.dumps(submitted_answers),
    )
    db.session.add(attempt)
    db.session.commit()

    review = []
    for question in QUESTIONS:
        selected = submitted_answers[str(question["id"])]
        review.append({
            **question,
            "selected_text": question["options"][selected] if selected >= 0 else "Not answered",
            "is_correct": selected == question["answer"],
        })

    return render_template("result.html", attempt=attempt, review=review)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        configured_password = os.environ.get("ADMIN_PASSWORD", "")
        password = request.form.get("password", "")
        if not configured_password:
            flash("ADMIN_PASSWORD is not configured on the server.", "error")
        elif hmac.compare_digest(password, configured_password):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Incorrect password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    attempts = Attempt.query.order_by(Attempt.submitted_at.desc()).all()
    average = round(sum(a.score for a in attempts) / len(attempts), 2) if attempts else 0
    return render_template("admin.html", attempts=attempts, average=average)


@app.route("/admin/export.csv")
@admin_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student name", "Email", "Score", "Total", "Percentage", "Submitted at"])
    for attempt in Attempt.query.order_by(Attempt.submitted_at.desc()).all():
        writer.writerow([
            attempt.student_name, attempt.student_email, attempt.score,
            attempt.total, round(attempt.score / attempt.total * 100, 2),
            attempt.submitted_at.isoformat() if attempt.submitted_at else ""
        ])
    response = make_response("\\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=assessment-results.csv"
    return response


@app.route("/health")
def health():
    return {"status": "ok"}


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
