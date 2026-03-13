from datetime import datetime

from flask_login import UserMixin
from extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    department_id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), nullable=False)

    teachers = db.relationship("Teacher", back_populates="department")


class Student(db.Model):
    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True)
    enroll_no = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    address = db.Column(db.Text)
    pincode = db.Column(db.String(10))
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    father_salary = db.Column(db.Numeric(10, 2))
    father_occupation = db.Column(db.String(100))
    total_fees = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship("Payment", back_populates="student")

    @property
    def total_paid(self):
        return sum((p.paid_amount or 0) for p in self.payments)


class Teacher(db.Model):
    __tablename__ = "teachers"

    teacher_id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.department_id"), nullable=True
    )
    teacher_name = db.Column(db.String(100), index=True)
    qualification = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    salary = db.Column(db.Numeric(10, 2))
    pf = db.Column(db.Boolean)
    esi = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.relationship("Department", back_populates="teachers")


class Feedback(db.Model):
    __tablename__ = "feedback"

    feedback_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    message = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


class Payment(db.Model):
    __tablename__ = "payments"

    payment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=True, index=True
    )
    paid_amount = db.Column(db.Numeric(10, 2))
    payment_date = db.Column(db.Date)

    student = db.relationship("Student", back_populates="payments")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "staff"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("UserProfile", back_populates="user", uselist=False)

    def get_id(self):
        return str(self.user_id)


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True)
    full_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    phone = db.Column(db.String(30), nullable=True)

    user = db.relationship("User", back_populates="profile")


class PasswordResetOTP(db.Model):
    __tablename__ = "password_reset_otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, index=True)
    otp_code = db.Column(db.String(10), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



