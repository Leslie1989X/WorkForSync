import pandas as pd
import pathlib

def get_file(file_path,pattern = '.htm'):
	all_file = []
	files = pathlib.Path(file_path).glob(pattern)
	for i in files:
		if pathlib.Path.is_file(i):
			all_file.append(i)
	return all_file

if __name__ == '__main__':
	df = pd.DataFrame()
	paths = pathlib.Path(input("请输入文件夹路径："))
	new_name = paths.parts[-1]+" BatchReport.csv"
	new_paths = paths.parent/'Defect photo Qty Result'
	#new_paths2 = paths.parent
	#new_paths = new_paths2/'Defect photo Qty Result'
	pathlib.Path(new_paths).mkdir(parents=True, exist_ok=True)
	res = get_file(paths,pattern= '*.htm')
	for i in res:
		table_MN = pd.read_html(i)
		#print(f'Total tables:{len(table_MN)}')
		df = df._append(table_MN[2])
	'''
	#测试多表格合并
	for i in range(3):
		df = df._append(table_MN[i])
	print(df)
	'''
	#df = table_MN[2]    #htm文件里有三个表格，这里选择第二个。

	df.to_csv(new_paths/new_name, header=None, index=None)    #导出到csv文件，并且去掉了行号和列号。
