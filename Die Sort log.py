#此程序旨在处理Die Sort log文件夹内的log数据。通过log文件进行前后追溯die位置。
import pathlib
import pandas as pd
import re
def get_file(folder,pattern = '*.TXT'):   #文件名调取函数
	all_file = []
	files = pathlib.Path(folder).glob(pattern)
	for i in files:
		if pathlib.Path.is_file(i):
			all_file.append(i)
	return all_file
def split_colum(colum,sep): #分列函数
	A = colum.str.split(sep, expand=True)
	for col in list(A):
		A[col] = pd.to_numeric(A[col], errors='ignore')	#格式化dataframe，避免分列后数据变成str
	return A
def Die_sort_log(file_folder, device_name):	#单个die sort log文件处理。
	try:
		device_df = pd.read_csv(r'D:\OmniVision\RW\RW yield summary\device.csv')
		CR_Calculate = True
		device_df_1 = device_df[device_df['Device'].isin([device_name])]
		map_frame_col = int(device_df_1.iloc[0,6])
		map_frame_row = int(device_df_1.iloc[0,5])
		map_wafer_col = int(device_df_1.iloc[0,4])
		map_wafer_row = int(device_df_1.iloc[0,3])	
		device_RC = [map_frame_row-1,map_frame_col-1,map_wafer_row-1,map_wafer_col-1]
	except FileNotFoundError:
		CR_Calculate = False
		print('未找匹配的device列表。')
	except IndexError:
		CR_Calculate = False
		print('device错误，未找匹配的device列表。')
	file_stem = file_folder.stem
	file_name = file_folder.name
	df = pd.read_table(file_folder, header=None)
	df_begin = df.loc[df[0].str.match('^Begin|^Wafer')]  #匹配开头是Begin或Wafer的数据，收集成df_begin表
	df_begin = split_colum(df_begin[0],' ').rename(columns={0:'key', 1:'begin frame_lot'}).reset_index()   #分列，按照空格
	df_end = df.iloc[df.shape[0]-1,0].split(':')    #获取最后一行的total值
	df_begin.loc[df_begin.shape[0]] = [df.shape[0]-1,df_end[0],df_end[1]]   #Total填入分列表df_begin表
	print(f'从{file_name}提取的关键行：')
	print(df_begin)
	dict_begin = dict()
	index0 = 0
	for i in range(int((df_begin.shape[0]-1)/2)):
		a = df_begin.loc[i,'begin frame_lot']	#字典的key
		index1 = df_begin.loc[i,'index']
		index2 = df_begin.loc[i+1,'index']
		b = split_colum(df.iloc[index1+1:index2,:][0],',').rename(columns = {0:'Input_X',1:'Input_Y',2:'Output_X',3:'Output_Y'})	#字典的value
		b.insert(loc=0,column='begin Frame',value=a)
		b.insert(loc=0,column='N',value=b.index.values-index1+index0)
		index0 += b.shape[0]
		if CR_Calculate is True:
			b['Input_Col'] = b['Input_Y'].map(lambda x: device_RC[0]-int(x))	
			b['Input_Row'] = b['Input_X'].map(lambda x: device_RC[1]-int(x))
			b['Output_Col'] = b['Output_Y'].map(lambda x: device_RC[0]-int(x))
			b['Output_Row'] = b['Output_X'].map(lambda x: device_RC[1]-int(x))
		dict_begin[a] = b
	header_b = list(b)
	#print(dict_begin)
	
	return dict_begin, header_b, file_stem
def Output_dict_to_csv(path,file,dict,combine_rows=False):	#针对字典的value为dataframe的情况，分别将每个value输出到csv文件。
	if pathlib.Path(file).is_file():
		output_dict_csv = pathlib.Path(file).stem
	elif pathlib.Path(file).is_dir():
		output_dict_csv = pathlib.Path(file).parts[-1]
	elif len(file) > 0:
		output_dict_csv = str(file)
	else:
		output_dict_csv = 'Output_file'
	if path.is_dir():
		pass
	else:
		path = pathlib.Path.cwd()
	if combine_rows is False:
		for key, df in dict.items():
			output_res_filename = f'{output_dict_csv}_{key}.csv'
			df.to_csv(path/output_res_filename, index=False)
		print(f'{output_res_filename}文件输出在{path}.')
	elif combine_rows is True:
		output_res_filename = f'{output_dict_csv}.csv'
		header_b = list(dict[list(dict.keys())[0]])
		empty_df = pd.DataFrame(data=None, columns= header_b)
		empty_df.to_csv(path/output_res_filename, mode='w', index=False)		
		for df in dict.values():
			df.to_csv(path/output_res_filename, mode='a', header=False, index=False)
		print(f'{output_res_filename}文件输出在{path}.')			
