import os  
import pickle
import pandas as pd
from student import Student 

file_name = "student.pkl"

def save_data(stu):
    students = []
    if os.path.exists(file_name):
        with open(file_name, "rb") as file:
            students = pickle.load(file)

    students.append(stu)

    with open(file_name, "wb") as file: 
        pickle.dump(students, file)

def load_data():
    if not os.path.exists(file_name):
        print("No data found")
        return []

    with open(file_name, "rb") as file: 
        data = pickle.load(file)

    for ele in data: 
        ele.display()

    return data

def export_to_excel():
    students = load_data()
    if not students:
        print("No data to export")
        return

    records = []
    for s in students:
        records.append({
            "ID": s.id,
            "Name": s.name,
            "Roll": s.roll,
            "Enrollment Number": s.enroll_number,
            "Contact": s.contact,
            "Date of Birth": s.date_of_birth,
            "Attendance": s.attendence,
            "Total Fees": s.total_fees,
            "Course/Class": s.course_class
        })

    df = pd.DataFrame(records)
    df.to_excel("students_data.xlsx", index=False)
    print("Data exported to students_data.xlsx")
    print("Excel saved at:", os.path.abspath("students_data.xlsx"))
