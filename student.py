class Student:
    def __init__(self, name, roll, enroll_number, id, contact, date_of_birth, attendence, total_fees, course_class):
        self.name = name 
        self.roll = roll 
        self.enroll_number = enroll_number
        self.id = id
        self.contact = contact
        self.date_of_birth = date_of_birth
        self.attendence = attendence
        self.total_fees = total_fees
        self.course_class = course_class

    def display(self):
        print(f"Name:{self.name}")
        print(f"Roll:{self.roll}")
        print(f"Enroll Number:{self.enroll_number}")
        print(f"ID:{self.id}")
        print(f"Contact:{self.contact}")
        print(f"Date of Birth:{self.date_of_birth}")
        print(f"Attendence:{self.attendence}")
        print(f"Total Fees:{self.total_fees}")
        print(f"Course Class:{self.course_class}")

if __name__ == "__main__":
    pass