def Output_dict_to_excel(path,file,dict, header_is_diff=False):	#针对字典的value为dataframe的情况，输出value到xlsx文件。
	if pathlib.Path(file).is_file():
		output_dict_excel = pathlib.Path(file).stem
	elif pathlib.Path(file).is_dir():
		output_dict_excel = pathlib.Path(file).parts[-1]
	elif len(file) > 0:
		output_dict_excel = str(file)
	else:
		output_dict_excel = 'Output_file'
	if path.is_dir():
		pass
	else:
		path = pathlib.Path.cwd()
	output_dict_xlsx = f'{output_dict_excel}.xlsx'
	if header_is_diff is True:
		with pd.ExcelWriter(path/output_dict_xlsx, engine='openpyxl',mode='w') as writer:	#ExcelWriter，记得输入path，在writer前面输入path就会不断的覆盖写。
			for key, df_value in dict.items():		
				df_value.to_excel(writer, sheet_name = key, index=True)
		print(f'{output_dict_xlsx}文件输出在{path}.')
	elif header_is_diff is False:
		startrow = 1
		header_b = list(dict[list(dict.keys())[0]])
		empty_df = pd.DataFrame(data=None, columns= header_b)
		with pd.ExcelWriter(path/output_dict_xlsx, engine='openpyxl',mode='w') as writer:
			empty_df.to_excel(writer, sheet_name= output_dict_excel, index=True)
		#	for key, df_value in dict_begin.items():
		#		empty_df.to_excel(writer, sheet_name=key, index=True)
		with pd.ExcelWriter(path/output_dict_xlsx, engine='openpyxl',mode='a', if_sheet_exists='overlay') as writer:	#ExcelWriter，记得输入path，在writer前面输入path就会不断的覆盖写。
			for key, df_value in dict.items():
				df_value.to_excel(writer, sheet_name = output_dict_excel, header=False, index=True, startrow = startrow)		
		#		df_value.to_excel(writer, sheet_name = key, index=True)
				startrow += df_value.shape[0]
		print(f'{output_dict_xlsx}文件输出在{path}.')
if __name__=='__main__':	#代码入口，主程序的开始。
	file = input("请输入目标die sort log.txt路径: ").replace('"','')
	while pathlib.Path(file).is_file() is False:
		print("路径有误请重新输入目标die sort log.txt路径: ")
		file = input("请输入目标die sort log.txt路径: ").replace('"','')
		if len(file) == 0:
			file = r'D:\OmniVision\RW\AOI\问题分析\20240220\OV60A40 P3WK77.00\Die Sort log\A361-P3WK77.00-407.TXT'
	file_folder = pathlib.Path(file)  #目标文件的路径
	fff = file_folder.parent.parent/'result'	#获取上上级目录
	if fff.exists():
		pass
	else:
		pathlib.Path(fff).mkdir(parents = True, exist_ok = True) #建立文件夹
	folder = file_folder.parent	#获取上级目录
	file_list_Path = get_file(folder,'*.TXT')	#获取本目录下所有的log文件，生成列表
	device_name = input("请产品型号：").upper()	#可以不填，少一部计算过程。	
	results = Die_sort_log(file_folder,device_name)
	dict_begin = results[0]
	header_b = results[1]
	file_stem = results[2]	
	Output_dict_to_csv(fff,file_stem,dict_begin,combine_rows=True)
	Output_dict_to_excel(fff,file_stem,dict_begin)
