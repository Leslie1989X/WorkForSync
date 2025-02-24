import time
import cv2
import re
import pathlib
import numpy as np
import queue
import threading
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
#from Barcode_super_resolution import sr_img,algorithm,algoname
def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time

        print('this is wrapper')
        print(f"任务执行时间: {execution_time}秒")
        return result
    return wrapper
class MyExpection(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class CheckReadResult:
    def __init__(self):
        self.result_queue = queue.Queue()
        self._stop_flag = True
        self.__results = {}
        self.barcode_info = {}
        self.event = threading.Event()
        self.result = None
        
    def checkResult(self,time_out:int = 30,timeout:int=1,get_values:int = 3):
        n = 0
        self.event.set()
        start = time.time()
        while not self._stop_flag:
            if time.time() - start >time_out:
                self._stop_flag = True
                self.event.clear()
                if 0 < n <= get_values:
                    max_key = max(self.__results, key=self.__results.get)
                    max_value = self.__results[max_key]
                    max_count = list(self.__results.values()).count(max_value)
                    self.barcode_info[max_key].sort(key=lambda x:x[0][0].quality)
                    max_item = self.barcode_info[max_key][-1]
                    self.result = max_item
                    return max_item
                break
            try:
                text,info = self.result_queue.get(timeout=timeout)
            except queue.Empty:
                continue
            self.result_queue.task_done()
            n += 1
            try:
                label_info = text[0].data.decode('utf-8')
                quality = text[0].quality
            except Exception as e:
                continue
            if label_info not in self.__results.keys():
                self.__results[label_info] = quality
                self.barcode_info[label_info] = [(text,info)]
            else:
                self.__results[label_info] += quality
                self.barcode_info[label_info].append((text,info))
            if n > get_values:
                max_key = max(self.__results, key=self.__results.get)
                max_value = max(self.__results.values())
                max_count = list(self.__results.values()).count(max_value)
                if max_count == 1 and max_value >2:
                    self.barcode_info[max_key].sort(key=lambda x:x[0][0].quality)
                    max_item = self.barcode_info[max_key][-1]
                    self._stop_flag = True
                    self.event.clear()
                    self.result = max_item
                    return max_item
                else:
                    continue
            else:
                continue
        
                            
    def barcode_multi_read(self,img,clip:int = 6):
        temp_4 = img.copy()
        if not self.event.is_set():
                return
        for dx in range(clip):
            temp_4 = np_clip(temp_4) if dx != 0 else temp_4
            text = read(temp_4,symbols)
            self.result_queue.put((text,[dx,4])) if text else None
            if not self.event.is_set():
                break
            temp_1 = cv_filter2d(temp_4)
            text = read(temp_1,symbols)
            self.result_queue.put((text,[dx,4,1])) if text else None
            if not self.event.is_set():
                break
            temp_1_2=cv_guidedFilter(temp_1)
            text = read(temp_1_2,symbols)
            self.result_queue.put((text,[dx,4,1,2])) if text else None
            if not self.event.is_set():
                break
            temp_1_2_3 = gray(temp_1_2)
            text = read(temp_1_2_3,symbols)
            self.result_queue.put((text,[dx,4,1,2,3])) if text else None
            if not self.event.is_set():
                break
            temp_1_3 = gray(temp_1)
            text = read(temp_1_3,symbols)
            self.result_queue.put((text,[dx,4,1,3])) if text else None
            if not self.event.is_set():
                break
            temp_1_3_2 = cv_guidedFilter(temp_1_3)
            text = read(temp_1_3_2,symbols)
            self.result_queue.put((text,[dx,4,1,3,2])) if text else None
            if not self.event.is_set():
                break
            temp_1_1 = cv_filter2d(temp_1)
            text = read(temp_1_1,symbols)
            self.result_queue.put((text,[dx,4,1,1])) if text else None
            if not self.event.is_set():
                break
            temp_1_1_3 = gray(temp_1_1)
            text = read(temp_1_1_3,symbols)
            self.result_queue.put((text,[dx,4,1,1,3])) if text else None
            if not self.event.is_set():
                break
            temp_1_1_2 = cv_guidedFilter(temp_1_1)
            text = read(temp_1_1_2,symbols)
            self.result_queue.put((text,[dx,4,1,1,2])) if text else None
            if not self.event.is_set():
                break
            temp_2 = cv_guidedFilter(temp_4)
            text = read(temp_2,symbols)
            self.result_queue.put((text,[dx,4,2])) if text else None
            if not self.event.is_set():
                break
            temp_2_1 = cv_filter2d(temp_2)
            text = read(temp_2_1,symbols)
            self.result_queue.put((text,[dx,4,2,1])) if text else None
            if not self.event.is_set():
                break
    
symbols = [ZBarSymbol.CODE128,ZBarSymbol.CODE93,ZBarSymbol.CODE39]

def sharpen(img:cv2.typing.MatLike):
    src = img.copy()
    kernel = np.array([[0, -1, 0],
                    [-1, 5, -1],
                    [0, -1, 0]])
    dst = cv2.filter2D(src, -1, kernel)                                     # 锐化
    return dst
def cv_filter2d(img):
    dst = sharpen(img)
    dst = cv2.bilateralFilter(src=dst, d=0, sigmaColor=100, sigmaSpace=15)  # 双边滤波
    return dst
def cv_guidedFilter(img):
    dst = sharpen(img)
    dst = cv2.ximgproc.guidedFilter(dst, dst, 15, 12, -1)                   # 导向滤波 https://blog.csdn.net/youcans/article/details/122008763
    return dst
def gray(img):
    img_1 = img.copy()
    dst = cv2.cvtColor(img_1,cv2.COLOR_BGR2GRAY)
    return dst
def np_clip(img):
    dst = np.uint8(np.clip((1.1 * img.copy() + 10), 0, 255))
    return dst

def read(img,symbols,*args):
    n = args[0] if len(args)>0 else ''
    output = args[1] if len(args)>1 else ''
    pattern = re.compile(r'^[A-Z]{2}[A-Z0-9]{5}-[A-Z0-9]{4}($|-[A-Z0-9]{2}$|-[-A-Z0-9]{4}$|-[-A-Z0-9]{4}-.{1,4}$)')
    text = pyzbar.decode(img,symbols=symbols)
    if len(text) != 0:
        t = text[0].data.decode('utf-8')
        if re.match(pattern,t) is None or len(t) not in [12,15,17,19]:
            text = None
        else:
            #print(f"Sucess!|{t}|{text[0].quality}|{n}\n")
            return text
    else:
        text = None
    return text

def thread_it(func,name:str,*args,**kwargs):
    t = threading.Thread(target=func,name=name,args=args,kwargs=kwargs)
    t.daemon = True
    t.start()
    return t

def barcode_reader(labels:dict,label_ns: list[int] = [1, 2, 3, 4]):
    results = {}
    for label_n in label_ns:
        if label_n not in labels.keys():
            results[label_n]='Empty'
            continue
        imgs = labels[label_n]
        result = CheckReadResult()
        result._stop_flag = False
        barcode_result = thread_it(result.checkResult,'barcode_result')
        for img in imgs:
            if img is not None:
                height, width = img.shape[:2]
                center = (width/2, height/2)
                for dA in [0,1,2,-1,-2,3,-3]:
                    rotation_matrix = cv2.getRotationMatrix2D(center,dA,1.0)
                    rotated_image = cv2.warpAffine(src=img, M=rotation_matrix, dsize=(width, height))
                    barcode_read = thread_it(result.barcode_multi_read,'barcode_read',rotated_image)
        barcode_result.join()
        barcode_read.join()
        results[label_n]=result.result
    return results

if __name__ == '__main__':
    from IMG_Process import barcode_detection as img_det
    filename = time.strftime('%Y_%m_%d',time.localtime())
    output_LabelB = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\imwrite\CutLabelB'+"\\"+f'{filename}'
    pathlib.Path(output_LabelB).mkdir(parents=True,exist_ok=True)
    test_folder = input('Please input the folder path: ').replace('"','')
    label = img_det(test_folder,output_LabelB = output_LabelB,need_CV_BarcodeDetector=False)
    print(label)
    label_ns=[2]
    
    results = barcode_reader(label,label_ns)
    print(results)
    if label:
        for n in label_ns:
            num = 0
            for img in label[n]:
                try:
                    num += 1
                    cv2.imwrite(output_LabelB+f'\\{n}_{num}.png',img)
                except Exception as e:
                    continue
