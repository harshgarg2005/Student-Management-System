import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
import re                               
from student import Student
from storage import save_data, load_data, export_to_excel


def is_valid_gmail(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    return re.match(pattern, email)


def add_student():
    try:
        email = contact_entry.get()     # using Contact field as email

        # ✅ Gmail validation
        if not is_valid_gmail(email):
            messagebox.showerror(
                "Invalid Email",
                "Please enter a valid Gmail address (example@gmail.com)"
            )
            return

        s = Student(
            name_entry.get(),
            roll_entry.get(),
            enroll_entry.get(),
            id_entry.get(),
            email,                    
            dob_entry.get(),
            attendance_entry.get(),
            fees_entry.get(),
            class_entry.get()
        )
        save_data(s)
        messagebox.showinfo("Success", "Student data saved successfully")
        clear_fields()

    except Exception as e:
        messagebox.showerror("Error", str(e))


def show_students():
    load_data()
    messagebox.showinfo("Info", "Student data printed in console")


def export_excel():
    export_to_excel()
    messagebox.showinfo("Success", "Excel file generated")


def clear_fields():
    for entry in entries:
        if isinstance(entry, tk.Entry):
            entry.delete(0, tk.END)


root = tk.Tk()
root.title("Student Management System")
root.geometry("400x500")

labels = [
    "ID", "Name", "Date of Birth", "Contact (Gmail)",
    "Roll", "Enrollment No", "Course/Class",
    "Attendance", "Total Fees"
]

entries = []

for i, text in enumerate(labels):
    tk.Label(root, text=text).grid(row=i, column=0, padx=10, pady=5, sticky="w")

    if text == "Date of Birth":
        entry = DateEntry(root, width=18, date_pattern="yyyy-mm-dd")
    else:
        entry = tk.Entry(root)

    entry.grid(row=i, column=1, padx=10, pady=5)
    entries.append(entry)

(
    id_entry, name_entry, dob_entry, contact_entry,
    roll_entry, enroll_entry, class_entry,
    attendance_entry, fees_entry
) = entries

tk.Button(root, text="Add Student", command=add_student).grid(row=10, column=0, pady=15)
tk.Button(root, text="Show Students", command=show_students).grid(row=10, column=1)
tk.Button(root, text="Export to Excel", command=export_excel).grid(row=11, column=0, columnspan=2, pady=10)

root.mainloop()
