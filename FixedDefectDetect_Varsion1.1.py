import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.image as Image
import matplotlib.colors as mcolors
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable

import pathlib
import numpy as np
import time
from sklearn.cluster import DBSCAN

import configparser
#import re
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

def get_folder(file_path,pattern = '*',isDir = True):
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

def repeat_thread_detection(funcN):
    for item in threading.enumerate():
        if funcN==item.name:
            return True
    return False  
def thread_it1(func,name:str='test',*args,**kwargs):
    if not repeat_thread_detection(funcN=name):
        global t,event
        event = threading.Event()
        t = threading.Thread(target=func,name=name,args=args,kwargs=kwargs)
        t.daemon = True                               # 守护线程，True: 主进程退出则退出。
        t.start()

class XFunc:
    _event = threading.Event()
    __OSC_path =  r'\\172.34.12.5\rwfabdata'
    __SX_path = r'\\10.162.2.50\sx_eng_data\rwfabdata'
    __test_path_1 = r'D:\OmniVision\RW\AOI\AOI machine and recipe\AOI recipe'
    __test_path_2 = r'E:\CodeProject\VSCodeProjects\My_Projects\work_data\AOI_Recipe'
    __test_path = ''
    __test_raw_path = r'E:\CodeProject\VSCodeProjects\My_Projects\work_data\test_csv'
    def __init__(self) -> None:
        self.root_path = ''
    def _run_in_threading(self,method,*args, **kwargs):
        def thread_func():
            method(*args, **kwargs)
        t = threading.Thread(target=thread_func)
        t.daemon = True
        t.start()
    def xf0(self,event):
        self._run_in_threading(self.xFunc0,event)
    def xf1(self,event):
        self._event.wait()
        self._run_in_threading(self.xFunc1,event)
    def xf2(self,event):
        self._run_in_threading(self.xFunc2,event)
    def xf3(self,event):
        self._run_in_threading(self.xFunc3,event)
    def xf4(self,event):
        self._run_in_threading(self.xFunc4,event)
    def xf5(self,event):
        self._run_in_threading(self.xFunc5,event)
        
    def clear(self,n:int=-1):
        Comboboxes = [com0,com1,com2,com3,com4,com5,com6]
        for i in Comboboxes[n+1:]:
            i.set('')
            i['value'] = []
        if n == -1:
            self.__test_path = ''
            self.root_path = ''
            plt.close('all')
            gc.collect()
            text.delete('1.0','end')
            self._event.clear()
    def xFunc0(self,event):
        print(f"Executing in thread: {threading.current_thread().name}")
        location = com0.get()
        self.clear(n=0)
        if location == 'OSC':
            com1['value'] = ['RCAI'+str(i).rjust(2,'0') for i in range(1,13)]
            self.root_path = self.__OSC_path
        else:
            com1['value'] = ['RW-SCAI01-3','RW-SCAI02-15','RW-SCAI03-68','RW-SCAI04-64','RW-SCAI05-62','RW-SCAI06-58','RW-SCAI07-73','RW-SCAI08-72','RW-SCAI09-71']
            self.root_path = self.__SX_path
        if pathlib.Path(self.root_path).exists():
            print(f'{self.root_path} --> path correct')
            self.__test_path = self.root_path
        elif pathlib.Path(self.__test_path_1).exists():
            print(f'{self.__test_path_1} --> path correct')
            self.__test_path = self.__test_path_1
        elif pathlib.Path(self.__test_path_2).exists():
            print(f'{self.__test_path_2} --> path correct')
            self.__test_path = self.__test_path_2
        else:
            print(f'path error.')
        self._event.set()
    def xFunc1(self,event):
        print(f"Executing in thread: {threading.current_thread().name}")
        machine = com1.get()
        self.clear(n=1)
        pp = f'\\\\{machine}\\c$\\job'
        p = f'\\\\{machine}\\c$\\Falcon\\Scanresults'
        p = pathlib.Path(p)
        pp = pathlib.Path(pp)
        if self.__test_path == '':
            if p.exists():
                p = get_folder(p)
                p_l = [i.name for i in p]
                com2['value'] = p_l
        else:
            p = pathlib.Path(self.__test_path,machine,'Scanresults')
            if p.exists():
                p = get_folder(p)
                p_l = [i.name for i in p]
                com2['value'] = p_l
    def xFunc2(self,event):
        self.clear(n=2)
        machine = com1.get()
        chooseJob = com2.get()
        pp = f'\\\\{machine}\\c$\\job\\{chooseJob}'
        p = f'\\\\{machine}\\c$\\Falcon\\Scanresults\\{chooseJob}'
        pp = pathlib.Path(pp)
        p = pathlib.Path(p)
        if self.__test_path == '':
            if p.exists():
                p = get_folder(p)
                com3['value'] = [i.name for i in p]
                com3.current(0)
                p = get_folder(p[0])
                p_l = [i.name for i in p]
                com4['value'] = p_l
        else:
            p = pathlib.Path(self.__test_path,machine,'Scanresults',chooseJob)
            p = get_folder(p)
            if p == []:
                pass
            else:
                com3['value'] = [i.name for i in p]
                com3.current(0)
                p = get_folder(p[0])
                p_l = [i.name for i in p]
                com4['value'] = p_l        
    def xFunc3(self,event):
        self.clear(n=3)
        machine = com1.get()
        chooseJob = com2.get()
        Setup = com3.get()
        pp = f'\\\\{machine}\\c$\\job\\{chooseJob}\\{Setup}'
        p = f'\\\\{machine}\\c$\\Falcon\\Scanresults\\{chooseJob}\\{Setup}'
        pp = pathlib.Path(pp)
        p = pathlib.Path(p)
        if self.__test_path == '':
            if p.exists():
                p = get_folder(p)
                p_l = [i.name for i in p]
                com4['value'] = p_l
        else:
            p = pathlib.Path(self.__test_path,machine,'Scanresults',chooseJob,Setup)
            p = get_folder(p)
            p_l = [i.name for i in p]
            com4['value'] = p_l
    def xFunc4(self,event):
        self.clear(n=4)
        machine = com1.get()
        chooseJob = com2.get()
        Setup = com3.get()
        Lot = com4.get()
        pp = f'\\\\{machine}\\c$\\job\\{chooseJob}\\{Setup}\\{Lot}'
        p = f'\\\\{machine}\\c$\\Falcon\\Scanresults\\{chooseJob}\\{Setup}\\{Lot}'
        pp = pathlib.Path(pp)
        p = pathlib.Path(p)
        if self.__test_path == '':
            if p.exists():
                p = get_folder(p)
                p_l = [i.name for i in p]
                com5['value'] = p_l
        else:
            p = pathlib.Path(self.__test_path,machine,'Scanresults',chooseJob,Setup,Lot)
            p = get_folder(p)
            p_l = [i.name for i in p]
            com5['value'] = p_l
    def xFunc5(self,event):
        global calCheck,dieLevelReportFolder
        location = com0.get()
        calCheck = False
        dieLevelReportFolder = False
        machine = com1.get()
        job = com2.get()
        setup = com3.get()
        lot = com4.get()
        frameid = com5.get()
        dieLevelReportFile = '_'.join([job,setup,lot,frameid,'Die Level Report.csv'])
        if self.__test_path == '':
            if location == 'OSC':
                dieLevelReportPath1 = f'\\\\172.34.12.5\\rwfabdata\\Line Public\\PE\\JXY\\Reports\\{machine}\\RAW'
                dieLevelReportPath2 = f'\\\\172.34.12.5\\rwfabdata\\Line Public\\PE\\JXY\\ReportsOffline\\{machine}\\RAW'
            else:
                dieLevelReportPath1 = f'\\\\{machine}\\c$\\Reports\\Raw'
                dieLevelReportPath2 = r'c:\Reports\Raw'
            if pathlib.Path(dieLevelReportPath1,dieLevelReportFile).exists():
                dieLevelReportFolder = pathlib.Path(dieLevelReportPath1,dieLevelReportFile)
                text.insert('end','读取的文件路径: '+str(dieLevelReportFolder))
                text.insert('end','\n')
            elif pathlib.Path(dieLevelReportPath2,dieLevelReportFile).exists():
                dieLevelReportFolder = pathlib.Path(dieLevelReportPath2,dieLevelReportFile)
                text.insert('end','读取的文件路径: '+str(dieLevelReportFolder))
                text.insert('end','\n')
            else:
                messagebox.showerror('Wrong','未找到Die Level Report.csv。')
                calCheck = False
                dieLevelReportFolder = False
                return calCheck,dieLevelReportFolder
        else:
            if pathlib.Path(self.__test_raw_path,dieLevelReportFile).exists():
                dieLevelReportFolder = pathlib.Path(self.__test_raw_path,dieLevelReportFile)
                text.insert('end','读取的文件路径: '+str(dieLevelReportFolder))
                text.insert('end','\n')
        df =  pd.read_table(dieLevelReportFolder,header=None)
        index1 = []
        for index, row in df.iterrows():
            r = row.str.split(',')[0]
            for i in r:
                if i.title() in ['Col','Row','X','Y','Area']:
                    index1 = index
                    break
            if index1 != []:
                break
        df = pd.read_csv(dieLevelReportFolder,header=index1)
        cache = df['Class'].unique().tolist()
        cache.extend(['All','WithoutUnreviewed','WithoutGood','AllDefects'])
        com6['value'] = cache
        calCheck = True
        return calCheck,dieLevelReportFolder

