#针对Raw Data中的Die level Report.csv和surface.csv文件进行整合，提取想要的数据。Col, Row, X, Y, Area, Width, Length, Class, Type
import pathlib
import pandas as pd
import re
pattern = re.compile(r'[A-Za-z0-9- ]+')	#正则表达式1，匹配文件名，除了'_'
pattern2 = re.compile(r'Die Level Report.csv$')	#正则表达式2，匹配文件名
pattern3 = re.compile(r'Surface.csv$')	#正则表达式2，匹配文件名
suffix = "*.csv"
def get_file(file_path,pattern = suffix):
	all_file = []
	files = pathlib.Path(file_path).glob(pattern)
	for i in files:
		if pathlib.Path.is_file(i):
			all_file.append(i)
	return all_file
#以上获取目录中的所有csv文件的信息

if __name__=='__main__':
	Path_NeedProcess = pathlib.Path(input("请输入文件夹的路径："))
	Path_NeedProcess_file = Path_NeedProcess.parent
	res = get_file(Path_NeedProcess,pattern=suffix)
	res_DieLevelReport = []
	res_Surface = []
	for i in res:
		filename = i.name
		if re.search(pattern2,filename) != None:
			res_DieLevelReport.append(i)
		elif re.search(pattern3,filename) != None:
			res_Surface.append(i)
	df_DieLevelReport  = pd.DataFrame()
	for i in res_DieLevelReport:
		DieLevelReport_read = pd.read_csv(i,header=5)
		DieLevelReport_read2 = DieLevelReport_read.loc[:,['Col','Row','X','Y','Area','Class']]
		df_DieLevelReport = df_DieLevelReport._append(DieLevelReport_read2)
	print(df_DieLevelReport)
	df_Surface = pd.DataFrame()
	for i in res_Surface:
		Surface_read = pd.read_csv(i, header=0)
		Surface_read2 = Surface_read.loc[:,['Col','Row','DieX','DieY','Area', 'Width', 'Length', 'Zone', 'Type']]
		df_Surface = df_Surface._append(Surface_read2)
	print(df_Surface)
	df_CombineCol = pd.DataFrame()
	for index, row in df_Surface.iterrows():
		a = [row["Col"],row["Row"],row["DieX"],row["DieY"]]
		print(a)
		for index, row in df_DieLevelReport.iterrows():
			b = [row["Col"],row["Row"],row["X"],row["Y"]]