from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret"

# 🔥 IMPORTANT: eventlet mode for Railway
socketio = SocketIO(app, async_mode="eventlet")

# DB CONNECTION
def get_db():
    return sqlite3.connect("database.db")


# 🔥 AUTO CREATE DATABASE (IMPORTANT FOR DEPLOYMENT)
if not os.path.exists("database.db"):
    import database


# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        if user:
            session["user"] = user[1]
            session["role"] = user[3]
            return redirect("/dashboard")

    return render_template("login.html")


# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    db = get_db()
    incidents = db.execute("SELECT * FROM incidents").fetchall()

    total = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM incidents WHERE status='Resolved'").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM incidents WHERE status='Pending'").fetchone()[0]

    return render_template(
        "dashboard.html",
        incidents=incidents,
        role=session["role"],
        total=total,
        resolved=resolved,
        pending=pending
    )


# REPORT (ADMIN ONLY)
@app.route("/report", methods=["GET", "POST"])
def report():
    if "user" not in session or session["role"] != "admin":
        return redirect("/")

    if request.method == "POST":
        type = request.form["type"]
        location = request.form["location"]

        db = get_db()
        db.execute(
            "INSERT INTO incidents (type, location, status) VALUES (?, ?, ?)",
            (type, location, "Pending")
        )
        db.commit()

        # 🔥 REAL-TIME UPDATE
        socketio.emit("new_incident", {
            "type": type,
            "location": location,
            "status": "Pending"
        })

        return redirect("/dashboard")

    return render_template("index.html")


# UPDATE INCIDENT
@app.route("/update/<int:id>")
def update(id):
    if "user" not in session:
        return redirect("/")

    db = get_db()
    db.execute("UPDATE incidents SET status='Resolved' WHERE id=?", (id,))
    db.commit()

    # 🔥 REAL-TIME UPDATE
    socketio.emit("update_incident", {"id": id})

    return redirect("/dashboard")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# 🚀 MAIN (RAILWAY COMPATIBLE)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    socketio.run(app, host="0.0.0.0", port=port)