def calculate2():
    global calCheck,dieLevelReportFolder
    chooseDefect = com6.get()
    frameid = com5.get()
    if frameid == '':
        messagebox.showerror('Wrong','未选择FrameID。') 
    elif chooseDefect == '':
        messagebox.showerror('Wrong','未选择Defects。')
    elif calCheck and type(dieLevelReportFolder) != bool:
        machine = com1.get()
        job = com2.get()
        setup = com3.get()
        lot = com4.get()
        inipath = f'\\\\{machine}\\c$\\Falcon\\Scanresults\\{job}\\{setup}\\{lot}\\{frameid}\\ProductInfo.ini'
        if pathlib.Path(inipath).exists():
            text.insert('end','读取的INI路径: '+inipath)
            text.insert('end','\n')
            XDieSize,YDieSize,scan2dpixel = findDieSize(inipath)
            Navigator = f'\\\\{machine}\\c$\\Falcon\\Scanresults\\{job}\\{setup}\\Navigator.jpg'
            if not pathlib.Path(Navigator).exists():
                LastActiveRecipe = Metadata2(f'\\\\{machine}\\c$\\job\\{job}\\{setup}\\Metadata.ini')
                Navigator = f'\\\\{machine}\\c$\\job\\{job}\\{setup}\\Recipes\\{LastActiveRecipe}\\Navigator.jpg'
                if not pathlib.Path(Navigator).exists():
                    navigator_r = False
                else:
                    navigator_r = Image.imread(pathlib.Path(Navigator))
            else:
                navigator_r = Image.imread(pathlib.Path(Navigator))
        else:
            inipath = pathlib.Path(r'D:\OmniVision\RW\AOI\AOI machine and recipe\AOI recipe',machine,'Scanresults',job,setup,lot,frameid,'ProductInfo.ini')
            Navigator = pathlib.Path(r'D:\OmniVision\RW\AOI\AOI machine and recipe\AOI recipe',machine,'Scanresults',job,setup,'Navigator.jpg')
            if pathlib.Path(inipath).exists():
                XDieSize,YDieSize,scan2dpixel = findDieSize(inipath)
                if pathlib.Path(Navigator).exists():
                    navigator_r = Image.imread(pathlib.Path(Navigator))
                else:
                    navigator_r = False
            
        df =  pd.read_table(dieLevelReportFolder,header=None)
        index1 = []
        for index, row in df.iterrows():
            r = row.str.split(',')[0]
            for i in r:
                if i.title() in ['Col','Row','X','Y','Area']:
                    index1 = index
                    break
            if index1 != []:
                break
        df = pd.read_csv(dieLevelReportFolder,header=index1)
        df = df.loc[:,['X','Y','Class']]
        del df
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
        x = df.loc[:,'X']
        y = df.loc[:,'Y']
        matrix = np.zeros((y.max(),x.max()),dtype=int)
        for index, row in df.iterrows():
            matrix[row['Y']-1,row['X']-1] += 1
        d = int(calRadius.get())
        n = int(overlapQty.get())
        r = int(topValue.get())
        
        kernel = np.ones((d*2+1,d*2+1),dtype=int)   # 卷积核
        matrix = np.pad(matrix,((d,2*d+1-(matrix.shape[1]+d)%(2*d+1)),(d,2*d+1-(matrix.shape[0]+d)%(2*d+1))),'constant',constant_values=(0,0))
        result,non_expend_result,min_result = convolved2d_with_stride(matrix,kernel,stride=d*2+1)
        #showM(matrix,'D:\\OmniVision\\RW\\AOI\\AOI machine and recipe\\AOI recipe\\RCAI03\\Scanresults\\P-OV08D10-GA5A-BSI-5X-F-sort monitor\\setup1\\OV08D10Scratch\\A332-AP4K456.99-438\\test\\0_{}.jpg'.format(d))
        #showM(result,'D:\\OmniVision\\RW\\AOI\\AOI machine and recipe\\AOI recipe\\RCAI03\\Scanresults\\P-OV08D10-GA5A-BSI-5X-F-sort monitor\\setup1\\OV08D10Scratch\\A332-AP4K456.99-438\\test\\1_{}.jpg'.format(d))
        #showM(non_expend_result,'D:\\OmniVision\\RW\\AOI\\AOI machine and recipe\\AOI recipe\\RCAI03\\Scanresults\\P-OV08D10-GA5A-BSI-5X-F-sort monitor\\setup1\\OV08D10Scratch\\A332-AP4K456.99-438\\test\\2_{}.jpg'.format(d))
        #showM(min_result,'D:\\OmniVision\\RW\\AOI\\AOI machine and recipe\\AOI recipe\\RCAI03\\Scanresults\\P-OV08D10-GA5A-BSI-5X-F-sort monitor\\setup1\\OV08D10Scratch\\A332-AP4K456.99-438\\test\\3_{}.jpg'.format(d))
        result_p2 = np.where(result>n,result,0)
        top_three2 = np.unravel_index(min_result.ravel().argsort()[-int(r):],min_result.shape)
        top_three2 = (np.multiply(top_three2[0],2*d+1),np.multiply(top_three2[1],2*d+1))
        del result, non_expend_result,min_result,matrix
        
        plt.rcParams['font.sans-serif'] = ['SimHei']    # show chinese label
        plt.rcParams['axes.unicode_minus'] = False      # show +/-  
        plt.rcParams['figure.autolayout'] = True  
        
        fig,axes = plt.subplots(1,2,figsize=(12,6),dpi=150)
        vmax = []
        for i,(row,col) in enumerate(zip(*top_three2)):
            if int(result_p2[row,col])==0:
                pass
            else:
                axes[1].annotate(f'{int(result_p2[row,col])}',xy=(col,row),xytext=(-15,-15),
                            textcoords='offset points',ha='center',va='bottom',color = 'black',
                            bbox=dict(boxstyle='round,pad=0.3',fc='yellow',alpha=0.8,edgecolor = 'gray'),
                            arrowprops=dict(arrowstyle='->',connectionstyle='arc3,rad=0'))     # boxstyle: round/rarrow https://blog.csdn.net/TeFuirnever/article/details/88946088
            vmax.append(result_p2[row,col]) 
        masked_result_p2=np.ma.masked_outside(result_p2,1,max(vmax))    # 将colorbar范围外的点掩盖。
        norm = mcolors.Normalize(vmin=0.5,vmax=max(vmax))                 # 创建自定的color范围。
        axes[1].set_ylim(0,YDieSize)
        axes[1].set_xlim(0,XDieSize)
        axes[1].invert_yaxis()                                          # 反转y轴
        if type(navigator_r) != bool:
            axes[1].imshow(navigator_r,aspect='auto',extent=[0,XDieSize,YDieSize,0],cmap='gray',)   # 将导入的图片填充至此坐标轴，按照坐标轴的范围拉伸，颜色为灰度。
        cax2=axes[1].matshow(masked_result_p2,cmap = 'Reds',norm = norm)                    # 将矩阵写入此坐标轴，用自定的正态colorbar。
        divider2 = make_axes_locatable(axes[1])                                             # 创建可分割的轴对象。
        axes[1].set_title('Defects clustering')
        axes[1].xaxis.tick_top()                                                            # 将x轴刻度线移至top
        cax2_colorbar = divider2.append_axes('right',size='5%',pad=0.05)                    # 将colorbar放在轴右边，等高。
        colorbar2 = fig.colorbar(cax2,cax=cax2_colorbar)                                    # 向cax2添加colorbar作为图例。
        colorbar2.set_label('Defects Count')                                                # 设置colorbar标签
        
        if type(navigator_r) != bool:
            axes[0].imshow(navigator_r,aspect='auto',extent=[0,XDieSize,YDieSize,0],cmap='gray')       # 图像填充，拉伸。
        axes[0].scatter(x,y,s=4,c='y',alpha = 0.5)
        #divider0 = make_axes_locatable(axes[0])
        axes[0].set_title('Distribution of original defects')
        axes[0].set_ylim(0,YDieSize)
        axes[0].invert_yaxis()                      # 反转y轴                      
        axes[0].xaxis.tick_top()                    # 将x轴移到顶部
        axes[0].set_xlim(0,XDieSize)
        
        aspect_rato = 'equal'           # 'equal', 3/4; 纵横比。
        axes[1].set_aspect(aspect_rato,adjustable='box')
        axes[0].set_aspect(aspect_rato,adjustable='box')    
        plt.tight_layout()
        text.insert('end',f'正在保存图片...')
        text.insert('end','\n')
        filename = time.strftime("%Y%m%d",time.localtime())
        outputpath = pathlib.Path(root_path,'Line Public','PE','AOI','SortMonitor',filename)
        outputpath.mkdir(parents=True,exist_ok=True)
        plt.savefig(f'{outputpath}\\{chooseDefect} defects_{dieLevelReportFolder.stem}.jpg',bbox_inches='tight')
        plt.show()
        text.insert('end',f'图片保存在:{outputpath}\\{chooseDefect} defects_{dieLevelReportFolder.stem}.jpg')
        text.insert('end','\n')
        gc.collect()

