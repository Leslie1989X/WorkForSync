#此程序旨在比较两个csv文件的defect坐标['Col','Row','X','Y']，判断两者共同捕获的defect并反馈出。
import pandas as pd
import pathlib
import csv
f1 = pathlib.Path(input("请输入第一个export csv文件路径：").replace('"',''))
f2 = pathlib.Path(input("请输入第二个export csv文件路径：").replace('"',''))
f3 = f1.parent
file_name = 'result of '+f1.name
result = f3/file_name
f3_W = open(result,"w+",newline="")
name = ['NO.1','NO.2','Coordination']
f1 = pd.read_csv(f1)
f2 = pd.read_csv(f2)
coordination_f1 = f1.loc[:,['Col','Row','X','Y']]
coordination_f2 = f2.loc[:,['Col','Row','X','Y']]
#print(coordination_f1)
a = []
b = []
for index, row in coordination_f1.iterrows():
    a.append([row["Col"],row["Row"],row["X"],row["Y"]])
for index, row in coordination_f2.iterrows():
    b.append([row["Col"],row["Row"],row["X"],row["Y"]])
n = 0
c = []
x = (input("请输入defect的XY坐标允许的偏差值（默认为100）："))
if x == "":
    x = 100
else:
    x = int(x)
for i in a:
    n += 1
    m = 0
    for j in b:
        m += 1
        if i[:2] == j[:2] and abs(int(i[2])-int(j[2])) <= x and abs(int(i[3])-int(j[3])) <= x:
            #print(n,m,j)

            c.append([n,m,j])

#print(a)

try:
    writer = csv.writer(f3_W)
    writer.writerow(name)
    for i in range(len(c)):
        writer.writerow(c[i])
finally:
    f3_W.close()