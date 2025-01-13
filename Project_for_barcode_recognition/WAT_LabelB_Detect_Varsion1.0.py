import logging.handlers
import numpy as np
import cv2
from pyzbar import pyzbar
import time
import logging
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pathlib
import shutil
import wmi
from pyzbar.pyzbar import ZBarSymbol
from tkinter import messagebox
from tkinter import simpledialog
import tkinter as tk
import threading
import psutil

"""
WatchdogWatImage_0_4_2
"""

class WatChangeHandler(FileSystemEventHandler):
    def __init__(self,path,observer,outputpath) -> None:
        super().__init__()
        self.path = path
        self.observer = observer
        self.events_create = dict()
        self.pattern = re.compile(r'-[^-]+-')
        self.outputpath = outputpath
    
    def on_modified(self, event) -> None:
        
        if event.is_directory:
            logger_fileChange.info("directory modified|{0}".format(event.src_path))
        elif not event.is_directory:
            logger_fileChange.info("file modified|{0}".format(event.src_path))
        #return super().on_modified(event)

    def on_deleted(self, event) -> None:
        if event.is_directory:
            logger_fileChange.info("directory deleted|{0}".format(event.src_path))
            if event.src_path == str(self.path):
                self.observer.stop()
                logger_fileChange.error('TargetFile deleted...')
        else:
            logger_fileChange.info("file deleted|{0}".format(event.src_path))
        pass
        #return super().on_deleted(event)

    def on_moved(self, event) -> None:
        if event.is_directory:
            logger_fileChange.info("directory moved|from {0} to {1}".format(event.src_path,event.dest_path))
        else:
            logger_fileChange.info("file moved|from {0} to {1}".format(event.src_path,event.dest_path))
        pass
        # return super().on_moved(event)

    def on_created(self, event) -> None:
        event_time = time.time()
        if event.is_directory:
            logger_fileCreate.info("directory created|{0}".format(event.src_path))
        else:
            logger_fileCreate.info("file created|{0}".format(event.src_path))
            if pathlib.Path(event.src_path).suffix in ['.jpg','.JPG']:
                if False:#event.src_path in self.events_create.keys():
                    pass
                    # logger_fileCreate.debug(event_time-self.events_create[event.src_path])
                else:
                    #self.events_create[event.src_path] = event_time
                    logger_fileCreate.info(f'Start to detect barcode|{event.src_path}')
                    time.sleep(1)
                    outputpath = self.outputpath
                    read = BarcodeRead(time.time())
                    text,n = read.main(src_path=event.src_path,outputpath=outputpath)
                    endTime = time.time()
                    costTime1 = round(endTime-event_time,4)
                    logger_result.info(f'{pathlib.Path(event.src_path).parent.name}|{pathlib.Path(event.src_path).name}|{costTime1}|{text}|{n}')
                    logger_fileCreate.info(f'End to detect barcode|cost time|{costTime1}s|{text[0]}')
        pass
        # return super().on_created(event)