def calculate():
    def childThread(chooseDefect:str,frameid:str,machine:str,job:str,setup:str,lot:str,d:int,n:int,r:int,*args, **kwargs):
        print('Start')
        global calCheck,dieLevelReportFolder,results
        results = []
        navigator_r = False
        XDieSize,YDieSize,scan2dpixel = None,None,None
        if frameid == '':
            messagebox.showerror('Wrong','未选择FrameID。') 
        elif chooseDefect == '':
            messagebox.showerror('Wrong','未选择Defects。')
        elif calCheck and type(dieLevelReportFolder) != bool:
            inipath = f'\\\\{machine}\\c$\\Falcon\\Scanresults\\{job}\\{setup}\\{lot}\\{frameid}\\ProductInfo.ini'
            if pathlib.Path(inipath).exists():
                text.insert('end','读取的INI路径: '+inipath)
                text.insert('end','\n')
                XDieSize,YDieSize,scan2dpixel = findDieSize(inipath)
                Navigator = f'\\\\{machine}\\c$\\Falcon\\Scanresults\\{job}\\{setup}\\Navigator.jpg'
                if not pathlib.Path(Navigator).exists():
                    LastActiveRecipe = Metadata2(f'\\\\{machine}\\c$\\job\\{job}\\{setup}\\Metadata.ini')
                    Navigator = f'\\\\{machine}\\c$\\job\\{job}\\{setup}\\Recipes\\{LastActiveRecipe}\\Navigator.jpg'
                    if not pathlib.Path(Navigator).exists():
                        navigator_r = False
                    else:
                        navigator_r = Image.imread(pathlib.Path(Navigator))
                else:
                    navigator_r = Image.imread(pathlib.Path(Navigator))
            else:
                inipath = pathlib.Path(r'D:\OmniVision\RW\AOI\AOI machine and recipe\AOI recipe',machine,'Scanresults',job,setup,lot,frameid,'ProductInfo.ini')
                Navigator = pathlib.Path(r'D:\OmniVision\RW\AOI\AOI machine and recipe\AOI recipe',machine,'Scanresults',job,setup,'Navigator.jpg')
                if pathlib.Path(inipath).exists():
                    XDieSize,YDieSize,scan2dpixel = findDieSize(inipath)
                    if pathlib.Path(Navigator).exists():
                        navigator_r = Image.imread(pathlib.Path(Navigator))
                    else:
                        navigator_r = False
                
            df =  pd.read_table(dieLevelReportFolder,header=None)
            index1 = []
            for index, row in df.iterrows():
                r = row.str.split(',')[0]
                for i in r:
                    if i.title() in ['Col','Row','X','Y','Area']:
                        index1 = index
                        break
                if index1 != []:
                    break
            df = pd.read_csv(dieLevelReportFolder,header=index1)
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
            clusters,core_sample_mask = clustering(df,eps=d,min_samples=2,min_dice = n)
            results = [df,clusters,core_sample_mask,navigator_r,XDieSize,YDieSize,scan2dpixel]
            print('end')
            return results
    t = threading.Thread(target=childThread,name='calculation',kwargs={'chooseDefect':com6.get(),
                                                                       'frameid': com5.get(),
                                                                       'machine': com1.get(),
                                                                       'job': com2.get(),
                                                                       'setup': com3.get(),
                                                                       'lot': com4.get(),
                                                                       'd':int(calRadius.get()),
                                                                       'n':int(overlapQty.get()),
                                                                       'r': int(topValue.get())
                                                                       })
    t.daemon = True                               # 守护线程，True: 主进程退出则退出。
    t.start()
    t.join()
    global results
    draw(results[0],results[1],core_samples_mask=results[2],navigator_r=results[3],XDieSize=results[4],YDieSize=results[5])

