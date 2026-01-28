import pickle 
import os 
import re
from student import Student 
from storage import load_data,save_data,export_to_excel
def is_valid_gmail(email):    
    pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    return re.match(pattern, email)

def menu():
    while True:
        print('''
                1.Press 1 to Add Data 
                2.Press 2  to Read data 
                3.Press 3 to Export Data to Excel File
                4.Press 4 for Exit ''') 
        choice=input("Enter your choice :")
        if choice=="1":
            id=input("Enter Your ID:")
            name=input("Enter Your Name:")
            date_of_birth=input("Enter Your Date of Birth:")
            contact=input("Enter Your Contact:")
            roll=input("Enter Yo1ur Roll :")
            enroll_number=input("Enter Your Enrollment Number:")
            course_class=input("Enter Your Course Class:")
            attendence=input("Enter Your Attendence:")
            total_fees=input("Enter Your Total Fees:")
            if not is_valid_gmail(contact):
                print("Invalid Gmail address. Use example@gmail.com")
                continue
            s=Student(name,roll,enroll_number,id,contact,date_of_birth,attendence,total_fees,course_class) 
            save_data(s)
        if choice=="2":
            print("Student Details")
            load_data()
        if choice=="3":
            print("Export to Excel File")
            export_to_excel()
        if choice=="4":
            print("Thank You")
            exit() 
            
if __name__=="__main__":
    pass
