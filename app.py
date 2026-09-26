import os
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from db import query


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or os.urandom(32)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
UPLOADS = Path(__file__).parent / "uploads"
UPLOADS.mkdir(exist_ok=True)


def home():
    photos = query("SELECT photos.*, users.first_name FROM photos JOIN users ON users.id = photos.user_id ORDER BY photos.id DESC")
    count = query("SELECT COUNT(*) AS total FROM photos", one=True)["total"]
    return render_template("home.html", photos=photos, count=count)


def register():
    if request.method == "GET":
        return render_template("register.html")
    first = request.form.get("first_name", "").strip()
    last = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    if not first.isalpha() or not last.isalpha() or len(first) > 50 or len(last) > 50 or len(email) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(password) < 8:
        flash("Enter valid names, email, and a password of at least 8 characters.")
        return render_template("register.html"), 400
    if query("SELECT id FROM users WHERE email = %s", (email,), one=True):
        flash("That email is already registered.")
        return render_template("register.html"), 400
    user_id = query("INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)", (first, last, email, generate_password_hash(password, method="pbkdf2:sha256")))
    session["user_id"] = user_id
    session["first_name"] = first
    return redirect("/")


def login():
    if request.method == "GET":
        return render_template("login.html")
    email = request.form.get("email", "").strip().lower()
    user = query("SELECT * FROM users WHERE email = %s", (email,), one=True)
    if not user or not check_password_hash(user["password"], request.form.get("password", "")):
        flash("Incorrect email or password.")
        return render_template("login.html"), 401
    session.clear()
    session["user_id"] = user["id"]
    session["first_name"] = user["first_name"]
    response = redirect("/")
    response.set_cookie("last_login", datetime.now().strftime("%Y-%m-%d %H:%M"), max_age=7 * 24 * 60 * 60, httponly=True, samesite="Lax")
    return response


def logout():
    session.clear()
    return redirect("/login")


def upload():
    if not session.get("user_id"):
        return redirect("/login")
    if request.method == "GET":
        return render_template("upload.html")
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    image = request.files.get("image")
    extension = Path(secure_filename(image.filename or "")).suffix.lower() if image else ""
    if not title or len(title) > 200 or not image or extension not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        flash("Enter a title and choose a JPG, PNG, GIF, or WebP image.")
        return render_template("upload.html"), 400
    if image.mimetype not in {"image/jpeg", "image/png", "image/gif", "image/webp"}:
        flash("The selected file must be an image.")
        return render_template("upload.html"), 400
    filename = uuid4().hex + extension
    image.save(UPLOADS / filename)
    photo_id = query("INSERT INTO photos (user_id, file_name, title, description) VALUES (%s, %s, %s, %s)", (session["user_id"], filename, title, description))
    return redirect(f"/photo/{photo_id}")


def show(photo_id):
    photo = query("SELECT photos.*, users.first_name, users.last_name FROM photos JOIN users ON users.id = photos.user_id WHERE photos.id = %s", (photo_id,), one=True)
    if not photo:
        abort(404)
    comments = query("SELECT comments.*, users.first_name FROM comments JOIN users ON users.id = comments.user_id WHERE photo_id = %s ORDER BY comments.id", (photo_id,))
    return render_template("photo.html", photo=photo, comments=comments)


def comment(photo_id):
    if not session.get("user_id"):
        return redirect("/login")
    if not query("SELECT id FROM photos WHERE id = %s", (photo_id,), one=True):
        abort(404)
    body = request.form.get("comment", "").strip()
    if not body or len(body) > 1000:
        flash("Comment must be between 1 and 1000 characters.")
    else:
        query("INSERT INTO comments (photo_id, user_id, comment) VALUES (%s, %s, %s)", (photo_id, session["user_id"], body))
    return redirect(f"/photo/{photo_id}#comments")


def delete(photo_id):
    if not session.get("user_id"):
        return redirect("/login")
    photo = query("SELECT file_name FROM photos WHERE id = %s AND user_id = %s", (photo_id, session["user_id"]), one=True)
    if not photo:
        abort(403)
    query("DELETE FROM photos WHERE id = %s AND user_id = %s", (photo_id, session["user_id"]))
    (UPLOADS / photo["file_name"]).unlink(missing_ok=True)
    return redirect("/")


def about():
    return render_template("about.html")


# Match paths to actions
routes = [
    ("GET", r"/", home),
    ("GET", r"/about", about),
    ("GET", r"/login", login),
    ("POST", r"/login", login),
    ("GET", r"/register", register),
    ("POST", r"/register", register),
    ("POST", r"/logout", logout),
    ("GET", r"/upload", upload),
    ("POST", r"/upload", upload),
    ("GET", r"/photo/(\d+)", show),
    ("POST", r"/photo/(\d+)/comment", comment),
    ("POST", r"/photo/(\d+)/delete", delete),
]


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOADS, filename)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def dispatch(path):
    path = "/" + path
    for method, pattern, handler in routes:
        match = re.fullmatch(pattern, path)
        if method == request.method and match:
            return handler(*[int(value) for value in match.groups()])
    abort(404)


if __name__ == "__main__":
    app.run(debug=True)