@timer
def clustering(RawData,eps:float=30.0,min_samples:int=2,*args, **kwargs):
    try:
        if type(RawData) == pd.DataFrame:
            X = RawData.loc[:,['X','Y']].values
        elif type(RawData) == np.ndarray:
            X = RawData.copy()
        else:
            raise TypeError
    except TypeError:
        print(f'Data exception, {type(RawData)} is not in [np.ndarray, pd.DataFrame]')
        return None,None
    except Exception as e:
        print(f'Wrong to exec. {e}')
        return None,None
    else:
        dbscan = DBSCAN(eps=eps,min_samples=min_samples)
        clusters = dbscan.fit_predict(X=X)
        core_sample_mask = np.zeros_like(clusters,dtype=bool)
        core_sample_mask[dbscan.core_sample_indices_] = True
        if 'min_dice' in kwargs.keys() and type(RawData) == pd.DataFrame:
            min_dice = kwargs['min_dice']   
            tem = np.unique(clusters)
            tem = tem[tem!=-1]
            for i in tem:
                _cache = RawData.iloc[np.where(clusters == i)]
                if len(set(zip(_cache['Col'],_cache['Row']))) < min_dice:
                    core_sample_mask[np.where(clusters == i)] = False
                    clusters = np.where(clusters == i,-1,clusters)
                else:
                    continue
        return clusters,core_sample_mask