class BarcodeProcess:
    def __init__(self) -> None:
        pass
    def preprocess_img(img):
        """图片预处理，输出三个结果：\n
        第一个为drawContour后的彩图；
        第二个为裁剪的斜向条形码图；
        第三个为裁剪的横向条形码图；"""
        img1 = img.copy()
        row = img1.shape[0]
        col = img1.shape[1]
        gray1 = cv2.cvtColor(img1,cv2.COLOR_BGR2GRAY)
        ddepth = cv2.CV_32F
        gradX = cv2.Sobel(gray1,ddepth,dx=1,dy=0,ksize=-1)
        gradY = cv2.Sobel(gray1,ddepth,dx=0,dy=1,ksize=-1)
        gradXY = cv2.subtract(gradX,gradY)
        gradXY = cv2.convertScaleAbs(gradXY)
        blur = cv2.blur(gradXY,(9,9))                               # 均值滤波
        _,thresh = cv2.threshold(blur,150,255,cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
        closed = cv2.morphologyEx(thresh,cv2.MORPH_CLOSE,kernel)
        closed = cv2.erode(closed,kernel,iterations=7)
        closed = cv2.dilate(closed,kernel,iterations=5)
        cnts = cv2.findContours(closed,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
        cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
        rect = BarcodeProcess.findSideling(cnts,row,col)
        return rect
    def findSideling(cnts,row,col):
        cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
        for i in range(len(cnts)):
            cnt = cnts[i]
            rect = cv2.minAreaRect(cnt)
            x = rect[0][0]
            y = rect[0][1]
            angle = rect[2]
            if 15 < angle < 75 and x > col*0.6 and y > row*0.55:
                return rect
    def furprocess_img(img):
        """图片二次处理\n
        """
        img_g = cv2.cvtColor(img.copy(),cv2.COLOR_BGR2GRAY)
        img_2 = img.copy()
        # 自适应二值化
        bin_img = cv2.adaptiveThreshold(img_g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 0)
        # 边缘检测
        contours, hierarchy = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = sorted(contours, key=cv2.contourArea,reverse=True)
        rect = cv2.minAreaRect(contour[0])  # 生成此轮廓的最小外接矩形，中心点，(宽度，高度)，倾斜度。
        box = cv2.boxPoints(rect)   # 获取rect外接矩形的四个顶点坐标。
        box = np.intp(box)
        cv2.drawContours(img_2, [box], -1, (0, 255, 0), 3)
        return img_2,rect,box
    def sharpen(img):
        src = img.copy()
        kernel = np.array([[0, -1, 0],
                        [-1, 5, -1],
                        [0, -1, 0]])

        dst = cv2.filter2D(src, -1, kernel)                                     # 锐化
        return dst
    def cv_filter2d(img):
        dst = BarcodeProcess.sharpen(img)
        dst = cv2.bilateralFilter(src=dst, d=0, sigmaColor=100, sigmaSpace=15)  # 双边滤波
        return dst
    def cv_guidedFilter(img):
        dst = BarcodeProcess.sharpen(img)
        dst = cv2.ximgproc.guidedFilter(dst, dst, 15, 12, -1)                   # 导向滤波 https://blog.csdn.net/youcans/article/details/122008763
        return dst
    def gray(img):
        img_1 = img.copy()
        dst = cv2.cvtColor(img_1,cv2.COLOR_BGR2GRAY)
        return dst

    def np_clip(img):
        dst = np.uint8(np.clip((1.1 * img.copy() + 10), 0, 255))
        return dst
    def Rotate2(img,rect:list,dAngle=0.0,dLength=0.0,hh = 0.0,ww = 0.0):
        """图片进一步旋转，裁剪。\n
        不外拓展，争取刚好框选白底。"""
        w = rect[1][0]
        h = rect[1][1]
        if w >= h:
            angle = rect[2]
            w = rect[1][1]
            h = rect[1][0]
            pass
        else:
            angle = rect[2]-90
        rotation_matrix = cv2.getRotationMatrix2D(rect[0],round(angle+dAngle,3),1.0)
        img_box = cv2.warpAffine(img.copy(),rotation_matrix,(img.shape[1],img.shape[0]))
        img_box = cv2.getRectSubPix(img_box,tuple(map(lambda x:int(x),(h+hh+dLength,w+ww+dLength))),tuple(map(lambda x:int(x),rect[0])))
        return img_box
    pass
class BarcodeRead:
    def __init__(self,times) -> None:
        self.pattern = re.compile(r'-[^-]+-')
        self.times= times
        pass
    def read(gray_img,*args):
        n = args[0] if len(args)>0 else ''
        pattern = re.compile(r'^[A-Z]{2}[A-Z0-9]{5}-[A-Z0-9]{4}($|-[A-Z0-9]{2}$|-[-A-Z0-9]{4}$|-[-A-Z0-9]{4}-.{1,4}$)')    # changed
        text = pyzbar.decode(gray_img,symbols=[ZBarSymbol.CODE128,ZBarSymbol.CODE93])
        # TODO 后续增加CODE39的识别。
        if len(text) != 0:
            t = text[0].data.decode('utf-8')
            if re.match(pattern,t) is None or len(t) not in [12,15,17,19]:                     # changed
                print(text[0])
                text = []
            else:
                print(f'Sucess!\n--------',text[0].data.decode('utf-8'),'----',text[0].quality,n)
        else:
            text = []
            #print('Fail!\n--------')
        return text
    
    def checkReadResult(texts):
        text = []
        n = []
        if len(texts) == 2:
            if texts[0][0][0].data.decode('utf-8') == texts[1][0][0].data.decode('utf-8'):
                if texts[0][0][0].quality < texts[1][0][0].quality:
                    text = texts[1][0]
                    n = texts[1][1]
                    return text,n
                else:
                    text = texts[0][0]
                    n = texts[0][1]
                    return text,n
            else:
                return [],[-1]
        elif len(texts) > 2:
            tem = dict()
            for i in texts:
                data = i[0][0].data.decode('utf-8')
                quality = i[0][0].quality
                if data in tem.keys():
                    tem[data].append(quality)
                else:
                    tem[data] = [quality]
            q = [sum(i) for i in tem.values()]
            qty = q.count(max(q))
            try:
                if qty == 1:
                    for key,value in tem.items():
                        if sum(value) == max(q):
                            tar = max(value)
                            for i in texts:
                                if key == i[0][0].data.decode('utf-8') and tar == i[0][0].quality:
                                    n = i[1]
                                    text = i[0]
                                    raise MyExpection('Find target')
                    return [],[-1]
                else:
                    return [],[-1]
            except MyExpection:
                return text,n
            except Exception:
                return [],[-1]
        else:
            return [],[-1]
    def multiRead(img,*args,**kwargs):    
        outputpath = args[0] if len(args) != 0 else None
        x = args[1] if len(args) > 1 else 6
        temp_4 = img.copy()
        global texts
        #texts = kwargs['ts'] if 'ts' in kwargs.keys() else []      # 记录成功读取的内容，data
        result1 = []
        result2 = [-1]
        try:
            for dx in range(0,x):
                temp_4 = BarcodeProcess.np_clip(temp_4) if dx != 0 else temp_4
                n = [dx,4]          # n为处理过程，1：锐化+双边滤波；2：锐化+导向滤波；3；灰度化；4：曝光+10%
                temp_1 = BarcodeProcess.cv_filter2d(temp_4)
                n.append(1)
                text = BarcodeRead.read(temp_1,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 != [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_2 = BarcodeProcess.cv_guidedFilter(temp_1)
                n.append(2)
                text = BarcodeRead.read(temp_1_2,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 != [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_2_3 = BarcodeProcess.gray(temp_1_2)
                n.append(3)
                text = BarcodeRead.read(temp_1_2_3,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_3 = BarcodeProcess.gray(temp_1)
                n.pop()
                n.pop()
                n.append(3)
                del temp_1_2
                del temp_1_2_3
                text = BarcodeRead.read(temp_1_3,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_3_2 = BarcodeProcess.cv_guidedFilter(temp_1_3)
                n.append(2)
                text = BarcodeRead.read(temp_1_3_2,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_1 = BarcodeProcess.cv_filter2d(temp_1)
                n.pop()
                n.pop()
                del temp_1_3
                del temp_1_3_2
                n.append(1)                
                text = BarcodeRead.read(temp_1_1,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_1_3 = BarcodeProcess.gray(temp_1_1)
                n.append(3)                
                text = BarcodeRead.read(temp_1_1_3,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_1_2 = BarcodeProcess.cv_guidedFilter(temp_1_1)
                n.pop()
                del temp_1_1_3
                n.append(2)                
                text = BarcodeRead.read(temp_1_1_2,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                n.pop()
                n.pop()
                n.pop()
                del temp_1_1_2
                del temp_1_1
                del temp_1
                temp_2 = BarcodeProcess.cv_guidedFilter(temp_4)
                n.append(2)                
                text = BarcodeRead.read(temp_2,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                temp_2_1 = BarcodeProcess.cv_filter2d(temp_2)
                n.append(1)
                text = BarcodeRead.read(temp_2_1,n)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 !=  [-1]:
                        raise MyExpection('Read Same Result')
                del temp_2
                del temp_2_1
        except MyExpection as e:
            return result1,result2
        else:
            return [],[-1]
        
    def main(self,src_path,outputpath):
        labelA = pathlib.Path(src_path).stem.strip()                        # 剔除空格 changed
        try:
            lotID = re.search(self.pattern,labelA).group().replace('-','')
        except Exception as LabelAError:
            lotID = labelA
            logger_barcode.error(f'Wrong LabelA|{src_path}')
        outputpath_used = pathlib.Path(pathlib.Path(src_path).parent,'Used')
        pathlib.Path(outputpath_used).mkdir(parents=True,exist_ok=True)
        outputpath_lot = pathlib.Path(outputpath,lotID)
        outputpath_fail=pathlib.Path(outputpath,'fail')
        pathlib.Path(outputpath_fail).mkdir(parents=True,exist_ok=True)
        detect_time = time.time()
        try:
            img = cv2.imread(src_path)
            roateRect = BarcodeProcess.preprocess_img(img)
        except BaseException as except_image_process:
            logger_barcode.error(except_image_process)
            detect_time2 = time.time()
            while round(detect_time2-detect_time,4) < 4.5:
                try:
                    time.sleep(0.5)
                    img = cv2.imread(src_path)
                    roateRect = BarcodeProcess.preprocess_img(img)
                    break
                except Exception:
                    detect_time2 = time.time()
                    continue
            else:
                roateRect = 'Fail to open file'
                logger_barcode.error(f'Fail to open file|{src_path}')
                pass
        if roateRect == None:
            text = ["None"]
            n=['None']
        elif roateRect == 'Fail to open file':
            text = ['Fail to open file']
            n=['Fail to open file']
            pass
        else:
            pathlib.Path(outputpath_lot).mkdir(parents=True,exist_ok=True)                              # 在原来的目标目录下新建lot名的文件夹
            text = []
            n=[-1]
            global texts
            texts = []            
            for dA in [0,1,2,-1,-2,3,-3]:
                if time.time()-self.times > 100:
                    text,n = [],[-1]
                    break
                image2 = BarcodeProcess.Rotate2(img.copy(),roateRect,dAngle=dA,hh=300,ww=70)    # 裁剪1次的label B
                text,n = BarcodeRead.multiRead(image2,outputpath_lot)
                if text == []:
                    cv2.imwrite(f'{outputpath_lot}/{labelA}.jpg',image2)
                    image2_jpg = cv2.imread(f'{outputpath_lot}/{labelA}.jpg')
                    text,n = BarcodeRead.multiRead(image2_jpg,outputpath_lot)
                    pathlib.Path(f'{outputpath_lot}/{labelA}.jpg').unlink()
                    if text == []:
                        results = BarcodeProcess.furprocess_img(image2_jpg)[1]
                        image2_jpg_box = BarcodeProcess.Rotate2(image2_jpg,results,0,0,0,0)
                        text,n = BarcodeRead.multiRead(image2_jpg_box,outputpath_lot)
                        if text == []:
                            results2 = BarcodeProcess.furprocess_img(image2.copy())[1]
                            image2_box = BarcodeProcess.Rotate2(image2,results2,0,0,0,0)
                            text,n = BarcodeRead.multiRead(image2_box,outputpath_lot)
                            if text == []:
                                cv2.imwrite(f'{outputpath_lot}/{labelA}.jpg',image2_box)
                                image2_box_jpg = cv2.imread(f'{outputpath_lot}/{labelA}.jpg')
                                text,n = BarcodeRead.multiRead(image2_box_jpg,outputpath_lot)
                                pathlib.Path(f'{outputpath_lot}/{labelA}.jpg').unlink()
                                if text == []:
                                    """新增angle判定，之前angle出现错误。"""
                                    if results2[1][0] >= results2[1][1]:
                                        angle = round(results2[2],1)
                                    else:
                                        angle = round(results2[2]-90,1)
                                    """end"""
                                    for i in np.arange(-0.5,0.6,0.1):
                                        if time.time()-self.times > 100:
                                            text,n = [],[-1]
                                            break
                                        image2_m = BarcodeProcess.Rotate2(img.copy(),roateRect,dAngle=round(round(i,1)+angle,1),hh=300,ww=70)
                                        text,n = BarcodeRead.multiRead(image2_m,outputpath_lot)
                                        if text == []:
                                            results3 = BarcodeProcess.furprocess_img(image2_m)[1]
                                            image2_m_box = BarcodeProcess.Rotate2(image2_m,results3)
                                            text,n = BarcodeRead.multiRead(image2_m_box,outputpath_lot)
                                            if text ==[]:
                                                continue
                                            else:
                                                break
                                        else:
                                            break
                                    if text != []:
                                        break
                                else:
                                    break
                            else:
                                break
                        else:
                            break
                    else:
                        break
                else:
                    break
                pass
            if text != []:
                t1=text[0].data.decode('utf-8')
                print(f"code: {t1}")
                print(f'type: {text[0].type}')
                print(f'quality: {text[0].quality}')
                logger_barcode.info(f'Success to read|{src_path}')
                if pathlib.Path(outputpath_used,pathlib.Path(src_path).name).exists():
                    new_name = pathlib.Path(src_path).stem+'_COPY '+time.strftime("%Y%m%d%H%M%S", time.localtime())+pathlib.Path(src_path).suffix
                    shutil.move(src_path,pathlib.Path(outputpath_used,new_name))
                else:
                    shutil.move(src_path,outputpath_used)
            else:
                text = ['Fail']
                t1 = ''
                logger_barcode.warning(f'Fail to read|{src_path}')
                shutil.copy(src_path,outputpath_fail)                     # 识别失败的另存
                if pathlib.Path(outputpath_used,pathlib.Path(src_path).name).exists():
                    new_name = pathlib.Path(src_path).stem+'_COPY'+time.strftime("%Y%m%d%H%M%S", time.localtime())+pathlib.Path(src_path).suffixes
                    shutil.move(src_path,pathlib.Path(outputpath_used,new_name))
                else:
                    shutil.move(src_path,outputpath_used)
            with open(f'{(outputpath_lot)}/{labelA}.txt','w',encoding='utf-8') as f:
                f.write(t1)
        return text,n
    
def monitor_folder(targetFilepath:pathlib.Path,*args):
    outputpath = args[0]
    observer=Observer()
    targetFileName = args[1]
    targetFilepath = pathlib.Path(targetFilepath,targetFileName)
    if observer.is_alive():
        pass
    else:
        if pathlib.Path(targetFilepath).exists():
            event_handler = WatChangeHandler(targetFilepath,observer,outputpath)
            observer.schedule(event_handler,targetFilepath,recursive=False)
            observer.start()
            logger_main.info('WAT monitor action start...')
            logger_fileCreate.info('WAT monitor action start...')
            logger_fileChange.info('WAT monitor action start...')
        else:
            logger_fileCreate.error(FileNotFoundError)
            while pathlib.Path(targetFilepath).exists() is False:
                time.sleep(2)
            else:
                event_handler = WatChangeHandler(targetFilepath,observer,outputpath)
                observer.schedule(event_handler,targetFilepath,recursive=False)
                time.sleep(0.5)
                observer.start()
                logger_main.info('TargetFile exists, program start...')
                logger_fileCreate.info('TargetFile exists, program start...')
                logger_fileChange.info('TargetFile exists, program start...')
    return observer

def getInfo():
    w = wmi.WMI()
    user = pathlib.Path.home().name
    try:
        userdetail = w.Win32_UserAccount(Name =user)[0]
    except Exception:
        user = 'DefaultAccount'
        userdetail = w.Win32_UserAccount(Name =user)[0]
    
    nic_configs = w.Win32_NetworkAdapterConfiguration(IPEnabled=True)
    if nic_configs != []:
        nic = nic_configs[0]
        MAC = nic.MACAddress
        IPV4 = nic.IPAddress[0]
        try:
            DNSHostName = nic.DNSHostName
        except Exception:
            DNSHostName = 'Non-DNSHostName'
    else:
        MAC = 'NA'
        IPV4 = 'NA'
        DNSHostName = 'Non-DNSHostName'
    return MAC,IPV4,DNSHostName,user,userdetail

def labelB_Output(outputpath):
    try:
        if pathlib.Path(outputpath).is_dir():
            pathlib.Path(outputpath).mkdir(parents=True,exist_ok=True)
            with open(outputpath+'\\'+'demo.txt',mode='w',encoding='utf-8') as f:
                f.write('')
            pathlib.Path(outputpath+'\\'+'demo.txt').unlink()
            logger_main.info('----NAS LabelB normal----')
            logger_result.info('----NAS LabelB normal----')
        else:
            raise MyExpection(f'Wrong Label B output path: {outputpath}')
    except Exception as E:
        logger_result.debug(E)
        logger_main.debug(E)
        outputpath = pathlib.Path(r'\\172.34.12.5\rwfabdata\Cassette transfer log\JXY\TEST\LabelB')
        try:
            pathlib.Path(outputpath).mkdir(parents=True,exist_ok=True)
            with open(outputpath+'\\'+'demo.txt',mode='w',encoding='utf-8') as f:
                f.write('')
            pathlib.Path(outputpath+'\\'+'demo.txt').unlink()
            logger_main.info(f'----NAS Test LabelB normal: {str(outputpath)}----')
            logger_result.info(f'----NAS Test LabelB normal: {str(outputpath)}----')
        except Exception:
            try:
                outputpath = pathlib.Path("D:\\OmniVision\\RW\\VScodeProjects\\TestData\\NeedReadBarCode\\testfile\\testResult")
                if outputpath.exists():
                    date = str(time.localtime().tm_year)+'_'+str(time.localtime().tm_mon)+'_'+str(time.localtime().tm_mday)
                    outputpath = pathlib.Path(outputpath,date)
                    pathlib.Path(outputpath).mkdir(parents=True,exist_ok=True)
                    with open(outputpath/'demo.txt',mode='w',encoding='utf-8') as f:
                        f.write('')
                    pathlib.Path(outputpath/'demo.txt').unlink()
                    pass
                else:
                    outputpath = pathlib.Path("D:\\OmniVision\\RW_WAT\\LabelB")
                    pathlib.Path(outputpath).mkdir(parents=True,exist_ok=True)
                    with open(outputpath/'demo.txt',mode='w',encoding='utf-8') as f:
                        f.write('')
                    pathlib.Path(outputpath/'demo.txt').unlink()
                logger_main.info(f'----Use local LabelB output: {str(outputpath)}----')
                logger_result.info(f'----Use local LabelB output: {str(outputpath)}----')
            except Exception as E:
                logger_result.debug(E)
                logger_main.debug(E)
                new_w = tk.Tk()
                screenWidth = new_w.winfo_screenwidth()  #获取显示区域宽度
                screenHeigh = new_w.winfo_screenheight() #获取显示区域高度
                rootwidth = 600 
                rootheight = 400
                left = (screenWidth-rootwidth)/2
                top = (screenHeigh-rootheight)/2
                new_w.geometry('%dx%d+%d+%d'%(rootwidth,rootheight,left,top))    #宽度x高度+x偏移+y偏移
                new_w.withdraw()
                while True:
                    entry=simpledialog.askstring(title='Wrong Label B output path',prompt='请输入Label B的输出路径: ',parent=new_w)
                    if entry != '' and entry != None:
                        outputpath = entry.replace('"','')
                        if pathlib.Path(outputpath).is_dir() and pathlib.Path(outputpath).exists():
                            with open(outputpath+'\\'+'demo.txt',mode='w',encoding='utf-8') as f:
                                f.write('')
                            pathlib.Path(outputpath+'\\'+'demo.txt').unlink()
                            break
                new_w.destroy()
                logger_main.info(f'----Use custom LabelB output: {str(outputpath)}----')
                logger_result.info(f'----Use custom LabelB output: {str(outputpath)}----')
    return pathlib.Path(outputpath)

def confirm_exit():
    if messagebox.askokcancel("关闭窗口","确定关闭吗？"):
        entry=simpledialog.askstring(title='口令确认：',prompt='请输入口令：')
        global salt,run
        if hash(hash(entry)+salt) == code:
            logger_fileCreate.info('WAT monitor action end by closing windows.')
            logger_result.info('WAT monitor action end by closing windows.')
            logger_barcode.info('WAT monitor action end by closing windows.')
            logger_fileChange.info('WAT monitor action end by closing windows.')
            logger_main.info('WAT monitor action end by closing windows.')
            run = False
            root.destroy()
        elif hash(entry) == hash(time.strftime("%Y%m%d%H%M",time.localtime())):
            logger_fileCreate.info('WAT monitor action end by closing windows.')
            logger_result.info('WAT monitor action end by closing windows.')
            logger_barcode.info('WAT monitor action end by closing windows.')
            logger_fileChange.info('WAT monitor action end by closing windows.')
            logger_main.info('WAT monitor action end by closing windows.')
            run = False
            root.destroy()
            pass
        else:
            messagebox.showerror('Wrong','口令错误。')
            logger_fileCreate.warning('Try to close windows.')
            logger_result.warning('Try to close windows.')
            logger_barcode.warning('Try to close windows.')
            logger_fileChange.warning('Try to close windows.')
            logger_main.warning('Try to close windows.')

class MyExpection(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

def thread_it(func,name:str,*args):
    if not repeat_thread_detection(funcN=name):
        global run,t,event
        event = threading.Event()
        run = True
        t = threading.Thread(target=func,name=name,args=args)
        t.setDaemon(True)                               # 守护线程，True: 主进程退出则退出。
        t.start()
        
def repeat_thread_detection(funcN):
    for item in threading.enumerate():
        if funcN==item.name:
            return True
    return False    

def closed_thread():
    if messagebox.askokcancel("关闭条码监控","确定关闭条码监控及识别吗？"):
        global run
        run = False
        change_button_color(button_OK)
    pass

def main():
    global run,status,root_path
    event.clear()
    status = False
    change_button_color(button_OK)
    try:
        while run:
            try:
                # 配置文件监控
                targetFilepath = r'E:\WDCM_IMG'
                if pathlib.Path(targetFilepath).exists():
                    pass
                else:
                    targetFilepath = map_path1.get().replace('"','')
                    targetFilepath = r'D:\OmniVision\RW\VScodeProjects\TestData\NeedReadBarCode\NewImage\202405-WAT1' if targetFilepath == '' or pathlib.Path(targetFilepath).exists() is False else targetFilepath
                    if pathlib.Path(targetFilepath).exists() is False:
                        raise MyExpection('Not found target monitor folder.')
                map_path1.delete(0,'end')
                map_path1.insert('0',targetFilepath)                
                # 配置LabelB result输出路径
                outputpath = map_path2.get().replace('"','')
                if outputpath == '':
                    outputpath = str(pathlib.Path(root_path,"WaferMapping","WAT Validation","Frame Label B"))
                    #outputpath = "\\\\172.34.12.5\\rwfabdata\\WaferMapping\\WAT Validation\\Frame Label B"
                outputpath = labelB_Output(outputpath)
                map_path2.delete(0,'end')
                map_path2.insert('0',outputpath)
                
                TargetFileName = str(time.localtime().tm_year)+'_'+str(time.localtime().tm_mon)#+'_'+str(time.localtime().tm_min)
                observer = monitor_folder(targetFilepath,outputpath,TargetFileName)
                logger_main.info(f'TargetFile|{targetFilepath}\{TargetFileName}')
                logger_fileCreate.info(f'TargetFile|{targetFilepath}\{TargetFileName}')
                logger_fileChange.info(f'TargetFile|{targetFilepath}\{TargetFileName}')
                
                while observer.is_alive() and run:
                    status = True
                    change_button_color(button_OK)
                    targetFolderPath = pathlib.Path(targetFilepath,TargetFileName)
                    if targetFolderPath.exists():
                        pass
                    else:
                        logger_main.info(f'TargetFolder not exist|{targetFolderPath.name}')
                        observer.stop()
                        observer.join()
                        continue
                    newTargetFileName = str(time.localtime().tm_year)+'_'+str(time.localtime().tm_mon)#+'_'+str(time.localtime().tm_min)
                    time.sleep(1)
                    if newTargetFileName == TargetFileName:
                        continue
                    else:
                        logger_main.info(f'TargetFile Changed|{TargetFileName} --> {newTargetFileName}')
                        observer.stop()
                        observer.join()
                        time.sleep(3)
                else:
                    status = False
                    observer.stop()
                    observer.join()
            except KeyboardInterrupt:
                logger_main.info('WAT monitor action was termination by KeyboardInterrupt...')
                run = False
                change_button_color(button_OK)
                break
            except MyExpection as f:
                logger_main.error(f)
                logger_main.error('Program end.')
                tk.Label(root, text = '路径无效。').pack()
                run = False
                change_button_color(button_OK)
            except Exception as Except:
                logger_main.error(Except)
                logger_main.error('Program restart.')
    except KeyboardInterrupt:
        logger_main.info('WAT monitor action was termination by KeyboardInterrupt...')
        logger_fileCreate.info('WAT monitor action was termination by KeyboardInterrupt...')
        logger_fileChange.info('WAT monitor action was termination by KeyboardInterrupt...')
    except BaseException as otherException:
        logger_fileCreate.error(otherException)
        logger_fileChange.error(otherException)
    finally:
        logger_main.info('WAT monitor action end...')
        logger_fileCreate.info('WAT monitor action end...')
        logger_fileChange.info('WAT monitor action end...')
        event.set()

def change_button_color(button):
    global run,status
    if run:
        if status:
            button['bg'] = 'green'
        else:
            button['bg'] = 'red'
    else:
        button['bg'] = 'SystemButtonFace'
    
        
# 控制台输出    https://blog.csdn.net/bigcarp/article/details/123428577
class LoggerBox(tk.Text):
    def write(self,message):
        self.insert('end',message)
        self.see(tk.END)
        self.update()

def setPassword():
    mpd_path = pathlib.Path(__file__).parent
    mpd_name = pathlib.Path(__file__).stem

    global salt,_root_path,root_path
    result = messagebox.askquestion("请选择公司: ","OSC请选择是, \nSX请选择否。")
    if result == 'yes':
        root_path = _root_path['OSC']
    else:
        root_path = _root_path['SX']
    salt = int(time.time())
    while True:
        entry=simpledialog.askstring(title='口令设置：',prompt='请输入口令(长度大于等于5位, 仅限数字、字母): ')
        if entry != None:
            x = len(entry)
            if x < 5:
                continue
            else:
                p = '^[0-9a-zA-Z]{5,%s}$' % x
                p = re.compile(p)
                if re.match(p,entry) != None:
                    code = hash(hash(entry)+salt)
                    del entry
                    """
                    with open(pathlib.Path(mpd_path,f'password_{mpd_name}.txt'),mode="w") as f:
                        f.write(str(code))
                    """
                    return code
        else:
            return None
    
def check_pid(name):
    n = 0
    for pid in psutil.process_iter():
        if pid.name() == name and pid.status()=='running':
            n += 1
            print(pid.name(),pid.status())
            if n>1:
                return pid
    return None


if __name__ == '__main__':
    _root_path = {"SX":r'\\10.162.2.50\sx_eng_data\rwfabdata',"OSC":r"\\172.34.12.5\rwfabdata"}

    PID_name = pathlib.Path(__file__).stem
    PID_name = PID_name+'.exe'
    # GUI配置
    root = tk.Tk(baseName='wwaatt')
    root.title('WAT Label B Detect')
    screenWidth = root.winfo_screenwidth()  #获取显示区域宽度
    screenHeigh = root.winfo_screenheight() #获取显示区域高度
    rootwidth = 600 
    rootheight = 400
    left = (screenWidth-rootwidth)/2
    top = (screenHeigh-rootheight)/2
    root.geometry('%dx%d+%d+%d'%(rootwidth,rootheight,left,top))    #宽度x高度+x偏移+y偏移
    #messagebox.showinfo('InfoPID_name',PID_name)
    if check_pid(PID_name) != None:
        messagebox.showerror('Wrong','程序已经在运行。')
        root.destroy()
        root.mainloop()
    else:
        fm_base1 = tk.Frame(root,height=30)
        fm_base1.pack(fill='x',expand='no')
        tk.Label(fm_base1,text = 'WAT image路径(默认不变更): ').pack(side='left',anchor='nw',expand='no')
        map_path1 = tk.Entry(fm_base1, width=50, bg='white')
        map_path1.pack(side='left',anchor='nw')
        fm_base2 = tk.Frame(root,height=30)
        fm_base2.pack(fill='x',expand='no')
        tk.Label(fm_base2,text = 'Label B输出路径(默认不变更): ').pack(side='left',anchor='nw',expand='no')
        map_path2 = tk.Entry(fm_base2, width=50, bg='white')
        map_path2.pack(side='left',anchor='nw')
        
        fm_button = tk.Frame(root,height=30)
        fm_button.pack()
        button_OK = tk.Button(fm_button, text='Start',command = lambda: thread_it(main,'WAT'),activebackground='green')
        button_OK2 = tk.Button(fm_button, text='End',command = lambda: closed_thread())
        button_OK.pack(side=tk.LEFT)
        button_OK2.pack(side=tk.LEFT)
        
        # 配置关闭程序的密码
        code = setPassword()
        if code == None:
            root.destroy()
            root.mainloop()
        else:
            #　https://blog.csdn.net/m0_53195006/article/details/128467471
            fm_t = tk.Frame(root)
            fm_t.pack(fill='both',expand='yes')
            s2 = tk.Scrollbar(fm_t)
            b2 = tk.Scrollbar(fm_t,orient='horizontal')
            s2.pack(side='right',fill='y')
            b2.pack(side='bottom',fill='x')
            """
            texts = tk.Text(fm_t,font=('Consolas',9),undo=True,autoseparators=False,wrap='none',xscrollcommand=b2.set,yscrollcommand=s2.set)
            texts.pack(fill='both',expand='yes')
            texts.insert('end','Successfully connected to window')
            s2.config(command=texts.yview)
            b2.config(command=texts.xview)"""
            
            # https://blog.csdn.net/bigcarp/article/details/123428577
            streamHandlerBox = LoggerBox(fm_t)
            streamHandlerBox.pack(fill='both',expand='yes')
            s2.config(command=streamHandlerBox.yview)
            b2.config(command=streamHandlerBox.xview)
            
            
            # 信息获取
            MAC,IPV4,DNSHostName,user,userdetail = getInfo()
            log_name = str(DNSHostName+'_'+IPV4)
            # 确定日志输出路径, 配置日志
            outputpath_log = pathlib.Path(root_path,'Cassette transfer log',"JXY",'ENG_test','log')
            #outputpath_log = pathlib.Path(r'\\172.34.12.5\rwfabdata\Cassette transfer log\JXY\TEST\log')
            filename = time.strftime("%Y%m%d",time.localtime())
            try:
                pathlib.Path(outputpath_log).mkdir(parents=True,exist_ok=True)
                with open(outputpath_log/'demo.txt',mode='w',encoding='utf-8') as f:
                    f.write('')
                pathlib.Path(outputpath_log/'demo.txt').unlink()
            except Exception as except_log_output:
                a = except_log_output
                try:
                    if pathlib.Path(r'D:\OmniVision\RW\VScodeProjects\project\debug').exists():
                        outputpath_log = pathlib.Path(r'D:\OmniVision\RW\VScodeProjects\project\debug',filename)
                    else:
                        outputpath_log = pathlib.Path("D:\\OmniVision\\RW_WAT\\LabelB Log\\")
                    pathlib.Path(outputpath_log).mkdir(parents=True,exist_ok=True)
                    with open(outputpath_log/'demo.txt',mode='w',encoding='utf-8') as f:
                        f.write('')
                    pathlib.Path(outputpath_log/'demo.txt').unlink()
                except Exception as except_log_output:
                    a2 = except_log_output
                    outputpath_log = pathlib.Path(input("Please input LabelB output folder path: ").replace('"',''))
            finally:
                # 重复的屏幕输出解决方案 https://blog.csdn.net/xuan_010/article/details/118566749

                # 配置watchDog日志 分create和change两类
                #logging.basicConfig(level=logging.NOTSET,format="%(asctime)s|%(filename)s|%(levelname)s|%(message)s",datefmt="%Y/%m/%d/%X")
                formator = logging.Formatter(fmt="%(asctime)s|%(filename)s|%(levelname)s|%(message)s")    # 日志格式器
                logger_fileCreate = logging.getLogger('FileCreate')         # 创建日志器，WAT monitor log Create
                logger_fileCreate.setLevel(logging.DEBUG)                   # Set level
                logger_fileChange = logging.getLogger('FileChange')         # 创建日志器，WAT monitor log file change
                logger_fileChange.setLevel(logging.INFO)
                logger_main = logging.Logger('main',level=logging.DEBUG)    # 创建日志器，WAT monitor log main
                
                sh = logging.StreamHandler()
                sh.setFormatter(formator)   # 给sh添加格式器
                logger_fileCreate.addHandler(sh)   # 将输出处理器添加到日志器
                logger_main.addHandler(sh)
                logger_fileChange.addHandler(sh)
                
                
                #fh = logging.FileHandler(f"{outputpath_log}\\{log_name}_WATMonitor_Create.log",encoding="utf-8")  # 写入处理器，写入内容到文件
                #fh_barcode = logging.FileHandler(f"{outputpath_log}\\{log_name}_BarcodeDetect.log",encoding="utf-8")
                #fh.setFormatter(formator)
                # logger_fileCreate.addHandler(fh)
                # handlerSize = logging.handlers.RotatingFileHandler(f"{outputpath_log}\\WATMonitor_backup.log",mode='a',maxBytes=10240000,backupCount=10)
                handlerDate = logging.handlers.TimedRotatingFileHandler(f"{outputpath_log}\\{log_name}_WATMonitor_Create.log",when='W0',backupCount=0,encoding='utf-8')
                logger_fileCreate.addHandler(handlerDate)
                handlerDate.setFormatter(formator)
                handlerDate22 = logging.handlers.TimedRotatingFileHandler(f"{outputpath_log}\\{log_name}_WATMonitor_FileChange.log",when='W0',backupCount=0,encoding='utf-8')
                logger_fileChange.addHandler(handlerDate22)
                handlerDate22.setFormatter(formator)
                handlerDate33 = logging.handlers.TimedRotatingFileHandler(f"{outputpath_log}\\{log_name}_WATMonitor_main.log",when='W0',backupCount=0,encoding='utf-8')
                logger_main.addHandler(handlerDate33)
                handlerDate33.setFormatter(formator)
                
                sh1 = logging.StreamHandler(streamHandlerBox)
                sh1.setFormatter(formator)
                logger_fileCreate.addHandler(sh1)
                logger_fileChange.addHandler(sh1)
                logger_main.addHandler(sh1)
                try:
                    logger_main.debug(f'User: {user}')
                    logger_main.debug(f'IPV4: {IPV4}')
                    logger_main.debug(f'MAC: {MAC}')
                    logger_main.debug(f'DNSHostName: {DNSHostName}')
                    logger_main.debug(f'UserInfo: {userdetail}')
                    logger_main.debug(a)
                    logger_main.debug(a)
                    del a
                    logger_main.info('----NAS Log abnormal----')
                    if 'a2' in dir():
                        logger_main.debug(a2)
                        logger_main.debug(a2)
                        del a2
                    logger_main.info(f'----Use local Log: {outputpath_log}----')
                except Exception:
                    logger_main.info('----NAS Log normal----')
                finally:
                    pass
                # 配置barcode detect日志
                logger_barcode = logging.getLogger('BarcodeDetect')
                logger_barcode.setLevel(logging.DEBUG)
                #logger_barcode.addHandler(fh_barcode)
                #fh_barcode.setFormatter(formator)
                handlerDate2 = logging.handlers.TimedRotatingFileHandler(f"{outputpath_log}\\{log_name}_BarcodeDetect.log",when='W1',backupCount=0,encoding='utf-8')
                logger_barcode.addHandler(handlerDate2)
                handlerDate2.setFormatter(formator)
                logger_barcode.addHandler(sh1)
                logger_barcode.addHandler(sh)
                
                # 配置labelB Result汇总日志
                logger_result = logging.getLogger('BarcodeResult')
                logger_result.setLevel(logging.INFO)
                handlerDate3 = logging.handlers.TimedRotatingFileHandler(f"{outputpath_log}\\{log_name}_BarcodeResult.log",when='W1',backupCount=0,encoding='utf-8')
                logger_result.addHandler(handlerDate3)
                handlerDate3.setFormatter(formator)
                logger_result.addHandler(sh1)
                logger_result.addHandler(sh)
                root.protocol("WM_DELETE_WINDOW",confirm_exit)  # 退出提示     
                root.after(800,thread_it(main,'WAT'))
            root.mainloop()
