from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO
import sqlite3
import os

port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=port)

app = Flask(__name__)
app.secret_key = "secret"

socketio = SocketIO(app)

def get_db():
    return sqlite3.connect("database.db")

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()

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

    return render_template("dashboard.html",
                           incidents=incidents,
                           role=session["role"],
                           total=total,
                           resolved=resolved,
                           pending=pending)


# REPORT (ADMIN ONLY)
@app.route("/report", methods=["GET","POST"])
def report():
    if "user" not in session or session["role"] != "admin":
        return redirect("/")

    if request.method == "POST":
        t = request.form["type"]
        l = request.form["location"]

        db = get_db()
        db.execute("INSERT INTO incidents (type,location,status) VALUES (?,?,?)",(t,l,"Pending"))
        db.commit()

        socketio.emit("new_incident", {"type":t,"location":l})

        return redirect("/dashboard")

    return render_template("index.html")


# UPDATE
@app.route("/update/<int:id>")
def update(id):
    if "user" not in session:
        return redirect("/")

    db = get_db()
    db.execute("UPDATE incidents SET status='Resolved' WHERE id=?",(id,))
    db.commit()

    socketio.emit("update_incident", {"id":id})

    return redirect("/dashboard")


# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    socketio.run(app, debug=True)