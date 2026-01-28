import pickle   
with open("student.pkl","rb") as file:
    data=pickle.load(file) 
print(data)
for ele in data:
    ele.display() 
