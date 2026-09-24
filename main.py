from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, RadioField, SubmitField
from wtforms.validators import DataRequired, EqualTo
import sqlite3
import os
import fitz
from docx import Document
from sentence_transformers import SentenceTransformer, util
import spacy
import re
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = "_privatekey_"

app.config["UPLOAD_FOLDER"] = "uploads"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# --------------------------------------------------
# NLP MODELS
# --------------------------------------------------

nlp = spacy.load("en_core_web_sm")

bert_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

regex_remove_punct = re.compile(r"[^\w\s]")


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

def init_db():

    con = sqlite3.connect("users_db.db")

    c = con.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            gender TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            resume_name TEXT NOT NULL,
            match_score REAL NOT NULL,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    con.commit()

    con.close()


# --------------------------------------------------
# SIGNUP FORM
# --------------------------------------------------

class SignUpForm(FlaskForm):

    name = StringField(
        "Username",
        validators=[DataRequired()]
    )

    email = EmailField(
        "Email",
        validators=[DataRequired()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Passwords must match"
            )
        ]
    )

    gender = RadioField(
        "Gender",
        choices=[
            ("male", "Male"),
            ("female", "Female")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Register")


# --------------------------------------------------
# LOGIN FORM
# --------------------------------------------------

class LoginForm(FlaskForm):

    email = EmailField(
        "Email",
        validators=[DataRequired()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Login")


# --------------------------------------------------
# FILE TEXT EXTRACTION
# --------------------------------------------------

def extract_text_from_pdf(file_path):

    text = ""

    with fitz.open(file_path) as doc:

        for page in doc:

            text += page.get_text()

    return text


def extract_text_from_docx(file_path):

    doc = Document(file_path)

    return "\n".join(
        paragraph.text
        for paragraph in doc.paragraphs
    )


# --------------------------------------------------
# KEYWORD EXTRACTION
# --------------------------------------------------

def extract_keywords(text):

    doc = nlp(text.lower())

    keywords = set()

    for token in doc:

        if (
            not token.is_stop
            and not token.is_punct
            and token.is_alpha
            and len(token.text) > 2
        ):

            keywords.add(token.lemma_)

    return keywords


# --------------------------------------------------
# MATCH SCORE + CATEGORY ANALYSIS
# --------------------------------------------------

def compute_match_score(job_description, resume_text):

    # ----------------------------------------------
    # Overall semantic matching
    # ----------------------------------------------

    job_keywords = extract_keywords(job_description)

    resume_keywords = extract_keywords(resume_text)

    job_embedding = bert_model.encode(
        job_description,
        convert_to_tensor=True
    )

    resume_embedding = bert_model.encode(
        resume_text,
        convert_to_tensor=True
    )

    semantic_score = util.cos_sim(
        job_embedding,
        resume_embedding
    ).item()


    # ----------------------------------------------
    # Keyword overlap
    # ----------------------------------------------

    if job_keywords:

        keyword_overlap = (
            len(job_keywords & resume_keywords)
            / len(job_keywords)
        )

    else:

        keyword_overlap = 0


    # ----------------------------------------------
    # Overall score
    # ----------------------------------------------

    final_score = (
        (0.9 * semantic_score)
        +
        (0.2 * keyword_overlap)
    ) * 100

    final_score = min(
        max(final_score, 0),
        100
    )


    # ----------------------------------------------
    # Skill categories
    # ----------------------------------------------

    technical_skills = {

        "python",
        "java",
        "javascript",
        "typescript",

        "c",
        "c++",

        "sql",

        "html",
        "css",

        "react",
        "angular",

        "node",
        "nodejs",

        "express",
        "flask",
        "django",

        "machine learning",
        "deep learning",

        "artificial intelligence",

        "data science",
        "data analysis",

        "nlp",

        "tensorflow",
        "pytorch",

        "scikit-learn",

        "mongodb",
        "mysql",
        "postgresql",

        "api",
        "rest"
    }


    soft_skills = {

        "communication",
        "leadership",

        "teamwork",
        "team",

        "problem solving",
        "problem-solving",

        "adaptability",
        "creativity",

        "collaboration",
        "management",

        "organization",

        "time management",

        "critical thinking",

        "analytical",
        "interpersonal"
    }


    tools = {

        "git",
        "github",

        "docker",

        "aws",
        "azure",
        "gcp",

        "power bi",
        "tableau",

        "jupyter",

        "vscode",
        "visual studio code",

        "postman",

        "figma",

        "jira",

        "linux",

        "excel",

        "hadoop",
        "spark"
    }


    # ----------------------------------------------
    # Category score function
    # ----------------------------------------------

    def category_score(category_words):

        job_text = job_description.lower()

        resume_text_lower = resume_text.lower()


        relevant_words = [

            word

            for word in category_words

            if word in job_text
        ]


        if not relevant_words:

            return 0


        matched_words = [

            word

            for word in relevant_words

            if word in resume_text_lower
        ]


        score = (
            len(matched_words)
            /
            len(relevant_words)
        ) * 100


        return round(score, 1)


    # ----------------------------------------------
    # Calculate category scores
    # ----------------------------------------------

    technical_score = category_score(
        technical_skills
    )

    soft_score = category_score(
        soft_skills
    )

    tools_score = category_score(
        tools
    )


    # ----------------------------------------------
    # Return all results
    # ----------------------------------------------

    return {

        "overall": round(
            final_score,
            1
        ),

        "technical": technical_score,

        "soft": soft_score,

        "tools": tools_score
    }


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    return redirect(
        url_for("login")
    )


# --------------------------------------------------
# SIGNUP
# --------------------------------------------------

@app.route(
    "/signup",
    methods=["GET", "POST"]
)
def signup():

    form = SignUpForm()


    if form.validate_on_submit():

        username = form.name.data

        email = form.email.data

        password = form.password.data

        confirm_password = (
            form.confirm_password.data
        )

        gender = form.gender.data


        if password != confirm_password:

            flash(
                "Passwords do not match. Please try again.",
                "error"
            )

            return render_template(
                "SignUp_Page.html",
                form=form
            )


        con = None


        try:

            con = sqlite3.connect(
                "users_db.db"
            )

            c = con.cursor()


            c.execute(
                """
                INSERT INTO users
                (username, email, password, gender)
                VALUES (?, ?, ?, ?)
                """,
                (
                    username,
                    email,
                    password,
                    gender
                )
            )


            con.commit()


            flash(
                "Signup successful! Please log in.",
                "success"
            )


            return redirect(
                url_for("login")
            )


        except sqlite3.IntegrityError:

            flash(
                "Email already exists. Please use a different email.",
                "error"
            )


        finally:

            if con:

                con.close()


    return render_template(
        "SignUp_Page.html",
        form=form
    )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    form = LoginForm()


    if form.validate_on_submit():

        email = form.email.data

        password = form.password.data


        con = sqlite3.connect(
            "users_db.db"
        )

        c = con.cursor()


        c.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )


        user = c.fetchone()


        con.close()


        if user and user[3] == password:

            session["user_id"] = user[0]

            return redirect(
                url_for("upload_resume")
            )


        flash(
            "Invalid email or password. Please try again.",
            "error"
        )


    return render_template(
        "Login_Page.html",
        form=form
    )


# --------------------------------------------------
# RESUME UPLOAD + ANALYSIS
# --------------------------------------------------

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload_resume():

    if request.method == "POST":

        if (
            "job_description" in request.form
            and
            "resume" in request.files
        ):

            job_description = request.form[
                "job_description"
            ]

            resume = request.files[
                "resume"
            ]


            # --------------------------------------
            # Check uploaded file
            # --------------------------------------

            if resume.filename == "":

                flash(
                    "No file uploaded. Please select a file.",
                    "error"
                )

                return redirect(
                    url_for("upload_resume")
                )


            filename = secure_filename(
                resume.filename
            )


            file_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )


            resume.save(file_path)


            # --------------------------------------
            # Extract resume text
            # --------------------------------------

            filename_lower = filename.lower()


            if filename_lower.endswith(".pdf"):

                resume_text = extract_text_from_pdf(
                    file_path
                )


            elif filename_lower.endswith(".docx"):

                resume_text = extract_text_from_docx(
                    file_path
                )


            else:

                flash(
                    "Unsupported file format. Please upload a .pdf or .docx file.",
                    "error"
                )

                os.remove(file_path)

                return redirect(
                    url_for("upload_resume")
                )


            # --------------------------------------
            # Calculate analysis
            # --------------------------------------

            analysis_result = compute_match_score(

                job_description,

                resume_text
            )


            similarity_score = (
                analysis_result["overall"]
            )


            # --------------------------------------
            # Save analysis history
            # --------------------------------------

            if "user_id" in session:

                conn = sqlite3.connect(
                    "users_db.db"
                )

                cursor = conn.cursor()


                cursor.execute(
                    """
                    INSERT INTO analysis_history
                    (user_id, resume_name, match_score)
                    VALUES (?, ?, ?)
                    """,

                    (
                        session["user_id"],
                        filename,
                        float(similarity_score)
                    )
                )


                conn.commit()

                conn.close()


            # --------------------------------------
            # Delete uploaded file after processing
            # --------------------------------------

            os.remove(file_path)


            # --------------------------------------
            # Show result page
            # --------------------------------------

            return render_template(

                "result.html",

                similarity_score=similarity_score,

                technical_score=(
                    analysis_result["technical"]
                ),

                soft_score=(
                    analysis_result["soft"]
                ),

                tools_score=(
                    analysis_result["tools"]
                )
            )


        flash(
            "Missing job description or resume file.",
            "error"
        )


    return render_template(
        "index.html"
    )


# --------------------------------------------------
# HISTORY
# --------------------------------------------------

@app.route("/history")
def history():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    conn = sqlite3.connect(
        "users_db.db"
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT resume_name, match_score, analyzed_at
        FROM analysis_history
        WHERE user_id = ?
        ORDER BY analyzed_at DESC
        """,
        (session["user_id"],)
    )


    history_records = cursor.fetchall()


    conn.close()


    return render_template(
        "history.html",
        history_records=history_records
    )


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )