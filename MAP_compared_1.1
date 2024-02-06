import pathlib
import csv
f1 = pathlib.Path(input("请输入map A路径：").replace('"',''))
while f1.is_file() is not True:
    print('map A不存在，请检查map A路径')
    path1 = input("请输入map A路径：").replace('"','')
    f1 = pathlib.Path(path1)
f2 = pathlib.Path(input("请输入被对比的map B路径：").replace('"',''))
while f2.is_file() is not True:
    print('map B不存在，请检查map B路径')
    path2 = input("请输入map B路径：").replace('"','')
    f2 = pathlib.Path(path2)
x = int(input('第几行为map的第一行：'))
new_path1 = f1.parent
print(new_path1)
file1 = open(f1, 'r+')
filename1 = f1.name    #filename1 = pathlib.Path(path1).stem    #stem 分离文件名，名字和后缀
filename3 = 'different_'+filename1
file2 = open(f2, 'r+')
file3 = open(new_path1/filename3, 'w+')
f1_Date = file1.read().splitlines()
f2_Date = file2.read().splitlines()
n = 0
MapList = []
for i in f1_Date:
    if n < x:
        n += 1
    else:
        m = n-4
        st1 = ''
        lens = len(i)
        y = 0
        while y < lens:
            if i[y] == f2_Date[n][y]:
                st1 += i[y]
            else:
                st1 += '^'
                MapList.append([m,y])
            y += 1
        n += 1
        file3.write(st1+'\n')
file3.close()
filename1_1 = 'MapList_output_'+f1.stem+'.csv'
MapList_output = open(new_path1/filename1_1, 'w+', newline='')
name = ['map_Row','map_Col']
try:
    writer = csv.writer(MapList_output)
    writer.writerow(name)
    for i in range(len(MapList)):
        writer.writerow(MapList[i])
finally:
    MapList_output.close()
