import time
import cv2
import re
import pathlib
import numpy as np
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from Barcode_detection import get_file,preprocess_img,Rotate2,furprocess_img,img_det,test_main,check_img,sharpen,cv_filter2d,cv_guidedFilter,gray,np_clip
#from Barcode_super_resolution import sr_img,algorithm,algoname

class MyExpection(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
symbols = [ZBarSymbol.CODE128,ZBarSymbol.CODE93,ZBarSymbol.CODE39]

def read(img,symbols,*args):
    n = args[0] if len(args)>0 else ''
    output = args[1] if len(args)>1 else ''
    pattern = re.compile(r'^[A-Z]{2}[A-Z0-9]{5}-[A-Z0-9]{4}($|-[A-Z0-9]{2}$|-[-A-Z0-9]{4}$|-[-A-Z0-9]{4}-.{1,4}$)')
    text = pyzbar.decode(img,symbols=symbols)
    if len(text) != 0:
        t = text[0].data.decode('utf-8')
        if re.match(pattern,t) is None or len(t) not in [12,15,17,19]:
            print(text[0])
            text = []
        else:
            print(f'Sucess!\n-----',text[0].data.decode('utf-8'),'-----',text[0].quality,n)
    else:
        text = []
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
            temp_4 = np_clip(temp_4) if dx != 0 else temp_4
            n = [dx,4]          # n为处理过程，1：锐化+双边滤波；2：锐化+导向滤波；3；灰度化；4：曝光+10%
            temp_1 = cv_filter2d(temp_4)
            n.append(1)
            text = read(temp_1,n,outputpath)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 != [-1]:
                    raise MyExpection('Read Same Result')
            temp_1_2 = cv_guidedFilter(temp_1)
            n.append(2)
            text = read(temp_1_2,n,outputpath)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 != [-1]:
                    raise MyExpection('Read Same Result')
            temp_1_2_3 = gray(temp_1_2)
            n.append(3)
            text = read(temp_1_2_3,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            temp_1_3 = gray(temp_1)
            n.pop()
            n.pop()
            n.append(3)
            del temp_1_2
            del temp_1_2_3
            text = read(temp_1_3,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            temp_1_3_2 = cv_guidedFilter(temp_1_3)
            n.append(2)
            text = read(temp_1_3_2,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            temp_1_1 = cv_filter2d(temp_1)
            n.pop()
            n.pop()
            del temp_1_3
            del temp_1_3_2
            n.append(1)                
            text = read(temp_1_1,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            temp_1_1_3 = gray(temp_1_1)
            n.append(3)                
            text = read(temp_1_1_3,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            temp_1_1_2 = cv_guidedFilter(temp_1_1)
            n.pop()
            del temp_1_1_3
            n.append(2)                
            text = read(temp_1_1_2,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            n.pop()
            n.pop()
            n.pop()
            del temp_1_1_2
            del temp_1_1
            del temp_1
            temp_2 = cv_guidedFilter(temp_4)
            n.append(2)                
            text = read(temp_2,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            temp_2_1 = cv_filter2d(temp_2)
            n.append(1)
            text = read(temp_2_1,n)
            if text != []:
                texts.append([text,n.copy()])
                result1,result2 = checkReadResult(texts)
                if result2 !=  [-1]:
                    raise MyExpection('Read Same Result')
            del temp_2
            del temp_2_1
    except MyExpection as e:
        return result1,result2
    else:
        return [],[-1]
def rec(img):
    global texts
    texts = []
    result1,result2 = multiRead(img)
    return result1
    
if __name__ == '__main__':
    filename = time.strftime('%Y_%m_%d',time.localtime())
    output_LabelB = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\imwrite\CutLabelB'+"\\"+f'{filename}'
    pathlib.Path(output_LabelB).mkdir(parents=True,exist_ok=True)
    test_folder = input('Please input the folder path: ').replace('"','')
    label = img_det(test_folder,output_LabelB = output_LabelB,need_CV_BarcodeDetector=True)
    if label:
        try:
            n = 0
            for img in label[2]:
                n += 1
                cv2.imwrite(output_LabelB+f'\\{n}.png',img)
                text = rec(img)
                print(text)
                #text = rec(sr_img(img,algoname[2],algorithm))
                #print(text)
                print('-'*40)
        except Exception as e:
            print(e)
