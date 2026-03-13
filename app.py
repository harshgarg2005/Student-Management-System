import os
import shutil
import sys
import secrets
import smtplib
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime, timedelta

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

import csv
import io
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy.sql import func
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

# Load .env from the same folder as this file (project root)
_env_path = Path(__file__).resolve().parent / ".env"
_env_example = Path(__file__).resolve().parent / ".env.example"
if not _env_path.exists() and _env_example.exists():
    shutil.copy(_env_example, _env_path)
    print("Created .env from .env.example. Edit .env and set DB_PASSWORD to your MySQL password if needed.")
load_dotenv(_env_path)


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_port = os.environ.get("DB_PORT", "3306")
    db_name = os.environ.get("DB_NAME", "student_management_system")

    if not db_password:
        print("Error: DB_PASSWORD is not set. Edit the .env file in the project folder and set DB_PASSWORD to your MySQL root password.")
        sys.exit(1)

    user_quoted = quote_plus(db_user)
    password_quoted = quote_plus(db_password)
    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"mysql+pymysql://{user_quoted}:{password_quoted}@{db_host}:{db_port}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from models import (  # noqa: F401
        Student,
        Teacher,
        User,
        UserProfile,
        Feedback,
        Payment,
        Department,
        PasswordResetOTP,
    )

    def _ensure_profile(user: User) -> UserProfile:
        if user.profile:
            return user.profile
        profile = UserProfile(user_id=user.user_id)
        db.session.add(profile)
        db.session.commit()
        return profile

    def _send_email(to_email: str, subject: str, body: str) -> bool:
        smtp_host = os.environ.get("SMTP_HOST", "")
        smtp_port = int(os.environ.get("SMTP_PORT", "587") or "587")
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_password = os.environ.get("SMTP_PASSWORD", "")
        smtp_from = os.environ.get("SMTP_FROM", smtp_user)

        if not (smtp_host and smtp_user and smtp_password and smtp_from and to_email):
            return False

        msg = (
            f"From: {smtp_from}\r\n"
            f"To: {to_email}\r\n"
            f"Subject: {subject}\r\n"
            "\r\n"
            f"{body}\r\n"
        )

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_from, [to_email], msg.encode("utf-8"))
            return True
        except Exception:
            return False

    def _send_sms(to_phone: str, body: str) -> bool:
        twilio_account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
        twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
        twilio_phone_number = os.environ.get("TWILIO_PHONE_NUMBER", "")

        if not (twilio_account_sid and twilio_auth_token and twilio_phone_number and to_phone):
            return False

        try:
            client = Client(twilio_account_sid, twilio_auth_token)
            message = client.messages.create(
                body=body,
                from_=twilio_phone_number,
                to=to_phone
            )
            return True
        except TwilioRestException as e:
            print(f"[SMS ERROR] Twilio failed to send SMS: {e}")
            return False
        except Exception as e:
            print(f"[SMS ERROR] Unexpected error: {e}")
            return False


    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to view this page."

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            user = (
                db.session.query(User)
                .outerjoin(UserProfile, User.user_id == UserProfile.user_id)
                .filter(or_(User.username == username, UserProfile.email == username))
                .first()
            )
            if user and check_password_hash(user.password, password):
                _ensure_profile(user)
                login_user(user)
                flash("Logged in successfully.", "success")
                next_url = request.args.get("next") or url_for("home")
                return redirect(next_url)
            flash("Invalid username or password.", "error")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for("home"))

    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if User.query.count() > 0:
            flash("Setup already complete. Please log in.", "success")
            return redirect(url_for("login"))
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            email = (request.form.get("email") or "").strip() or None
            full_name = (request.form.get("full_name") or "").strip() or None
            phone = (request.form.get("phone") or "").strip() or None
            if not username or not password:
                flash("Username and password are required.", "error")
                return redirect(url_for("setup"))
            if len(password) < 6:
                flash("Password must be at least 6 characters.", "error")
                return redirect(url_for("setup"))
            try:
                user = User(
                    username=username,
                    password=generate_password_hash(password),
                    role="admin",
                )
                db.session.add(user)
                db.session.commit()
                profile = _ensure_profile(user)
                profile.email = email
                profile.full_name = full_name
                profile.phone = phone
                db.session.commit()
                flash("Admin account created. You can now log in.", "success")
                return redirect(url_for("login"))
            except Exception:
                db.session.rollback()
                flash("Username may already exist. Try another.", "error")
                return redirect(url_for("setup"))
        return render_template("setup.html")

    @app.route("/profile", methods=["GET"])
    @login_required
    def profile():
        prof = _ensure_profile(current_user)
        return render_template("profile.html", profile=prof)

    @app.route("/profile/update", methods=["POST"])
    @login_required
    def profile_update():
        prof = _ensure_profile(current_user)
        prof.full_name = (request.form.get("full_name") or "").strip() or None
        prof.email = (request.form.get("email") or "").strip() or None
        prof.phone = (request.form.get("phone") or "").strip() or None
        try:
            db.session.commit()
            flash("Profile updated.", "success")
        except Exception:
            db.session.rollback()
            flash("Email may already be used. Try another.", "error")
        return redirect(url_for("profile"))

    @app.route("/profile/change-password", methods=["GET", "POST"])
    @login_required
    def change_password():
        if request.method == "POST":
            current_pw = request.form.get("current_password") or ""
            new_pw = request.form.get("new_password") or ""
            confirm_pw = request.form.get("confirm_password") or ""

            if not check_password_hash(current_user.password, current_pw):
                flash("Current password is incorrect.", "error")
                return redirect(url_for("change_password"))
            if len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "error")
                return redirect(url_for("change_password"))
            if new_pw != confirm_pw:
                flash("New password and confirm password do not match.", "error")
                return redirect(url_for("change_password"))

            current_user.password = generate_password_hash(new_pw)
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for("profile"))
        return render_template("change_password.html")

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        if request.method == "POST":
            identifier = (request.form.get("identifier") or "").strip()
            if not identifier:
                flash("Enter your username or email.", "error")
                return redirect(url_for("forgot_password"))

            user = (
                db.session.query(User)
                .outerjoin(UserProfile, User.user_id == UserProfile.user_id)
                .filter(or_(User.username == identifier, UserProfile.email == identifier, UserProfile.phone == identifier))
                .first()
            )
            if not user:
                flash("If the account exists, an OTP has been sent.", "success")
                return redirect(url_for("reset_password"))

            prof = _ensure_profile(user)
            if not prof.email and not prof.phone:
                flash("No email or phone link to this account. Contact admin.", "error")
                return redirect(url_for("forgot_password"))

            otp = f"{secrets.randbelow(1000000):06d}"
            expires = datetime.utcnow() + timedelta(minutes=10)
            rec = PasswordResetOTP(user_id=user.user_id, otp_code=otp, expires_at=expires)
            db.session.add(rec)
            db.session.commit()

            subject = "OTP for password reset"
            body = f"Your OTP is {otp}. It expires in 10 minutes."
            
            # Determine if identifier matches email or phone, then send the appropriate notification
            if prof.phone and identifier == prof.phone:
                sent = _send_sms(prof.phone, body)
                if not sent:
                    print(f"[OTP DEBUG] user={user.username} phone={prof.phone} otp={otp}")
                    flash("OTP generated. (Twilio not configured) Check server console for OTP.", "success")
                else:
                    flash("OTP sent to your registered phone number.", "success")
            else:
                sent = _send_email(prof.email, subject, body)
                if not sent:
                    print(f"[OTP DEBUG] user={user.username} email={prof.email} otp={otp}")
                    flash("OTP generated. (SMTP not configured) Check server console for OTP.", "success")
                else:
                    flash("OTP sent to your registered email.", "success")

            return redirect(url_for("reset_password"))
        return render_template("forgot_password.html")

    @app.route("/reset-password", methods=["GET", "POST"])
    def reset_password():
        if request.method == "POST":
            identifier = (request.form.get("identifier") or "").strip()
            otp = (request.form.get("otp") or "").strip()
            new_pw = request.form.get("new_password") or ""
            confirm_pw = request.form.get("confirm_password") or ""

            if len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "error")
                return redirect(url_for("reset_password"))
            if new_pw != confirm_pw:
                flash("New password and confirm password do not match.", "error")
                return redirect(url_for("reset_password"))

            user = (
                db.session.query(User)
                .outerjoin(UserProfile, User.user_id == UserProfile.user_id)
                .filter(or_(User.username == identifier, UserProfile.email == identifier, UserProfile.phone == identifier))
                .first()
            )
            if not user:
                flash("Invalid details.", "error")
                return redirect(url_for("reset_password"))

            rec = (
                PasswordResetOTP.query.filter_by(user_id=user.user_id, otp_code=otp)
                .order_by(PasswordResetOTP.id.desc())
                .first()
            )
            if not rec or rec.used_at is not None:
                flash("Invalid OTP.", "error")
                return redirect(url_for("reset_password"))
            if rec.expires_at < datetime.utcnow():
                flash("OTP expired. Generate a new OTP.", "error")
                return redirect(url_for("forgot_password"))

            user.password = generate_password_hash(new_pw)
            rec.used_at = datetime.utcnow()
            db.session.commit()
            flash("Password reset successfully. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("reset_password.html")

    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/students", methods=["GET"])
    @login_required
    def students():
        all_students = Student.query.order_by(Student.student_id.desc()).all()
        return render_template("student_data.html", students=all_students)

    @app.route("/students/add", methods=["POST"])
    @login_required
    def add_student():
        form = request.form
        father_occ = form.get("father_occupation")
        if father_occ == "Other":
            father_occ = form.get("father_occupation_other")

        try:
            student = Student(
                name=form.get("name"),
                roll_no=form.get("roll_no"),
                enroll_no=form.get("enroll_no"),
                address=form.get("address"),
                pincode=form.get("pincode"),
                total_fees=form.get("total_fees") or 0,
                father_name=form.get("father_name"),
                mother_name=form.get("mother_name"),
                dob=form.get("dob") or None,
                father_salary=form.get("father_salary") or 0,
                father_occupation=father_occ,
            )
            db.session.add(student)
            db.session.commit()
            flash("Student added successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Failed to add student. Please try again.", "error")
        return redirect(url_for("students"))

    @app.route("/students/pay", methods=["POST"])
    @login_required
    def add_payment():
        roll_no = request.form.get("roll_no")
        paid_amount = request.form.get("paid_amount")
        payment_date_str = request.form.get("payment_date")

        if not roll_no or not paid_amount:
            flash("Roll No and Paid Amount are required.", "error")
            return redirect(url_for("students"))

        student = Student.query.filter_by(roll_no=roll_no).first()
        if not student:
            flash(f"Student with Roll No {roll_no} not found.", "error")
            return redirect(url_for("students"))

        try:
            pay_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date() if payment_date_str else datetime.utcnow().date()
            payment = Payment(
                student_id=student.student_id,
                paid_amount=float(paid_amount),
                payment_date=pay_date
            )
            db.session.add(payment)
            db.session.commit()
            flash(f"Payment of {paid_amount} recorded for {student.name} ({roll_no}).", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to record payment: {str(e)}", "error")

        return redirect(url_for("students"))

    @app.route("/students/export", methods=["GET"])
    @login_required
    def export_students():
        students = Student.query.order_by(Student.student_id.desc()).all()
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow([
            'ID', 'Name', 'Roll No', 'Enroll No', 'DOB', 'Address', 'Pincode', 
            'Father Name', 'Mother Name', 'Father Occupation', 'Father Salary', 
            'Total Fees', 'Paid Fees', 'Balance', 'Created At'
        ])
        for s in students:
            cw.writerow([
                f'="{s.student_id}"',
                s.name,
                f'="{s.roll_no}"',
                f'="{s.enroll_no}"' if s.enroll_no else '',
                f'="{s.dob.strftime("%Y-%m-%d")}"' if s.dob else '',
                s.address or '',
                f'="{s.pincode}"' if s.pincode else '',
                s.father_name or '',
                s.mother_name or '',
                s.father_occupation or '',
                f'="{s.father_salary:.2f}"' if s.father_salary else '="0.00"',
                f'="{s.total_fees:.2f}"' if s.total_fees else '="0.00"',
                f'="{s.total_paid:.2f}"' if s.total_paid else '="0.00"',
                f'="{((s.total_fees or 0) - (s.total_paid or 0)):.2f}"',
                f'="{s.created_at.strftime("%Y-%m-%d %H:%M")}"' if s.created_at else ''
            ])
        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=students_data.csv"}
        )

    @app.route("/students/delete/<int:student_id>", methods=["POST"])
    @login_required
    def delete_student(student_id):
        student = Student.query.get_or_404(student_id)
        try:
            Payment.query.filter_by(student_id=student_id).delete()
            db.session.delete(student)
            db.session.commit()
            flash("Student deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to delete student.", "error")
        return redirect(url_for("students"))

    @app.route("/teachers", methods=["GET"])
    @login_required
    def teachers():
        all_teachers = Teacher.query.order_by(Teacher.teacher_id.desc()).all()
        return render_template("teacher_data.html", teachers=all_teachers)

    @app.route("/teachers/add", methods=["POST"])
    @login_required
    def add_teacher():
        form = request.form
        try:
            teacher = Teacher(
                department_id=form.get("department_id") or None,
                teacher_name=form.get("teacher_name"),
                qualification=form.get("qualification"),
                subject=form.get("subject"),
                experience=form.get("experience") or 0,
                salary=form.get("salary") or 0,
                pf=form.get("pf") == "yes",
                esi=form.get("esi") == "yes",
            )
            db.session.add(teacher)
            db.session.commit()
            flash("Teacher added successfully.", "success")
        except Exception:
            db.session.rollback()
            flash("Failed to add teacher. Please try again.", "error")
        return redirect(url_for("teachers"))

    @app.route("/teachers/export", methods=["GET"])
    @login_required
    def export_teachers():
        teachers = Teacher.query.order_by(Teacher.teacher_id.desc()).all()
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow([
            'ID', 'Name', 'Department', 'Qualification', 'Subject', 
            'Experience (Years)', 'Salary', 'PF Enrolled', 'ESI Enrolled', 'Created At'
        ])
        for t in teachers:
            cw.writerow([
                f'="{t.teacher_id}"',
                t.teacher_name,
                t.department.department_name if t.department else '',
                t.qualification or '',
                t.subject or '',
                f'="{t.experience}"' if t.experience else '="0"',
                f'="{t.salary:.2f}"' if t.salary else '="0.00"',
                'Yes' if t.pf else 'No',
                'Yes' if t.esi else 'No',
                f'="{t.created_at.strftime("%Y-%m-%d %H:%M")}"' if t.created_at else ''
            ])
        return Response(
            si.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=teachers_data.csv"}
        )

    @app.route("/teachers/delete/<int:teacher_id>", methods=["POST"])
    @login_required
    def delete_teacher(teacher_id):
        teacher = Teacher.query.get_or_404(teacher_id)
        try:
            db.session.delete(teacher)
            db.session.commit()
            flash("Teacher deleted successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to delete teacher.", "error")
        return redirect(url_for("teachers"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        total_students = db.session.scalar(
            db.select(func.count()).select_from(Student)
        ) or 0
        total_teachers = db.session.scalar(
            db.select(func.count()).select_from(Teacher)
        ) or 0

        total_fees = db.session.scalar(
            db.select(func.coalesce(func.sum(Student.total_fees), 0))
        ) or 0
        total_paid_fees = db.session.scalar(
            db.select(func.coalesce(func.sum(Payment.paid_amount), 0))
        ) or 0
        outstanding_fees = total_fees - total_paid_fees

        total_salary = db.session.scalar(
            db.select(func.coalesce(func.sum(Teacher.salary), 0))
        ) or 0

        top_students = (
            db.session.query(
                Student,
                func.coalesce(func.sum(Payment.paid_amount), 0).label("paid_sum"),
            )
            .outerjoin(Payment, Student.student_id == Payment.student_id)
            .group_by(Student.student_id)
            .order_by(func.coalesce(func.sum(Payment.paid_amount), 0).desc())
            .limit(5)
            .all()
        )
        top_teachers = Teacher.query.order_by(Teacher.salary.desc()).limit(5).all()

        powerbi_embed_url = os.environ.get("POWERBI_EMBED_URL", "")

        return render_template(
            "dashboard.html",
            total_students=total_students,
            total_teachers=total_teachers,
            total_fees=total_fees,
            total_paid_fees=total_paid_fees,
            outstanding_fees=outstanding_fees,
            total_salary=total_salary,
            top_students=top_students,
            top_teachers=top_teachers,
            powerbi_embed_url=powerbi_embed_url,
        )

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact", methods=["GET"])
    def contact():
        return render_template("contact.html")

    @app.route("/feedback", methods=["POST"])
    def feedback():
        form = request.form
        try:
            fb = Feedback(
                name=form.get("name") or None,
                email=form.get("email") or None,
                message=form.get("message"),
            )
            db.session.add(fb)
            db.session.commit()
            flash("Thank you for your feedback.", "success")
        except Exception:
            db.session.rollback()
            flash("Failed to submit feedback. Please try again.", "error")
        return redirect(url_for("contact"))

    @app.cli.command("init-db")
    def init_db_command():
        with app.app_context():
            db.create_all()
        print("Database tables created.")

    return app


# Single app instance so db is always bound when using "flask run" or "from app import app"
app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

