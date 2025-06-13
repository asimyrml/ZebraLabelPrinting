from flask import Flask, request, render_template, flash, redirect, session
from models import db, User
import socket

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db.init_app(app)

def generate_zpl(label_value):
    return f"""
^XA
^PON
^PW432
^LL200
^BY2,3,100
^FO8,50^BCN,100,Y,N,N^FD{label_value}^FS
^XZ
"""

def send_to_printer(ip, port, zpl_code):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect((ip, port))
            sock.sendall(zpl_code.encode('utf-8'))
        return True, "Label successfully printed."
    except Exception as e:
        return False, f"Printer error: {e}"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(full_name=full_name, email=email)
            if email == "asim@admin.com":  # auto-assign admin
                user.is_admin = True
            db.session.add(user)
            db.session.commit()


        session["user_id"] = user.id
        flash("Logged in successfully.", "success")
        return redirect("/")

    return render_template("login.html")

@app.route("/", methods=["GET", "POST"])
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    user = User.query.get(user_id)

    if request.method == "POST":
        label = request.form.get("label_value", "").strip()
        ip = request.form.get("printer_ip", "").strip()
        port = request.form.get("printer_port", "").strip()

        ip_changed = ip and ip != user.printer_ip
        port_changed = port and str(user.printer_port) != port

        if port and not port.isdigit():
            flash("Port must be a number.", "error")
            return redirect("/")

        updated = False

        # IP or Port changed
        if ip_changed or port_changed:
            user.printer_ip = ip or user.printer_ip
            user.printer_port = int(port) if port else user.printer_port
            db.session.commit()
            flash("Printer settings updated.", "info")
            updated = True

        # Label submitted
        if label:
            zpl = generate_zpl(label)
            success, message = send_to_printer(user.printer_ip, user.printer_port, zpl)
            flash(message, "success" if success else "error")
            updated = True

        if not updated:
            flash("No changes detected.", "info")

        return redirect("/")

    return render_template("index.html", user=user, default_ip=user.printer_ip, default_port=user.printer_port)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out.", "info")
    return redirect("/login")




@app.route("/admin")
def admin_panel():
    user_id = session.get("user_id")
    if not user_id:
        flash("Unauthorized", "error")
        return redirect("/login")

    current_user = User.query.get(user_id)
    if not current_user or not current_user.is_admin:
        flash("Access denied", "error")
        return redirect("/")

    users = User.query.all()
    return render_template("admin.html", users=users)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


