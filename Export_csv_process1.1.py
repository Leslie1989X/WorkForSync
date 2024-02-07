#此程序的作用在于将一个文件夹内的所有csv文件中的['Area','Width','Length','Col','Row','X','Y','Classify']列合并写入一个新的csv文件中，并放在此目录下。

import pandas as pd
import pathlib
import csv

def get_file(file_path,pattern = '.csv'):
	all_file = []
	files = pathlib.Path(file_path).glob(pattern)
	for i in files:
		if pathlib.Path.is_file(i):
			all_file.append(i)
	return all_file

paths = pathlib.Path(input("请输入文件夹路径："))
res = get_file(paths,pattern= '*.csv')
report = paths.name + '.csv'
name = ['Area','Width','Length','Col','Row','X','Y','Classify']

f2 = open(paths/report,'w+',newline="")
for i in res:
	f1 = pd.read_csv(i)
	f1_need = f1.loc[:,['Area','Width','Length','Col','Row','X','Y','Classify']]
	a = []
	for index, row in f1.iterrows():
		a.append([row['Area'],row['Width'],row['Length'],row['Col'],row['Row'],row['X'],row['Y'],row['Classify']])
	writer = csv.writer(f2)
	writer.writerow(name)
	for i in range(len(a)):
		writer.writerow(a[i])
	f1.loc[:]
	f1_need.loc[:]
	a = []
	
f2.close()