@timer
def draw(RawData:np.ndarray,clusters:np.ndarray,s=10,alpha=0.3,needRect=True,core_samples_mask:np.ndarray=None,*args, **kwargs):
    if type(RawData) == pd.DataFrame:
        X = RawData.loc[:,['X','Y']].values
    elif type(RawData) == np.ndarray:
        X = RawData.copy()
    XDieSize = kwargs['XDieSize'] if 'XDieSize' in kwargs.keys() else None
    YDieSize = kwargs['YDieSize'] if 'YDieSize' in kwargs.keys() else None
    navigator_r = kwargs['navigator_r'] if 'navigator_r' in kwargs.keys() else None
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    plt.rcParams['figure.autolayout'] = True
    # 绘制聚类结果
    if type(core_samples_mask) == np.ndarray:
        plt.scatter(X[:,0],X[:,1],c=np.where(clusters==-1,'gray','green'),s=s,alpha=alpha)
        plt.scatter(X[core_samples_mask,0],X[core_samples_mask,1],c='r',s=s+5,marker='o')
    else:
        plt.scatter(X[:,0],X[:,1],c=clusters,s=s,alpha=alpha)
    if needRect:
        shift = 9
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
                plt.gca().add_patch(rect)
    plt.gca().set_aspect('equal')
    plt.title("基于固定距离的聚类结果")
    plt.xlabel("X轴")
    plt.ylabel("Y轴")
    plt.show()
        
