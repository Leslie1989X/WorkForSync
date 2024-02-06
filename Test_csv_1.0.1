import csv
import pathlib
import pandas as pd

#f1 = pathlib.Path(input("请输入export_csv A路径：").replace('"',''))
#f2 = pathlib.Path(input("请输入export_csv B路径：").replace('"',''))
f1 = pd.read_csv(pathlib.Path(r"E:\OMNIVISION\defect map\11.csv"))
f2 = pd.read_csv(pathlib.Path(r"E:\OMNIVISION\defect map\22.csv"))
coordinate_f1 = f1.loc[:,["col","row","x","y"]] #loc, 用逗号分隔开行和列，先行后列。
coordinate_f2 = f2.loc[:,["col","row","x","y"]]
print("Col:" + str(coordinate_f1.shape[1]))   #获取列数
print("Row:" + str(coordinate_f1.shape[0]))   #获取行数
data1 = []
data2 = []
for index, row in coordinate_f1.iterrows():
    data1.append([row["col"],row["row"]])
for index, row in coordinate_f2.iterrows():
    data2.append([row["col"],row["row"]])
a = []
n = 0  
for i in data1:
   n += 1
   m = 0
   for x in data2:
       m += 1
       if i == x:
           a.append([n-1,m-1,i])
print(a)
print(len(a))
aa = [[row[i] for row in a] for i in range(3)] 
print(aa)
b =[]
for i in range(len(a)):
    b = ([coordinate_f1.loc[[a[i][0]],["x","y"]]])
    print(b)

filename1_1 = 'MapList_output.csv'
path = pathlib.Path(r'E:\OMNIVISION\defect map\test_csv')
MapList_output = open(path/filename1_1, 'w+', newline='')
name = ['NO.1','NO.2','AOI_corrdinate']
try:
    writer = csv.writer(MapList_output)
    writer.writerow(name)
    for i in range(len(a)):
        writer.writerow(a[i])
finally:
    MapList_output.close()