#下面的部分目的是：结合每个frame的判定情况（机台导出的RAW csv文件）与die sort log记录进行追溯，查看是否前后判定不一致。
	need_get_frame_file = list(dict_begin.keys())
	need_get_frame_file.insert(0,file_stem)
	print('请将以下内容的RAW Data放入同一个文件夹，并提供文件夹的路径：')
	for i in need_get_frame_file: print(i)
	list_re_pattern = [re.compile(r'[A-Za-z0-9-\. ]+'),re.compile(r'Die Level Report.csv$'),re.compile(r'Surface.csv$')]
	RAW_path = input("请输入文件夹的路径：")
	if len(RAW_path) == 0:
		RAW_path = r'D:\OmniVision\RW\AOI\问题分析\20240220\OV60A40 P3WK77.00\RAW'	#懒得每次测试的时候输入
	else:
		while pathlib.Path(RAW_path).is_dir() is False:
			print("路径有误请重新输入文件夹路径: ")
			RAW_path = input("请输入文件夹的路径：").replace('"','')
	RAW_path_file = pathlib.Path(RAW_path)
	res = get_file(RAW_path_file,pattern='*.csv')
	res_DieLevelReport = [['path','Recipe','setup','lot','frame','file-classify']]
	res_Surface = [['path','Recipe','setup','lot','frame','file-classify']]
	for i in res:
		res_filename = i.name
		if re.search(list_re_pattern[1],res_filename) != None:
			slices = re.findall(list_re_pattern[0],res_filename)	#返回匹配的多个结果，列表
			res_DieLevelReport.append(slices)
			res_DieLevelReport[len(res_DieLevelReport)-1].insert(0,i)			
		elif re.search(list_re_pattern[2],res_filename) != None:
			slices = re.findall(list_re_pattern[0],res_filename)
			res_Surface.append(slices)
			res_Surface[len(res_Surface)-1].insert(0,i)				
	df_DieLevelReport_slices = pd.DataFrame(data=res_DieLevelReport[1:],index=None,columns=res_DieLevelReport[0])
	df_Suface_slices =  pd.DataFrame(data=res_Surface[1:],index=None,columns=res_Surface[0])
	slices_target = df_DieLevelReport_slices.loc[df_DieLevelReport_slices['frame'].isin([need_get_frame_file[0]])]
	slices_compared = df_DieLevelReport_slices.loc[df_DieLevelReport_slices['frame'].isin(need_get_frame_file[1:])]	#待数据匹配的表名
	df_target = pd.read_csv(slices_target.iloc[0,0],header=3)
	df_target.insert(0,'Frame',slices_target.iloc[0,4])
	before_Frame = pd.DataFrame()
	target_CRXY = df_target.loc[:,['Col','Row','X','Y']]
	for index, row in target_CRXY.iterrows():
		CR = [row['Col'],row['Row']]
		for key, df in dict_begin.items():
			CR_before = df[df['Output_Col'].isin([CR[0]]) & df['Output_Row'].isin([CR[1]])]
			before_Frame = before_Frame._append(CR_before)
	before_Frame = before_Frame.reset_index(drop=True)	#重置索引，并删除旧索引。
	df_target[['before Frame','Input_Col','Input_Row']] = before_Frame.loc[:,['begin Frame','Input_Col','Input_Row']]
	n = 0
	m = 0
	t = 10
	classify_df = pd.DataFrame()
	for index, row in df_target.iterrows():
		a = pd.read_csv(slices_compared[slices_compared['frame'] == row['before Frame']].iloc[0,0],header=3)
		b = [row['Input_Col'],row['Input_Row']]
		x = [row['X'],row['Y']]
		compared = pd.DataFrame()
		compared = a[a['Col'].isin([b[0]]) & a['Row'].isin([b[1]])]
		compared.insert(0, 'before Frame', row['before Frame'])

		if compared.empty:
			classify_df = classify_df._append(pd.Series(), ignore_index=True)
			m += 1
		else:
			lens = compared.shape[0]
			for index, row in compared.iterrows():
				y = [row['X'], row['Y']]
				if abs(int(x[0])-int(y[0])) <= t and abs(int(x[1])-int(y[1])) <= t:
					classify_df = classify_df._append(row, ignore_index=True)
					n += 1
					lens -= 1
			if lens == compared.shape[0]:
				classify_df = classify_df._append(pd.Series(None), ignore_index=True)
				m += 1
	print(f'共查找了{len(df_target)}个defect, 未匹配的defect数量: {m}, 匹配到的defeat数量: {n}')
	df_target[['before Classify','before X','before Y']] = classify_df.loc[:,['Class','X','Y']]
	df_target.to_csv(fff/f'{slices_target.iloc[0,4]}_classify_output.csv',index=None)
	print(f'{slices_target.iloc[0,4]}_classify_output.csv文件输出在{fff}.')
