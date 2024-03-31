import tkinter as tk
import configparser
import pathlib
import re
import pandas as pd
import time
import pprint
import json
class JobPathList:
    def get_list1(file_path):
        a = pathlib.Path(file_path).iterdir()  # 相当于Path.glob('*')
        return a
    def get_list2(file_path : str):
        all_file = []
        files = pathlib.Path(file_path).glob('**')   # 遍历当前目录下的所有下级文件夹
        for i in files:
            all_file.append(i)
        return all_file
    def get_list3(file_path):
        all_file = []
        files = pathlib.Path(file_path).glob("**/*") # 遍历当前目录下的所有下级文件和文件夹, 等效于bat中的 dir /s/b > file_path.suffix
        for i in files:
            all_file.append(i)
        return all_file
    def get_list4(file_path):
        all_file = []
        files = pathlib.Path(file_path).glob("*") # 遍历当前路径下的文件和文件夹
        for i in files:
            all_file.append(i)
        return all_file
    def get_list5(file_path):
        for p in pathlib.Path(file_path).iterdir():
            for s in p.rglob('*.ini'):  # 遍历给定目录下的所有文件夹下的所有下级文件夹和文件
                yield s #迭代生成器，只能用一次，减少内存占用。对于读取文件产生的不可预测内存占用，可以使用yield设置缓冲区不断的读取文件。
    def JobList(path_list): 
        JobList = [i for i in path_list if i.is_dir() and re.match(RePattern['Job'],str(i))]
        return JobList
def file_output(file_path,data,name):
    with open(pathlib.Path(file_path)/f'{name}','w',encoding='utf-8') as f:
        for i in data:
            f.write(str(i)+'\n')
    pass
class ReadINI:
    def Metadata2(ini_path):
        config = configparser.ConfigParser()
        config.read(pathlib.Path(ini_path))
        sections = config.sections()    # 获取所有的sections名，对大小写敏感
        option = config.options('General')  # 获取指定section名下的所有options变量名，对大小写不敏感。
        value = config.get('General','LastActiveRecipe')    #获取指定section的option的值。
        return {'Last Active Recipe':value}
    def MultiRecipe(ini_path):
        config = configparser.ConfigParser()
        config.read(pathlib.Path(ini_path))
        if config.has_option('Scan','recipe_2'):
            recipe_2 = True
            if config.get('Scan','Recipes') != None:
                link_recipe = True
            else:
                link_recipe = False
        else:
            link_recipe =False
        return {'link_recipe':link_recipe}
        pass
    def ProductInfo(ini_path):
        config = configparser.ConfigParser()
        config.read(pathlib.Path(ini_path))
        value = config.get('General','Scan2DPixelSize')    #获取指定section的option的值。
        return {'Scan2DPixelSize':value}
    def AlignmentData(ini_path):
        config = configparser.ConfigParser()
        config.read(pathlib.Path(ini_path))
        value1 = config.get('General','AlignPointsNum')    #获取指定section的option的名。
        value2 = config.get('General','MinScore')
        return {'AlignPointsNum':value1, 'MinScore':value2}      
    def Waferinfo(ini_path):
        config = configparser.ConfigParser()
        config.read(pathlib.Path(ini_path))
        value = config.get('Recipe','Name')
        quick = config.getboolean('General','key_quickAlign')
        try:
            value1 = config.get('AutoCycleInfo','Machine')    #获取指定section的option的值。
            value2 = config.getboolean('AutoCycleInfo','AutoCycleScan')
            value3 = config.get('AutoCycleInfo','Operator')
            return {'Recipe':value,'quick':quick,'AutoCycleScan':value2,'Operator':value3}
        except configparser.NoOptionError:
            return {'Recipe':value,'quick':quick,'AutoCycleScan':None,'Operator':None}
    def zones(ini_path):
        config = configparser.ConfigParser()
        config.read(pathlib.Path(ini_path))
        ALGName = config.options('ALGName')    #获取指定section的option的名。
        ALGName = {i:config['ALGName'][i] for i in ALGName}
        return ALGName
    def ZonesINI(ini_path):
        config = configparser.ConfigParser()
        config.read(pathlib.Path(ini_path))
        sections = config.sections()
        ZoneName = config['General']['ZoneName']
        TypeName = config['General']['TypeName']
        zoneini = {'ZoneName':ZoneName, 'TypeName':TypeName,'Algorithm': dict()}
        for i in range(1,len(sections)-1):
            AlgorithmName = config.get(f'{sections[i]}','AlgorithmName')
            enable = config.getboolean(f'{sections[i]}','Enable')
            Classify = int(config.get(f'{sections[i]}','Classify'))
            #zoneini[f'Algorithm[{i}]'] = {'name':AlgorithmName,'enable':enable,'Classify':Classify}
            zoneini['Algorithm'][f'{AlgorithmName}'] = {'enable':enable,'Classify':Classify}
            # zoneini[f'enable[{i}]'] = enable
            if AlgorithmName == 'Lynx Pixel':
                noise = str(config.get(f'{sections[i]}','ClutterDenoiseStrength'))
                seed_Bright = str(config.get(f'{sections[i]}','Spot_Bright_SeedThresh'))
                body_Bright = str(config.get(f'{sections[i]}','Spot_Bright_BodyThresh'))
                seed_Dark = str(config.get(f'{sections[i]}','Spot_Dark_SeedThresh'))
                body_Dark = str(config.get(f'{sections[i]}','Spot_Dark_BodyThresh'))
                AlgoDetail = {'noise':noise,
                              'seed_Bright':seed_Bright,
                              'body_Bright':body_Bright,
                              'seed_Dark':seed_Dark,
                              'body_Dark':body_Dark}
                #zoneini[f'Algorithm[{i}]'].update(AlgoDetail)
                zoneini['Algorithm'][f'{AlgorithmName}'].update(AlgoDetail)
            elif AlgorithmName == 'Surface':
                Area_Bright = str(config.get(f'{sections[i]}','BrightArea'))
                Width_Bright = str(config.get(f'{sections[i]}','BrightDiameter'))
                Length_Bright = str(config.get(f'{sections[i]}','BrightLength'))
                Contrast_Bright = str(config.get(f'{sections[i]}','High_Delta'))
                Area_Dark = str(config.get(f'{sections[i]}','DarkArea'))
                Width_Dark = str(config.get(f'{sections[i]}','DarkDiameter'))
                Length_Dark = str(config.get(f'{sections[i]}','DarkLength'))
                Contrast_Dark = str(config.get(f'{sections[i]}','Low_Delta'))
                AlgoDetail = {'Area_Bright':Area_Bright,
                              'Width_Bright':Width_Bright,
                              'Length_Bright':Length_Bright,
                              'Contrast_Bright':Contrast_Bright,
                              'Area_Dark':Area_Dark,
                              'Width_Dark':Width_Dark,
                              'Length_Dark':Length_Dark,
                              'Contrast_Dark':Contrast_Dark}
                #zoneini[f'Algorithm[{i}]'].update(AlgoDetail)
                zoneini['Algorithm'][f'{AlgorithmName}'].update(AlgoDetail)
                pass
            else:
                pass
        return zoneini
        pass
