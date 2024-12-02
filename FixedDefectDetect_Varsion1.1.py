import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.image as Image
import matplotlib.colors as mcolors
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable
import pandastable as pt

import pathlib
import numpy as np
import time
from sklearn.cluster import DBSCAN

import configparser

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading

import gc



"""
采用Cluster的DBSCAN算法对进行聚类。
"""
def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        exedfion_time = end_time - start_time
        print('this is wrapper')
        print(f"任务执行时间: {round(exedfion_time,3)}秒")
        return result
    return wrapper

@timer
def convolved2d_with_stride(matrix,kernel,stride):
    m,n = matrix.shape
    km,kn= kernel.shape
    out_m = (m-km)//stride+1
    out_n = (n-kn)//stride+1
    shape= (out_m,out_n,km,kn)
    strides = (stride*n*matrix.itemsize,stride*matrix.itemsize,n*matrix.itemsize,matrix.itemsize)
    matrix_view = np.lib.stride_tricks.as_strided(matrix,shape=shape,strides=strides)   # https://blog.csdn.net/qq_23869697/article/details/105594571
                                                                                        # https://zhuanlan.zhihu.com1/p/64933417
    result = np.einsum('ijkl,kl->ij',matrix_view,kernel)    # Einstein summation convention. Tensor(matrix_view): ijkl,Tensor(kernel): kl,Tensor(output):ij
    expanded_output = np.zeros_like(matrix)
    expanded_output2 = np.zeros_like(matrix)
    for i in range(out_m):
        for j in range(out_n):
            expanded_output[i*stride:(i+1)*stride,j*stride:(j+1)*stride]=result[i,j]
            expanded_output2[i*stride+(stride-1)//2,j*stride+(stride-1)//2] = result[i,j]
    return expanded_output,expanded_output2,result

def get_folder(file_path,pattern = '*',isDir = True) -> list[pathlib.Path]:
    all_file = []
    files = pathlib.Path(file_path).glob(pattern)
    
    for i in files:
        if pathlib.Path.is_file(i) and not isDir:
            all_file.append(i)
        elif pathlib.Path.is_dir(i) and isDir:
            all_file.append(i)
    return all_file
     
def findDieSize(ini_path):
    config = configparser.ConfigParser()
    config.read(pathlib.Path(ini_path))
    value = config.get('General','Scan2DPixelSize')    #获取指定section的option的值。
    XDieSize = config.get('Geometric','XDieSize')
    YDieSize = config.get('Geometric','YDieSize')
    return int(float(XDieSize)),int(float(YDieSize)),value
def Metadata2(ini_path):
    config = configparser.ConfigParser()
    config.read(pathlib.Path(ini_path))
    sections = config.sections()    # 获取所有的sections名，对大小写敏感
    option = config.options('General')  # 获取指定section名下的所有options变量名，对大小写不敏感。
    value = config.get('General','LastActiveRecipe')    #获取指定section的option的值。
    return value

def LastActiveRecipe(ini_path):
    config = configparser.ConfigParser()
    config.read(pathlib.Path(ini_path))
    sections = config.sections()    # 获取所有的sections名，对大小写敏感
    option = config.options('General')  # 获取指定section名下的所有options变量名，对大小写不敏感。
    value = config.get('General','LastActiveRecipe')    #获取指定section的option的值。
    ProductInfo_path = pathlib.Path(ini_path,'Recipes',value,'ProductInfo.ini')
    Navigator_path = pathlib.Path(ini_path,'Recipes',value,'Navigator.jpg')
    return ProductInfo_path,Navigator_path

        
class XFunc:
    __test_path_ = [r'D:\OmniVision\RW\AOI\AOI machine and recipe\AOI recipe',
                    r'E:\CodeProject\VSCodeProjects\My_Projects\work_data\AOI_Recipe']
    __test_raw_path_ = [r"D:\OmniVision\RW\AOI\AOI machine and recipe\AOI_Data\Reports",
                        r'E:\CodeProject\VSCodeProjects\My_Projects\work_data\test_csv',
                        r'\\172.34.12.5\rwfabdata\Line Public\PE\JXY\Reports',
                        r'\\172.34.12.5\rwfabdata\Line Public\PE\JXY\ReportsOffline']
    __SX_AOI = r'\\10.162.2.50\sx_eng_data\rwfabdata',['RW-SCAI01-3','RW-SCAI02-15','RW-SCAI03-68','RW-SCAI04-64','RW-SCAI05-62','RW-SCAI06-58','RW-SCAI07-73','RW-SCAI08-72','RW-SCAI09-71'],'\\\\{}\\c$\\Reports\\Raw\\{}','c:\\Reports\\Raw\\{}'
    __OSC_AOI = r'\\172.34.12.5\rwfabdata',['RCAI'+str(i).rjust(2,'0') for i in range(1,13)],'\\\\172.34.12.5\\rwfabdata\\Line Public\\PE\\JXY\\ReportsOffline\\{}\\RAW\\{}','\\\\172.34.12.5\\rwfabdata\\Line Public\\PE\\JXY\\Reports\\{}\\RAW\\{}'
    
    def __init__(self) -> None:
        self.root_path = ''
        self.raw_path = ''
        self.results = []
        self.dieLevelReportFolder = False
        self.outputpath = ''
        self.toplevel = dict()
        self.__ENG_Mode = False
        self.__test_path = ''
        self.__test_raw_path = ''
        self._event = threading.Event()
        self.__maxtoplevel = 1
        self._scanresults = ''
    def _run_in_threading(self,method,*args,name:str='childThreading', **kwargs):
        #for i in threading.enumerate(): print(i)
        if kwargs is None:
            kwargs = {}
        if 'kwargs' in kwargs.keys():
            kwargs = kwargs['kwargs']
        def thread_func(*args, **kwargs):
            method(*args, **kwargs)
        t = threading.Thread(target=thread_func,name=name,args=args,kwargs=kwargs)
        t.daemon = True
        t.start()
    def clear(self,*args,n:int=-1, **kwargs):
        global xfunc
        Comboboxes = [com0,com1,com2,com3,com4,com5,com6]
        for i in Comboboxes[n+1:]:
            i.set('')
            i['value'] = [] if i != com0 else i['value']
        if n == -1:
            xfunc.__init__()
            text.delete('1.0','end')
            plt.close('all')
            gc.collect()
    def xf0(self,event):
        self._run_in_threading(self.xFunc0,event)
    def xf1(self,event):
        self._event.wait()
        self._run_in_threading(self.xFunc1,event)
    def xf2(self,event):
        self._event.wait()
        self._run_in_threading(self.xFunc2,event)
    def xf3(self,event):
        self._event.wait()
        self._run_in_threading(self.xFunc3,event)
    def xf4(self,event):
        self._event.wait()
        self._run_in_threading(self.xFunc4,event)
    def xf5(self,event):
        self._event.wait()
        self._run_in_threading(self.xFunc5,event)
    def calculate(self):
        self._event2 = threading.Event()
        frameid = com5.get()
        self.chooseDefect = com6.get()
        if frameid == '':
            messagebox.showerror('Wrong','未选择FrameID。')
            return None
        if self.chooseDefect == '':
            messagebox.showerror('Wrong','未选择Defects。')
            return None
        if type(self.dieLevelReportFolder) == bool:
            messagebox.showerror('Wrong','未找到Die Level Report.csv')
            return None
        else:
            self._event.wait()
            self._run_in_threading(self._calculate,name='calculation',kwargs={'chooseDefect':com6.get(),
                                                                            'frameid': com5.get(),
                                                                            'machine': com1.get(),
                                                                            'chooseJob': com2.get(),
                                                                            'Setup': com3.get(),
                                                                            'Lot': com4.get(),
                                                                            'd':int(calRadius.get()),
                                                                            'n':int(overlapQty.get()),
                                                                            'r': int(topValue.get())
                                                                            })
            self._event2.wait()
            if self.results != []:
                if type(self.results[3]) != bool:
                    text.insert('end','读取的图像路径: '+str(self.results[3]))
                    text.insert('end','\n')
                self.draw(self.results[0],self.results[1],core_samples_mask=self.results[2],navigator_r=self.results[3],XDieSize=self.results[4],YDieSize=self.results[5],dicenum=self.results[6])
        
    def xFunc0(self,event):
        print(f"Executing in thread: {threading.current_thread().name}")
        location = com0.get()
        test = test_entry.get()
        self.clear(n=0)
        filename = time.strftime("%Y%m%d",time.localtime())
        if test.split('|')[0] == 'ENG31235_JXY' and location == 'ENG_TEST':
            self.__ENG_Mode = True
            for i in self.__test_path_:
                if pathlib.Path(i).exists():
                    print(f'{i} --> test path correct')
                    self.__test_path = i
                    self.__outputpath = pathlib.Path(self.__test_path,'test','SortMonitor',filename)
                    break
            else:
                if len(test.split('|')) > 1:
                    self.__test_path = test.split('|')[1].replace('"','')
                    if pathlib.Path(self.__test_path).exists():
                        self.__outputpath = pathlib.Path(self.__test_path,'test','SortMonitor',filename)
                else:
                    messagebox.showerror('Wrong','测试路径无效')
            for i in self.__test_raw_path_:
                if pathlib.Path(i).exists():
                    print(f'{i} --> test raw path correct')
                    self.__test_raw_path = i
                    break
            else:
                if len(test.split('|')) > 2:
                    if pathlib.Path(test.split('|')[2].replace('"','')).exists():
                        self.__test_raw_path = test.split('|')[2].replace('"','')
                    else:
                        messagebox.showerror('Wrong','测试raw路径无效')
            com1['value'] = [i.name for i in get_folder(self.__test_path)]
        else:
            self.__ENG_Mode = False
            if location == 'OSC':
                self.root_path = self.__OSC_AOI[0]
                self.raw_path = self.__OSC_AOI[2:]
                if pathlib.Path(self.root_path).exists():
                    self.__outputpath = pathlib.Path(self.root_path,'Line Public','PE','AOI','SortMonitor',filename)
                    print(f'{self.root_path} --> path correct')                
                    com1['value'] = self.__OSC_AOI[1]
                else:
                    messagebox.showerror('Wrong',f'{self.root_path}路径无效')
                    self.root_path = ''
            elif location == 'SX':
                self.root_path = self.__SX_AOI[0]
                self.raw_path = self.__SX_AOI[2:]
                if pathlib.Path(self.root_path).exists():
                    self.__outputpath = pathlib.Path(self.root_path,'Line Public','PE','AOI','SortMonitor',filename)
                    print(f'{self.root_path} --> path correct')
                    com1['value'] = self.__SX_AOI[1]
                else:
                    messagebox.showerror('Wrong',f'{self.root_path}路径无效')
                    self.root_path = ''
            else:
                messagebox.showinfo('Info','Test Value为空。')
        self._event.set()
    def xFunc1(self,event):
        self._event.clear()
        print(f"Executing in thread: {threading.current_thread().name}")
        machine = com1.get()
        self.clear(n=1)
        if not self.__ENG_Mode:
            self._scanresults = pathlib.Path(f'\\\\{machine}\\c$\\Falcon\\Scanresults')
            self.scanresults = self._scanresults
            if self.root_path != '' and self.scanresults.exists():
                    p = get_folder(self.scanresults)
                    p_l = [i.name for i in p]
                    com2['value'] = p_l
            else:
                messagebox.showerror('Wrong','未找到有效路径。')
        else:
            self._scanresults = pathlib.Path(self.__test_path,machine,'Scanresults')
            self.scanresults = self._scanresults
            if self.__test_path != '' and self.scanresults.exists():
                p = get_folder(self.scanresults)
                p_l = [i.name for i in p]
                com2['value'] = p_l
            else:
                messagebox.showerror('Wrong','未找到有效路径。')
        self._event.set()
    def xFunc2(self,event):
        self._event.clear()
        self.clear(n=2)
        chooseJob = com2.get()
        self.scanresults = pathlib.Path(self._scanresults,chooseJob)
        if self.scanresults.exists():
            p = get_folder(self.scanresults)
            if p == []:
                pass
            else:
                com3['value'] = [i.name for i in p]
                com3.current(0)
                p = get_folder(p[0])
                p_l = [i.name for i in p]
                com4['value'] = p_l
        self._event.set()
    def xFunc3(self,event):
        self._event.clear()
        self.clear(n=3)
        chooseJob = com2.get()
        Setup = com3.get()
        self.scanresults = pathlib.Path(self._scanresults,chooseJob,Setup)
        if self.scanresults.exists():
            p = get_folder(self.scanresults)
            p_l = [i.name for i in p]
            com4['value'] = p_l
        self._event.set()
    def xFunc4(self,event):
        self._event.clear()
        self.clear(n=4)
        chooseJob = com2.get()
        Setup = com3.get()
        Lot = com4.get()
        self.scanresults = pathlib.Path(self._scanresults,chooseJob,Setup,Lot)
        self.outputpath = pathlib.Path(self.__outputpath,Lot)
        if self.scanresults.exists():
            p = get_folder(self.scanresults)
            p_l = [i.name for i in p]
            com5['value'] = p_l
        self._event.set()
    def xFunc5(self,event):
        self._event.clear()
        self.clear(n=5)
        location = com0.get()
        self.dieLevelReportFolder = False
        machine = com1.get()
        chooseJob = com2.get()
        Setup = com3.get()
        Lot = com4.get()
        frameid = com5.get()
        dieLevelReportFile = '_'.join([chooseJob,Setup,Lot,frameid,'Die Level Report.csv'])
        self.scanresults = pathlib.Path(self._scanresults,chooseJob,Setup,Lot,frameid)
        inipath = pathlib.Path(self.scanresults,'ProductInfo.ini')
        if not self.__ENG_Mode:
            for i in self.raw_path:
                if i.count("{}") == 2:
                    _tem = i.format(machine,dieLevelReportFile)
                elif i.count("{}") == 1:
                    _tem = i.format(dieLevelReportFile)
                else:
                    continue
                if pathlib.Path(_tem).exists():
                    self.dieLevelReportFolder = pathlib.Path(_tem)
                    text.insert('end','读取的文件路径: '+_tem)
                    text.insert('end','\n')
                    break
            else:
                messagebox.showerror('Wrong','未找到Die Level Report.csv')
                self.dieLevelReportFolder = False
                self._event.set()
                return self.dieLevelReportFolder
        else:
            if pathlib.Path(self.__test_raw_path,machine,'RAW',dieLevelReportFile).exists():
                self.dieLevelReportFolder = pathlib.Path(self.__test_raw_path,machine,'RAW',dieLevelReportFile)
                text.insert('end','读取的文件路径: '+str(self.dieLevelReportFolder))
                text.insert('end','\n')
            else:
                messagebox.showerror('Wrong','未找到Die Level Report.csv')
                self.dieLevelReportFolder = False
                self._event.set()
                return self.dieLevelReportFolder
        df =  pd.read_table(self.dieLevelReportFolder,header=None)
        self.index1 = []
        for index, row in df.iterrows():
            r = row.str.split(',')[0]
            for i in r:
                if i.title() in ['Col','Row','X','Y','Area']:
                    self.index1 = index
                    break
            if self.index1 != []:
                break
        df = pd.read_csv(self.dieLevelReportFolder,header=self.index1)
        cache = ['All','AllDefects','WithoutGood','WithoutUnreviewed']
        cache.extend(df['Class'].unique().tolist())
        com6['value'] = cache
        com6.set('All')
        self._event.set()
        return self.dieLevelReportFolder
    def clustering(self,RawData,eps:float=30.0,min_samples:int=2, **kwargs):
        __bo = False
        try:
            if type(RawData) == pd.DataFrame:
                if 'Y' in RawData and 'X' in RawData and 'Col' in RawData and 'Row' in RawData:
                    X = RawData.loc[:,['X','Y']].values
                else:
                    raise KeyError
                if 'min_dice' in kwargs.keys() and 'topValue' in kwargs.keys():
                    topValue = kwargs['topValue']
                    min_dice = kwargs['min_dice']
                    __bo = True
                else:
                    __bo = False
            elif type(RawData) == np.ndarray:
                if RawData.shape[1] != 2:
                    raise Exception('Data shape is incorrect')
                X = RawData.copy()
            else:
                raise TypeError
        except TypeError:
            print(f'Data exception, {type(RawData)} is not in [np.ndarray, pd.DataFrame]')
            return None,None,{}
        except KeyError:
            print(f'Data exception, X/Y not in {RawData.columns.to_list()}')
            return None,None,{}
        except Exception as e:
            print(f'Wrong to exec. {e}')
            return None,None,{}
        else:
            dbscan = DBSCAN(eps=eps,min_samples=min_samples)
            clusters = dbscan.fit_predict(X=X)
            core_sample_mask = np.zeros_like(clusters,dtype=bool)
            core_sample_mask[dbscan.core_sample_indices_] = True
            dicenumlist = []
            dicenum = {}
            if __bo: 
                tem = np.unique(clusters)
                tem = tem[tem!=-1]
                for i in tem:
                    _cache = RawData.iloc[np.where(clusters == i)]
                    if len(set(zip(_cache['Col'],_cache['Row']))) < min_dice:
                        core_sample_mask[np.where(clusters == i)] = False
                        clusters = np.where(clusters == i,-1,clusters)
                    else:
                        dicenumlist.append((int(i),len(set(zip(_cache['Col'],_cache['Row'])))))
                        continue
                #dicenumlist = sorted(dicenumlist,key=lambda x: x[1])
                dicenumlist.sort(key=lambda x:x[1],reverse=True)
                dicenumlist = dicenumlist[:topValue]
                dicenum = {i[0]:i[1] for i in dicenumlist}
                
            return clusters,core_sample_mask,dicenum
    def _calculate(self,chooseDefect:str,frameid:str,machine:str,chooseJob:str,Setup:str,Lot:str,d:int,n:int,r:int,*args, **kwargs):
        print('Start')
        self.results = []
        NavigatorPath = False
        XDieSize,YDieSize = 0,0
        inipath = pathlib.Path(self.scanresults,'ProductInfo.ini')
        Navigator = pathlib.Path(self._scanresults,chooseJob,Setup,'Navigator.jpg')
        if Navigator.exists():
            NavigatorPath = Navigator
        elif not self.__ENG_Mode:
            LastActiveRecipe = Metadata2(f'\\\\{machine}\\c$\\job\\{chooseJob}\\{Setup}\\Metadata.ini')
            Navigator = pathlib.Path(f'\\\\{machine}\\c$\\job\\{chooseJob}\\{Setup}\\Recipes\\{LastActiveRecipe}\\Navigator.jpg')
            if Navigator.exists():
                NavigatorPath = Navigator
        if inipath.exists():
            XDieSize,YDieSize,scan2dpixel = findDieSize(inipath)
        elif not self.__ENG_Mode:
            LastActiveRecipe = Metadata2(f'\\\\{machine}\\c$\\job\\{chooseJob}\\{Setup}\\Metadata.ini')
            inipath = pathlib.Path(f'\\\\{machine}\\c$\\job\\{chooseJob}\\{Setup}\\Recipes\\{LastActiveRecipe}\\ProductInfo.ini')
            if inipath.exists():
                XDieSize,YDieSize,scan2dpixel = findDieSize(inipath)
        df = pd.read_csv(self.dieLevelReportFolder,header=self.index1)
        if chooseDefect == 'WithoutUnreviewed':
            df = df[df['Class'] !='unreviewed']
        elif chooseDefect == 'All':
            pass
        elif chooseDefect == 'WithoutGood':
            df = df[df['Class'] !='Good']
        elif chooseDefect == 'AllDefects':
            df = df[df['Class'] !='Good']
            df = df[df['Class'] !='unreviewed']
        else:
            df = df[df['Class']==chooseDefect]
        clusters,core_sample_mask,dicenum = self.clustering(df,eps=d,min_samples=2,min_dice = n,topValue = r)
        self.results = [df,clusters,core_sample_mask,NavigatorPath,XDieSize,YDieSize,dicenum]
        print('end')
        if self.outputpath != '':
            self.outputpath.mkdir(parents=True,exist_ok=True)
            if type(clusters) == np.ndarray:
                tem = np.unique(clusters)
                tem = tem[tem!=-1]
                if len(tem) >1:
                    __fixed = 'True'
                else:
                    __fixed = 'False'
            else:
                __fixed = 'Null'
            with open(f'{str(self.outputpath)}\\{frameid}.txt',mode='w',encoding='utf-8') as f:
                f.write(__fixed)
                
        self._event2.set()
        return 
    def draw(self,RawData,clusters:np.ndarray,s=4,alpha=0.5,needRect=True,core_samples_mask:np.ndarray=None,*args, **kwargs):
        if type(RawData) == pd.DataFrame:
            X = RawData.loc[:,['X','Y']].values
        elif type(RawData) == np.ndarray:
            X = RawData.copy()
        else:
            return
        XDieSize = kwargs['XDieSize'] if 'XDieSize' in kwargs.keys() else 0
        YDieSize = kwargs['YDieSize'] if 'YDieSize' in kwargs.keys() else 0
        XDieSize = max(X[:,0]) if XDieSize == 0 else XDieSize
        YDieSize = max(X[:,1]) if YDieSize == 0 else YDieSize
        Navigator = kwargs['navigator_r'] if 'navigator_r' in kwargs.keys() else False
        dicenum = kwargs['dicenum']
        navigator_r = Image.imread(Navigator) if type(Navigator) != bool else None
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        plt.rcParams['figure.autolayout'] = True
        
        #fig,axes = plt.subplots(1,2,figsize=(12,6),dpi=300)
        fig,self.axes = plt.subplots(1,2,figsize = (12,6),dpi = 150)
        self.axes[0]
        if type(navigator_r) == np.ndarray:
            self.axes[0].imshow(navigator_r,aspect='auto',extent=[0,XDieSize,YDieSize,0],cmap='gray',)
            self.axes[1].imshow(navigator_r,aspect='auto',extent=[0,XDieSize,YDieSize,0],cmap='gray',)
        self.axes[0].scatter(X[:,0],X[:,1],c='y',s=s,alpha=alpha)   
        if type(core_samples_mask) == np.ndarray:
            self.axes[1].scatter(X[:,0],X[:,1],c=np.where(clusters==-1,'gray','green'),s=s,alpha=alpha)
            self.axes[1].scatter(X[core_samples_mask,0],X[core_samples_mask,1],c='r',s=s+3,alpha=alpha)
        else:
            self.axes[1].scatter(X[:,0],X[:,1],c=clusters,s=s,alpha=alpha)
        if needRect:
            shift = 9
            self.rects = dict()
            tem = np.unique(clusters)
            if len(tem) == 1:
                pass
            else:
                tem = np.delete(tem,np.where(tem==-1))
                for i in range(len(tem)):
                    _tem = X[np.where(clusters==tem[i])]
                    xmax,ymax = np.max(_tem,axis=0)
                    xmin,ymin = np.min(_tem,axis=0)
                    rect = plt.Rectangle((xmin-shift,ymin-shift),xmax-xmin+shift*2,ymax-ymin+shift*2,fill = False,edgecolor = 'g',linewidth = 2)
                    self.axes[1].add_patch(rect)
                    self.rects[rect] = tem[i]
                    if tem[i] in dicenum.keys():
                        self.axes[1].annotate(f'{int(dicenum[tem[i]])}',xy=(xmin-shift,ymax+shift),xycoords='data',xytext=(-XDieSize*0.005,-YDieSize*0.003),textcoords='offset points',
                                            bbox=dict(boxstyle='round,pad=0.3',fc='yellow',alpha=alpha,edgecolor='gray'),
                                            arrowprops=dict(arrowstyle='->',connectionstyle='arc3,rad=0'))
                    # plt.annotate() https://blog.csdn.net/leaf_zizi/article/details/82886755
        self.axes[0].set_title('Distribution of original defects')
        self.axes[1].set_title('Defects Clustering')
        self.axes[0].set_ylim(0,YDieSize)
        self.axes[1].set_ylim(0,YDieSize)
        self.axes[0].invert_yaxis()                      # 反转y轴
        self.axes[1].invert_yaxis()
        self.axes[0].xaxis.tick_top()                    # 将x轴移到顶部
        self.axes[1].xaxis.tick_top()
        self.axes[0].set_xlim(0,XDieSize)
        self.axes[1].set_xlim(0,XDieSize)
        aspect_rato = 'equal'           # 'equal', 3/4; 纵横比。
        self.axes[0].set_aspect(aspect_rato,adjustable='box')
        self.axes[1].set_aspect(aspect_rato,adjustable='box') 
        if self.outputpath != '':
            self.outputpath.mkdir(parents=True,exist_ok=True)
            plt.tight_layout()
            plt.savefig(f'{self.outputpath}\\{self.chooseDefect} defects_{self.dieLevelReportFolder.stem}.jpg',bbox_inches='tight')
            text.insert('end',f'图片保存在:{self.outputpath}\\{self.chooseDefect} defects_{self.dieLevelReportFolder.stem}.jpg')
            text.insert('end','\n')
        #cid = fig.canvas.mpl_connect('motion_notify_event', self.on_move)
        cid = fig.canvas.mpl_connect('button_press_event', self.on_click)  # button_press_event, button_release_event
        
        plt.show()
    def show_table(self,*args, **kwargs):
        if len(self.toplevel) >= self.__maxtoplevel:
            messagebox.showerror('Wrong','无法创建更多窗口。')
        elif self.results != []:
            self.new_window = tk.Toplevel(root)
            self.new_window.title(f'Data Review {len(self.toplevel)}')
            self.new_window.protocol("WM_DELETE_WINDOW",lambda windows=len(self.toplevel):self.toplevelclose(windows))
            self.toplevel[len(self.toplevel)]=self.new_window
            self.frame = tk.Frame(self.new_window)
            self.frame.pack()
            
            if 'rect' in kwargs.keys():
                df = self.results[0].iloc[np.where(self.results[1] == self.rects[kwargs['rect']])[0],:]
            else:
                df = self.results[0]
            self.table = pt.Table(self.frame,dataframe=df,showtoolbar=False,showstatusbar=True)
            self.table.show()
            if self.results[6] != []:
                for index,num in self.results[6]:
                    print(index,num)
            self.new_window.mainloop()
        else:
            messagebox.showerror('Wrong','无法创建空窗口。')
            
    def toplevelclose(self,topl):
        print(f'Close {topl}: ',id(self))
        self.toplevel[topl].destroy()
        del self.toplevel[topl]
        
    def markTopValur(self,topValue:int):
        pass
    def on_move(self,event):
        # 如果事件对象是在Axes对象上触发，则执行以下操作
        # https://geek-docs.com/matplotlib/matplotlib-ask-answer/105_matplotlib_how_to_get_a_xy_position_pointing_with_mouse_in_a_interactive_plot_python.html
        if event.inaxes is not None:
            x, y = event.xdata, event.ydata
            #print(x, y)
    
    def on_click(self,event):
        # https://geek-docs.com/matplotlib/matplotlib-ask-answer/matplotlib-click-events_z1.html
        tem = event.inaxes
        if event.button == 1:
            if event.dblclick:
                print('double click')
                x, y = event.xdata, event.ydata
                if event.inaxes is not None:
                    self.__maxtoplevel = len(tem.patches) +1 if len(tem.patches) > 0 else 1
                    for i in tem.patches:
                        if isinstance(i,plt.Rectangle):
                            xmin,ymin = i.xy
                            xmax = xmin + i.get_width()
                            ymax = ymin + i.get_height()
                            if xmin <= x <=xmax and ymin <= y <= ymax:
                                print('True')
                                print(f"Left click at: {event.xdata}, {event.ydata}")
                                self.show_table(rect = i)
        elif event.button == 3:
            print(f"Right click at: {event.xdata}, {event.ydata}")
            
def xf0(event):
    xfunc.xf0(event)
def xf1(event):
    xfunc.xf1(event)
def xf2(event):
    xfunc.xf2(event)
def xf3(event):
    xfunc.xf3(event)
def xf4(event):
    xfunc.xf4(event)
def xf5(event):
    xfunc.xf5(event)
def show_table():
    xfunc.show_table()
def calculate():
    xfunc.calculate()
def clear(*args, **kwargs):
    global xfunc
    print('Before: ',id(xfunc))
    Comboboxes = [com0,com1,com2,com3,com4,com5,com6]
    for i in Comboboxes:
        i.set('')
        i['value'] = [] if i != com0 else i['value']
    __tem = xfunc.toplevel.keys()
    for i in list(__tem):
        xfunc.toplevel[i].destroy()
        del xfunc.toplevel[i]
    del xfunc
    xfunc = XFunc()
    print('After: ',id(xfunc))
    for fig in plt.get_fignums():
        plt.figure(fig)
        plt.close()
    gc.collect()
    text.delete('1.0','end')
    test_entry.select_clear()
    return xfunc
def confirm_exit():
    if messagebox.askokcancel("关闭窗口","确定关闭吗？"):
        root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    #var = tk.StringVar(value='ENG31235_JXY')
    var = tk.StringVar()
    xfunc = XFunc()
    print('mainloop: ',id(xfunc))
    root.title('Sort Press Defect Detect')
    screenWidth = root.winfo_screenwidth()  #获取显示区域宽度
    screenHeigh = root.winfo_screenheight() #获取显示区域高度
    rootwidth = 500
    rootheight = 500
    left = (screenWidth-rootwidth)/2
    top = (screenHeigh-rootheight)/2
    root.geometry('%dx%d+%d+%d'%(rootwidth,rootheight,left,top))    #宽度x高度+x偏移+y偏移
    tk.Label(root,text='Sort monitor的AOI结果压伤分析',relief='flat').pack(side='top',anchor='n',fill='x')
    s1 = tk.Scrollbar(root)
    b1 = tk.Scrollbar(root,orient='horizontal')
    s1.pack(side='right',fill='y')
    b1.pack(side='bottom',fill='x')
    fm_1 = tk.Frame(root,background='white',width=40)
    fm_1.pack(side='left',anchor='n',fill='none',expand=False)
    tk.Label(fm_1,text='Location: ',relief='flat').pack(side='top',anchor='w',expand=False,fill='x')
    tk.Label(fm_1,text='Machine: ',relief='flat').pack(side='top',anchor='w',expand=False,fill='x')
    tk.Label(fm_1,text='Job: ',relief='flat').pack(side='top',anchor='center',expand=False,fill='x')
    tk.Label(fm_1,text='Setup: ',relief='flat').pack(side='top',anchor='center',expand=False,fill='x')
    tk.Label(fm_1,text='Lot: ',relief='flat').pack(side='top',anchor='w',fill='x')
    tk.Label(fm_1,text='Frame ID: ',relief='flat').pack(side='top',anchor='w',fill='x')
    tk.Label(fm_1,text='Defects: ',relief='flat').pack(side='top',anchor='w',fill='x')
    tk.Label(fm_1,text='Calculated radius: ',relief='flat').pack(side='top',anchor='w',fill='x')
    tk.Label(fm_1,text='Dice Qty: ',relief='flat').pack(side='top',anchor='w',fill='x')

    tk.Label(fm_1,text='Top Value: ',relief='flat').pack(side='top',anchor='w',fill='x')
    
    # 创建下拉菜单、文本输入框
    fm_r = tk.Frame(root,background='white',padx=0)
    fm_r.pack(side='left',anchor='n',fill='none',expand=False)
    fm_2 = tk.Frame(fm_r,background='white',padx=0)
    fm_2.pack(side='top',anchor='nw',fill='none',expand=False,padx=0)
    com0 = ttk.Combobox(fm_2,width=40)
    com0.pack(side='top',anchor='w',)
    values = ['OSC','SX','ENG_TEST']
    com0['value'] = values
    com0['state'] = 'readonly'
    #com0.current(2)
    com0.bind('<<ComboboxSelected>>',lambda event: xf0(event)) 
    com1 = ttk.Combobox(fm_2,width=40)        # https://blog.csdn.net/ever_peng/article/details/102563786
    com1.pack(side='top',anchor='w',)
    #values = ['RCAI'+str(i).rjust(2,'0') for i in range(1,13)]
    com1['state'] = 'readonly'
    #com1.current(2)
    com1.bind('<<ComboboxSelected>>',lambda event: xf1(event)) 
    # 给下拉菜单绑定事件,textvariable=tk.StringVar()
    com2 = ttk.Combobox(fm_2,width=40)
    com2.pack(side='top',anchor='w',ipadx=0)
    com2['state'] = 'readonly'
    com2.bind('<<ComboboxSelected>>',lambda event: xf2(event)) 
    com3 = ttk.Combobox(fm_2,width=40)
    com3.pack(side='top',anchor='w')
    com3['state'] = 'readonly'
    com3.bind('<<ComboboxSelected>>',lambda event: xf3(event)) 
    com4 = ttk.Combobox(fm_2,width=40)
    com4.pack(side='top',anchor='w')
    com4['state'] = 'readonly'
    com4.bind('<<ComboboxSelected>>',lambda event: xf4(event)) 
    com5 = ttk.Combobox(fm_2,width=40)
    com5.pack(side='top',anchor='w')
    com5['state'] = 'readonly'
    com5.bind('<<ComboboxSelected>>',lambda event: xf5(event)) 
    com6 = ttk.Combobox(fm_2,width=40,)
    com6.pack(side='top',anchor='w')
    com6['state'] = 'readonly'
    
    fm_31 = tk.Frame(fm_r,background='white',width=100)
    fm_31.pack(side='top',anchor='nw',fill='none',expand=False) 
    fm_3 = tk.Frame(fm_r,background='white',width=100)
    fm_3.pack(side='top',anchor='nw',fill='none',expand=False)  
    calRadius = tk.Entry(fm_31,background='white',width=10)
    calRadius.pack(side='left',anchor='nw')
    calRadius.insert('0',30)
    tk.Label(fm_31,text='range 10-50',relief='flat').pack(side='top',anchor='n',expand=False,fill='x')
    overlapQty = tk.Entry(fm_3,background='white',width=10)
    overlapQty.pack(side='top',anchor='nw')
    overlapQty.insert('0',3)
    topValue = tk.Entry(fm_3,background='white',width=10)
    topValue.pack(side='top',anchor='nw')
    topValue.insert('0',10)
    
    fm_32 = tk.Frame(fm_r,background='white',width=100)
    fm_32.pack(side='top',anchor='nw',fill='none',expand=False)
    #button_OK = tk.Button(fm_32, text='Calculate',command=lambda: thread_it(calculate,'calculate'))
    button_OK = tk.Button(fm_32, text='Calculate',command=lambda : calculate())
    button_OK.pack(side='left',anchor='nw',fill='both')
    button_clear = tk.Button(fm_32, text='Clear',command=lambda xfunc=xfunc:clear(xfunc))
    button_clear.pack(side='right',anchor='ne',fill='none')
    button_show = tk.Button(fm_32, text='Show',command=show_table)
    button_show.pack(side='right',anchor='ne',fill='none')
    
    fm_4 = tk.Frame(fm_r,background='white',width=100,height=100)
    fm_4.pack(side='top',anchor='nw',fill='both',expand='yes')
    s2 = tk.Scrollbar(fm_4)
    b2 = tk.Scrollbar(fm_4,orient='horizontal')
    s2.pack(side='right',fill='y')
    b2.pack(side='bottom',fill='x')
    text = tk.Text(fm_4,height=12)
    text.pack(side='top',anchor='nw',fill='both',expand='yes')
    
    fm_5 = tk.Frame(fm_r,background='white')
    fm_5.pack(side='top',anchor='nw')
    tk.Label(fm_5,text='Test Value: ',relief='flat').pack(side='left',anchor='nw',fill='none')
    test_entry = tk.Entry(fm_5,background='gray',width=60,textvariable=var)
    test_entry.pack(side='left',anchor='nw')
    
    root.protocol("WM_DELETE_WINDOW",confirm_exit)  # 退出提示     
    root.mainloop()
    
