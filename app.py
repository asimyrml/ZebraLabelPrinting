from flask import Flask, request, render_template, flash, redirect, session
from models import db, User
from uuid import uuid4
from datetime import datetime
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

import os

def send_zpl_to_printer(ip, port, zpl):
    print("[🖨️] Etiket yazıcıya gönderiliyor...")
    print(f"IP: {ip}, Port: {port}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)

            # Docker içindeysen 'host.docker.internal', değilse IP'yi olduğu gibi kullan
            running_in_docker = os.path.exists("/.dockerenv")
            connect_ip = "host.docker.internal" if running_in_docker and ip == "0.0.0.0" else ip

            s.connect((connect_ip, int(port)))
            s.sendall(zpl.encode('utf-8'))

        print("[🖨️] Etiket yazıcıya gönderildi.")
        return True
    except Exception as e:
        print("[✖] Yazıcıya gönderim hatası:", e.__class__.__name__, str(e))
        return False



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(full_name=full_name, email=email, api_token=str(uuid4().hex))
            if email == "asim@admin.com":
                user.is_admin = True
            db.session.add(user)
            db.session.commit()
        session["user_id"] = user.id
        flash("Giriş başarılı.", "success")
        return redirect("/")
    return render_template("login.html")

@app.route("/", methods=["GET", "POST"])
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    user = User.query.get(user_id)
    if not user:
        flash("Lütfen tekrar giriş yapın.", "error")
        return redirect("/login")

    if request.method == "POST":
        label = request.form.get("label_value", "").strip()
        ip = request.form.get("printer_ip", "0.0.0.0").strip()
        port = request.form.get("printer_port", "9100").strip()
        print(label, ip, port)

        if port and not port.isdigit():
            flash("Port numarası geçersiz.", "error")
            return redirect("/")

        if ip:
            user.printer_ip = ip
        if port:
            user.printer_port = int(port)


        print(label, ip, port)

        if label:
            zpl = generate_zpl(label)
            user.zpl_code = zpl
            user.zpl_updated_at = datetime.utcnow()

            db.session.commit()

            if user.printer_ip and user.printer_port:
                print("user.printer_ip:", user.printer_ip)
                print("user.printer_port:", user.printer_port)
                print("ZPL:", zpl)
                if send_zpl_to_printer(user.printer_ip, user.printer_port, zpl):
                    flash("Etiket yazıcıya gönderildi.", "success")
                else:
                    flash("Yazdırma hatası oluştu.", "error")
            else:
                flash("Yazıcı IP/Port bilgisi eksik.", "error")
        else:
            db.session.commit()
            flash("Yazıcı ayarları güncellendi.", "info")

        return redirect("/")

    return render_template("index.html", user=user, default_ip=user.printer_ip, default_port=user.printer_port)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Çıkış yapıldı.", "info")
    return redirect("/login")

@app.route("/admin")
def admin_panel():
    user_id = session.get("user_id")
    current_user = User.query.get(user_id)
    if not current_user or not current_user.is_admin:
        flash("Yetkisiz erişim", "error")
        return redirect("/")
    users = User.query.all()
    return render_template("admin.html", users=users)

@app.route("/label/latest_zpl")
def latest_zpl():
    token = request.args.get("token")
    if not token:
        return "Unauthorized", 401
    user = User.query.filter_by(api_token=token).first()
    if not user or not user.zpl_code:
        return "No label available", 404
    return user.zpl_code, 200, {"Content-Type": "text/plain"}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
