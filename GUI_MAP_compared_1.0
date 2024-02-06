import tkinter as tk
import pathlib
import csv
def Calculate_map():
    path1 = map_path1.get().replace('"','')
    path2 = map_path2.get().replace('"','')
    if len(path1) == 0:
        tk.Label(root, text = 'map A路径不能为空。').pack()
    elif len(path2) == 0:
        tk.Label(root, text = 'map B路径不能为空。').pack()
    else:
        x = 4
        f1 = pathlib.Path(path1)
        f2 = pathlib.Path(path2)
        if f1.is_file() is not True:
            tk.Label(root, text = 'map A不存在。').pack()
        elif f2.is_file() is not True:
            tk.Label(root, text = 'map B不存在。').pack()
        else:
            new_path1 = f1.parent
            file1 = open(f1, 'r+')
            filename1 = pathlib.Path(path1).name    #filename1 = pathlib.Path(path1).stem    #stem 分离文件名，名字和后缀
            filename3 = 'different_'+filename1
            file2 = open(f2, 'r+')
            file3 = open(new_path1/filename3, 'w+')
            f1_Date = file1.read().splitlines()
            f2_Date = file2.read().splitlines()
            n = 0
            MapList = []
            for i in f1_Date:
                if n < x:
                    #f3.write(i+'\n')
                    n += 1
                else:
                    st1 = ''
                    #print(i)
                    lens = len(i)
                    y = 0
                    while y < lens:
                        if i[y] == f2_Date[n][y]:
                            st1 += i[y]
                        else:
                            st1 += '^'
                            m = n-4
                            MapList.append([m,y])
                        y += 1
                    n += 1
                    file3.write(st1+'\n')
            file3.close()
            tk.Label(root, text = '结果输出为：'+str(new_path1/filename3)).pack()
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
root = tk.Tk()
root.title('GUI_test')
screenWidth = root.winfo_screenwidth()  #获取显示区域宽度
screenHeigh = root.winfo_screenheight() #获取显示区域高度
rootwidth = 600 
rootheight = 400
left = (screenWidth-rootwidth)/2
top = (screenHeigh-rootheight)/2
root.geometry('%dx%d+%d+%d'%(rootwidth,rootheight,left,top))    #宽度x高度+x偏移+y偏移
#root.geometry('600x400+50+50')
tk.Label(root,text = '请输入map A路径：').pack(side='top',anchor='n')
map_path1 = tk.Entry(root, width=30, bg='white')
map_path1.pack(side='top',anchor='n')
tk.Label(root,text = '请输入map B路径：').pack(side='top',anchor='n')
map_path2 = tk.Entry(root, width=30, bg='white')
map_path2.pack(side='top',anchor='n')
button_OK = tk.Button(root, text='Calculate', command = Calculate_map).pack()
root.mainloop()
