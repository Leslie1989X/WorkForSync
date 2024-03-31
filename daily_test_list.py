import pathlib

with open(pathlib.Path(r'venv1_project/project/Data')/'daily_test_list.txt','r') as file:
    # students = ["甲",23,"乙",31,"丙",32,"丁",100]
    students = eval(file.read().replace('"',''))
print(f'当前学生、成绩列表为：\n{students}')
order = input("选择想要操作的方式：(A)查找(B)新增(C)刪除(D)修改 - 请输入：").upper()
if order == "A":
    同学=input("输入学生的名字: ")
    if 同学 not in students:
        print("查无此人")
    else:
        同学位置=students.index(同学)
        print(f"{students[同学位置]}的成绩是{students[同学位置 + 1]}分")
        # print(students.index(同学))
        # print(students[students.index(同学)])
elif order == "B":
    同学 = input("输入学生的名字: ")
    分數 = input("她/他的成绩是: ")
    students.append(同学)
    students.append(分數)
    同学位置 = students.index(同学)
    print(f"已经完成新学生的添加, {students[同学位置]}的成绩是{students[同学位置+1]}分")
elif order == "C":
        同学 = input("输入学生的名字: ")
        if 同学 not in students:
            print("查無此人")
        else:
            同学位置 = students.index(同学)
            成積 = students[同学位置 + 1]
            students.remove(students[同学位置])
            students.remove(成積)
            print(f"已刪走呢位某利！")

elif order == "D":
    同学 = input("输入学生的名字: ")
    if 同学 not in students:
        print("查无此人")
    else:
        新名字 = input("同学的名字: ")
        新分數 = input("她/他的成绩是: ")
        同学位置 = students.index(同学)
        students[同学位置] = 新名字
        students[students.index(新名字)+1] = 新分數
        print(f"已经完成修改, 学生({students[students.index(新名字)]})的成绩是{students[students.index(新名字)+1]}分")

else:
    print("无此操作功能，请重新再试。")
with open(pathlib.Path(r'venv1_project/project/Data')/'daily_test_list.txt','w') as file:
    file.write(str(students))
        