"""
import csv
MapList = [[1,2],[2,3],[3,4]]
filename1_1 = 'MapList_output.csv'
MapList_output = open(filename1_1, 'w+', newline='')
name = ['map_Row','map_Col']
try:
    writer = csv.writer(MapList_output)
    writer.writerow(name)
    for i in range(len(MapList)):
        writer.writerow(MapList[i])
finally:
    MapList_output.close()
"""
import pathlib
import pandas as pd

f1 = pathlib.Path(input("请输入export_csv A路径：").replace('"',''))
f2 = pathlib.Path(input("请输入export_csv B路径：").replace('"',''))

coordinate_f1 = f1.loc[:,["col","row","x","y"]] #loc, 用逗号分隔开行和列，先行后列。
coordinate_f2 = f2.loc[:,["col","row","x","y"]]
print("Col:" + str(coordinate_f1.shape[1]))   #获取列数
print("Row:" + str(coordinate_f1.shape[0]))   #获取行数
print("Data1")
print(coordinate_f1)
print("Data2")
print(coordinate_f2)
data1 = []
data2 = []
for index, row in coordinate_f1.iterrows():
    data1.append(str(row["col"]) +'+'+ str(row["row"]))
for index, row in coordinate_f2.iterrows():
    data2.append(str(row["col"]) +'+'+ str(row["row"])) 
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
b =[]
for i in range(len(a)):
    c = coordinate_f1.loc[[a[i][0]],["col","row","x","y"]]
    d = coordinate_f2.loc[[a[i][1]],["col","row","x","y"]]
    print(c)
    print(d)
