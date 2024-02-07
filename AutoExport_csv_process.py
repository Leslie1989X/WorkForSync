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
df = pd.DataFrame()
res = get_file(paths,pattern= '*.csv')
for i in res:
    f1_r = pd.read_csv(i,header=18)
    df = df._append(f1_r.loc[:,['Width','Length','Col','Row','X','Y','Classify']])
df.to_csv(paths/"summary.csv", index=None)    #导出到csv文件，并且去掉了行号和列号。