def show():
    a=text.get('-1.0','end')
    if a != '\n':
        a = a.split('\n')[-3]
        a = a.split(':')[-1].strip()
        if pathlib.Path(a).exists():
            aa = Image.imread(pathlib.Path(a))
            plt.axis('off')
            plt.title('Defect Distribution')
            plt.imshow(aa)
            plt.show()
            

def confirm_exit():
    if messagebox.askokcancel("关闭窗口","确定关闭吗？"):
        root.destroy()
        
def clear():
    com0.set('')
    com1.set('')
    com2.set('')
    com3.set('')
    com4.set('')
    com5.set('')
    com6.set('')
    
    com1['value'] = []
    com2['value'] = []
    com3['value'] = []
    com4['value'] = []
    com5['value'] = []
    com6['value'] = []
    plt.close('all')
    gc.collect()
    text.delete('1.0','end')

if __name__ == '__main__':
    root = tk.Tk()
    xfunc = XFunc()
    root.title('Sort Press Defect Detect')
    screenWidth = root.winfo_screenwidth()  #获取显示区域宽度
    screenHeigh = root.winfo_screenheight() #获取显示区域高度
    rootwidth = 600 
    rootheight = 400
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
    tk.Label(fm_1,text='Overlap Qty: ',relief='flat').pack(side='top',anchor='w',fill='x')

    tk.Label(fm_1,text='Top value: ',relief='flat').pack(side='top',anchor='w',fill='x')
    
    # 创建下拉菜单、文本输入框
    fm_r = tk.Frame(root,background='white',padx=0)
    fm_r.pack(side='left',anchor='n',fill='none',expand=False)
    fm_2 = tk.Frame(fm_r,background='white',padx=0)
    fm_2.pack(side='top',anchor='nw',fill='none',expand=False,padx=0)
    com0 = ttk.Combobox(fm_2,width=40)
    com0.pack(side='top',anchor='w',)
    values = ['SX','OSC']
    com0['value'] = values
    com0['state'] = 'readonly'
    #com0.current(2)
    com0.bind('<<ComboboxSelected>>',lambda event: xfunc.xf0(event)) 
    com1 = ttk.Combobox(fm_2,width=40)        # https://blog.csdn.net/ever_peng/article/details/102563786
    com1.pack(side='top',anchor='w',)
    #values = ['RCAI'+str(i).rjust(2,'0') for i in range(1,13)]
    com1['state'] = 'readonly'
    #com1.current(2)
    com1.bind('<<ComboboxSelected>>',lambda event: xfunc.xf1(event)) 
    # 给下拉菜单绑定事件,textvariable=tk.StringVar()
    com2 = ttk.Combobox(fm_2,width=40)
    com2.pack(side='top',anchor='w',ipadx=0)
    com2['state'] = 'readonly'
    com2.bind('<<ComboboxSelected>>',lambda event: xfunc.xf2(event)) 
    com3 = ttk.Combobox(fm_2,width=40)
    com3.pack(side='top',anchor='w')
    com3['state'] = 'readonly'
    com3.bind('<<ComboboxSelected>>',lambda event: xfunc.xf3(event)) 
    com4 = ttk.Combobox(fm_2,width=40)
    com4.pack(side='top',anchor='w')
    com4['state'] = 'readonly'
    com4.bind('<<ComboboxSelected>>',lambda event: xfunc.xf4(event)) 
    com5 = ttk.Combobox(fm_2,width=40)
    com5.pack(side='top',anchor='w')
    com5['state'] = 'readonly'
    com5.bind('<<ComboboxSelected>>',lambda event: xfunc.xf5(event)) 
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
    overlapQty.insert('0',2)
    topValue = tk.Entry(fm_3,background='white',width=10)
    topValue.pack(side='top',anchor='nw')
    topValue.insert('0',10)
    
    fm_32 = tk.Frame(fm_r,background='white',width=100)
    fm_32.pack(side='top',anchor='nw',fill='none',expand=False)
    #button_OK = tk.Button(fm_32, text='Calculate',command=lambda: thread_it(calculate,'calculate'))
    button_OK = tk.Button(fm_32, text='Calculate',command=calculate)
    button_OK.pack(side='left',anchor='nw',fill='both')
    button_clear = tk.Button(fm_32, text='Clear',command=clear)
    button_clear.pack(side='right',anchor='ne',fill='none')
    button_show = tk.Button(fm_32, text='Show',command=show)
    button_show.pack(side='right',anchor='ne',fill='none')
    
    fm_4 = tk.Frame(fm_r,background='white',width=100,height=100)
    fm_4.pack(side='top',anchor='nw',fill='both',expand='yes')
    """
    s2 = tk.Scrollbar(fm_4)
    b2 = tk.Scrollbar(fm_4,orient='horizontal')
    s2.pack(side='right',fill='y')
    b2.pack(side='bottom',fill='x')
    """ 
    text = tk.Text(fm_4)
    text.pack(side='top',anchor='nw',fill='both',expand='yes')
    

      
    fm_5 = tk.Frame(fm_r,background='white')
    fm_5.pack(side='top',anchor='nw')
    tk.Label(fm_5,text='Test Value: ',relief='flat').pack(side='left',anchor='nw',fill='none')
    tk.Entry(fm_5,background='gray',width=20).pack(side='left',anchor='nw')
    
    root.protocol("WM_DELETE_WINDOW",confirm_exit)  # 退出提示     
    root.mainloop()
    
