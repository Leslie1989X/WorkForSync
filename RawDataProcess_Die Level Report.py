import pathlib
import pandas as pd
import re
suffix = "*." + input("请输入文件额后缀名(不含.)：")

def get_file(file_path,pattern = suffix):
	all_file = []
	files = pathlib.Path(file_path).glob(pattern)
	for i in files:
		if pathlib.Path.is_file(i):
			all_file.append(i)
	return all_file
pattern = re.compile(r'[A-Za-z0-9- ]+')	#正则表达式1
pattern2 = re.compile(r'Die Level Report.csv$')	#正则表达式2
if __name__=='__main__':
	paths = pathlib.Path(input("请输入文件夹路径："))
	paths_file = paths.parent
	res = get_file(paths,pattern=suffix)
	new_list = []
	j_list  = []
	pattern2_file = []
	df = pd.DataFrame()
	df_pattern2 = pd.DataFrame()
	for i in res:
		x = i.name	#获取文件名
		j = re.findall(pattern,x)	#返回匹配的多个结果，列表
		new_list.append([x, i.stat().st_size])	#将文件名等信息添加到new_list中
		j_list.append(j)
		if re.search(pattern2,x) != None:	#判断文件名是否符合正则表达式pattern2
			pattern2_file.append(i)
	pattern2_col = ['Col','Row','X','Y','Area','Class']

	for i in pattern2_file:
		pattern2_read = pd.read_csv(i,header=3)
		print(pattern2_read)
		pattern2_read2 = pattern2_read.loc[:,['Col','Row','X','Y','Area','Class']]
		df_pattern2 = df_pattern2._append(pattern2_read2)
	pattern2_name = str(paths.name)+'-Die Level Report.csv'
	df_pattern2.to_csv(paths_file/pattern2_name,index=None)

	name = ['name','info']
	name_col = ['Recipe','setup','lot','frame ID','file','suffix']

	file_name = str(paths.name)+'.csv'

	df = pd.DataFrame(columns=name, data=new_list, index=None)
	df_j = pd.DataFrame(columns=name_col, data=j_list,index=None)
	df.to_csv(paths/'1.txt',index=None)
	df_j.to_csv(paths_file/file_name,index=None)
	
        #		print(i.name)   #.name 文件名，包含后缀名，如果是目录则获取目录名
        #		print(i.stem)   #.stem 文件名，不包含后缀
        
import glob
files2 = glob.glob(r'D:\OmniVision\RW\AOI\问题分析\20240204\OVX9000 UNH679\UNH679\*.csv')
