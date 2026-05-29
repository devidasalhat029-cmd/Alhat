sub1_marks=int(input("Enter the marks of subject 1: "))
sub2_marks=int(input("Enter the marks of subject 2: "))
sub3_marks=int(input("Enter the marks of subject 3: "))
sub4_marks=int(input("Enter the marks of subject 4: "))
sub5_marks=int(input("Enter the marks of subject 5: "))
total_marks=sub1_marks+sub2_marks+sub3_marks+sub4_marks+sub5_marks
percentage=(total_marks/500)*100
print("*******************")
print("Total marks:", total_marks)
print("Percentage:", percentage)
if(percentage>=75):
    print("*****DESTINATION: FIRST CLASS*******")
elif(percentage>=60):    
    print("******FIRST CLASS*******")
elif(percentage>=45):
    print("********PASS********")
else:
    print("********FAIL********")