class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
RePattern = {
             'Job':re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+$'),
             'Metadata2':re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+\\[A-Za-z0-9]+\\Metadata.ini'),
             'MultiRecipe':re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+\\[A-Za-z0-9]+\\MultiRecipe.ini'),             
             'ProductInfo':re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+\\[A-Za-z0-9]+\\Recipes\\[A-Za-z0-9]+\\ProductInfo.ini'),
             'ZonesINI':re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+\\[A-Za-z0-9]+\\Recipes\\[A-Za-z0-9]+\\Zones\\.+\.ini'),
             'Waferinfo':re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+\\[A-Za-z0-9]+\\Recipes\\[A-Za-z0-9]+\\Waferinfo.ini'),
             'zones':re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+\\[A-Za-z0-9]+\\Recipes\\[A-Za-z0-9]+\\zones.ini'),
             'AlignmentData': re.compile(r'(.+:.*|\\\\[A-Za-z0-9]+\\c\$)\\Job\\(E-|P-)[ (|)A-Za-z0-9\.%-]+\\[A-Za-z0-9]+\\Recipes\\[A-Za-z0-9]+\\AlignmentData.ini')

            }   
# ini文件的正则匹配
    # Job 匹配job文件夹名
def ini_read():
    #file_path = input('输入Job路径: ').replace('"','')
    file_path = map_path1.get().replace('"','')
    if len(file_path) == 0:
        tk.Label(root, text = '路径不能为空。').pack()
        calculate = False
    elif file_path == '*rcai':
        tk.Label(root, text = 'RCAI_all').pack()
        rcai_list = ['\\rcai01\c$\Job','\\rcai02\c$\Job','\\rcai03\c$\Job','\\rcai04\c$\Job','\\rcai05\c$\Job','\\rcai06\c$\Job','\\rcai07\c$\Job','\\rcai08\c$\Job','\\rcai09\c$\Job','\\rcai10\c$\Job','\\rcai11\c$\Job','\\rcai12\c$\Job']
        calculate = True
        pass

    elif pathlib.Path(file_path).is_dir(): 
        ini_path_list1 = JobPathList.get_list1(file_path)
        joblist = JobPathList.JobList(ini_path_list1)   # 对此进行正则匹配，筛选符合的job目录
        if len(joblist) == 0:
            joblist = JobPathList.JobList([pathlib.Path(file_path)])
            if len(joblist) == 0:
                tk.Label(root, text = '路径内无有效的job文件夹').pack()
                calculate = False
            else:
                calculate = True
                find_machine = 2
        else:
            calculate = True
            find_machine = 1
        
        if calculate:
            start = time.time()
            try:
                machine = str(pathlib.Path(file_path).parents[find_machine].name)
            except IndexError:
                machine = str(pathlib.Path(file_path).anchor.split('\\')[2])
            file_output(file_path,joblist,f'{machine}_joblist_py.txt')
            info_alljob = dict()
            exception = []
            for i in joblist:
                ini_path_list5 = JobPathList.get_list5(i)
                info_job = dict()
                job = pathlib.Path(i).name
                info_job['Job'] = job
                info_job['Last Active Recipe'] = None
                info_job['link_recipe'] = None    
                info_job['Recipes'] = dict()
                try:
                    for ini in ini_path_list5:
                        try:
                            if re.match(RePattern['Metadata2'],str(ini)):
                                LastActiveRecipe = ReadINI.Metadata2(ini)
                                info_job.update(LastActiveRecipe)
                            elif re.match(RePattern['MultiRecipe'],str(ini)):
                                link_recipe = ReadINI.MultiRecipe(ini)
                                info_job.update(link_recipe)
                                pass
                            elif re.match(RePattern['Waferinfo'],str(ini)):
                                WaferInfo = ReadINI.Waferinfo(ini)
                                Curr_recipe = WaferInfo['Recipe']
                                if Curr_recipe in info_job['Recipes'].keys():
                                    info_job['Recipes'][f'{Curr_recipe}'].update(WaferInfo)
                                else:
                                    info_job['Recipes'][f'{Curr_recipe}'] = WaferInfo
                                pass        
                            elif re.match(RePattern['ProductInfo'],str(ini)):
                                Scan2DPixelSize = ReadINI.ProductInfo(ini)
                                info_job['Recipes'][f'{Curr_recipe}'].update(Scan2DPixelSize)
                            elif re.match(RePattern['AlignmentData'],str(ini)):
                                Curr_recipe = ini.parent.name                        
                                AlignPointsNum = ReadINI.AlignmentData(ini)
                                info_job['Recipes'].update({Curr_recipe:dict()})  # #
                                if f'{Curr_recipe}' in info_job['Recipes'].keys():
                                    info_job['Recipes'][f'{Curr_recipe}'].update(AlignPointsNum)
                                else:
                                    info_job['Recipes'][f'{Curr_recipe}'] = AlignPointsNum
                                #MinScore = ReadINI.AlignmentData(ini)[1]
                            elif re.match(RePattern['zones'],str(ini)):
                                ALGName = ReadINI.zones(ini)
                                del ALGName['255']
                                Zones = dict()
                                for key, value in ALGName.items():
                                    Zones[value] = None
                                info_job['Recipes'][f'{Curr_recipe}']['Zones'] = Zones
                                ZoneName = list(ALGName.values())
                            elif re.match(RePattern['ZonesINI'],str(ini)):
                                if ini.stem in ZoneName:
                                    ZoneValue = ReadINI.ZonesINI(ini)
                                    info_job['Recipes'][f'{Curr_recipe}']['Zones'][f"{ZoneValue['ZoneName']}"] = ZoneValue
                                pass
                            else:
                                continue
                        except Exception as e:
                            print('Exception:',e)
                            print('Exception ini file:',ini)
                            exception.append([e,ini])
                            pass
                finally:
                    info_alljob[f'{job}'] = info_job
            pprint.pprint(info_alljob,sort_dicts=False) # sort_dicts=False 不对key进行排序

            with open(pathlib.Path(file_path)/f'{machine}_job_details.json','w',encoding='utf-8') as file:  # https://geek-docs.com/python/python-ask-answer/162_python_how_to_pretty_print_nested_dictionaries.html
                json.dump(info_alljob,file,indent=4,ensure_ascii=False)
            with open(pathlib.Path(file_path)/f'{machine}_exception.txt','w') as file2:
                file2.write(str('[INI Read Exception]\n'))
                for item in exception:
                    file2.write(str(item[0])+': '+str(item[1]) + '\n')
            end = time.time()
            print(f'cost {end-start}s.')

            # dictional to dataframe. ______________________________________
            time2 = time.time()
            exception = []
            try:
                List = [['Machine','N','Job','Last Active Recipe','link_recipe','Recipes','AlignPointsNum','quick','Scan2DPixelSize','Zones','TypeName','Algorithm','Enable','Classify']]
                df = pd.DataFrame(data=None,columns=List[0])
                n = 0 
                for key1, value1 in info_alljob.items():
                    n += 1
                    for key2, value2 in value1['Recipes'].items():
                        try:
                            for key3, value3 in value2['Zones'].items():
                                try:
                                    for key4, value4 in value3['Algorithm'].items():
                                        try:
                                            List.append([machine,n,value1['Job'],value1['Last Active Recipe'],value1['link_recipe'],key2,value2.get('AlignPointsNum',None),value2.get('quick',None),value2.get('Scan2DPixelSize',None),key3,value3.get('TypeName',None),key4,value4.get('enable',None),value4.get('Classify',None)])
                                        except Exception as E:
                                            print(E)
                                            exception.append([E,'Algorithm_loss'])
                                            List.append([machine,n,value1['Job'],value1['Last Active Recipe'],value1['link_recipe'],key2,value2.get('AlignPointsNum',None),value2.get('quick',None),value2.get('Scan2DPixelSize',None),key3,value3.get('TypeName',None),None,None,None])
                                        finally:
                                            df = df._append(pd.Series(List[-1],index=df.columns),ignore_index=True)
                                except Exception as E_Algorithm:
                                    List.append([machine,n,value1['Job'],value1['Last Active Recipe'],value1['link_recipe'],key2,value2.get('AlignPointsNum',None),value2.get('quick',None),value2.get('Scan2DPixelSize',None),key3,None,None,None,None])
                                    df = df._append(pd.Series(List[-1],index=df.columns),ignore_index=True)
                                    exception.append([E_Algorithm,'zone_loss'])
                                    pass
                        except Exception as E_Zones:
                            List.append([machine,n,value1['Job'],value1['Last Active Recipe'],value1['link_recipe'],key2,value2.get('AlignPointsNum',None),value2.get('quick',None),value2.get('Scan2DPixelSize',None),None,None,None,None,None])
                            df = df._append(pd.Series(List[-1],index=df.columns),ignore_index=True)
                            exception.append([E_Zones,'Zones_loss'])
            except Exception as f:
                print(f)
                exception.append([f,'Others'])
                pass
            finally:
                df.to_csv(pathlib.Path(file_path)/f'{machine}_jobs.csv',index=0)
                with open(pathlib.Path(file_path)/f'{machine}_exception.txt','a') as file2:
                    file2.write(str('[Dict to Dataframe Exception]\n'))
                    for item in exception:
                        file2.write(str(item[0])+': '+str(item[1]) + '\n')
                    pass
            time3 = time.time()
            print(f'cost {time3-time2}s')
            tk.Label(root, text = f'文件{machine}_job_details.json, {machine}_jobs.csv, {machine}_exception.txt, {machine}_joblist_py.txt输出在{file_path}下',wraplength=500).pack()
            pass
            return info_alljob, df
    else:
            tk.Label(root, text = '非法路径。').pack()

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Process AOI INI File')
    screenWidth = root.winfo_screenwidth()  #获取显示区域宽度
    screenHeigh = root.winfo_screenheight() #获取显示区域高度
    rootwidth = 600 
    rootheight = 400
    left = (screenWidth-rootwidth)/2
    top = (screenHeigh-rootheight)/2
    root.geometry('%dx%d+%d+%d'%(rootwidth,rootheight,left,top))    #宽度x高度+x偏移+y偏移
    #root.geometry('600x400+50+50')
    tk.Label(root,text = '输入Job路径: ').pack(side='top',anchor='n')
    map_path1 = tk.Entry(root, width=30, bg='white')
    map_path1.pack(side='top',anchor='n')
    button_OK = tk.Button(root, text='Calculate', command = ini_read).pack()
    root.mainloop()
    
    pass
