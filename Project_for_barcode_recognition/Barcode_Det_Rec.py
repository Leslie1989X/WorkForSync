import re
import cv2
import pathlib
import time
import numpy as np
import shutil
from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from opencv_superresolution import sr_img,algorithm,algoname

class MyExpection(RuntimeError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class BarcodeProcess:
    def __init__(self) -> None:
        pass
    def preprocess_img(img):
        """图片预处理，输出三个结果:\n
        第一个为drawContour后的彩图;\n
        第二个为裁剪的斜向条形码图'\n
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
        #gray_img = sr_img(gray_img,algoname[0],algorithm,scale=4)
        n = args[0] if len(args)>0 else ''
        output = args[1] if len(args)>1 else ''
        pattern = re.compile(r'^[A-Z]{2}[A-Z0-9]{5}-[A-Z0-9]{4}($|-[A-Z0-9]{2}$|-[-A-Z0-9]{4}$|-[-A-Z0-9]{4}-.{1,4}$)')    # changed
        text = pyzbar.decode(gray_img,symbols=[ZBarSymbol.CODE128,ZBarSymbol.CODE93,ZBarSymbol.CODE39])
        # TODO 后续增加CODE39的识别。
        if len(text) != 0:
            t = text[0].data.decode('utf-8')
            if re.match(pattern,t) is None or len(t) not in [12,15,17,19]:                     # changed
                print(text[0])
                text = []
            else:
                print(f'Sucess!\n-----',text[0].data.decode('utf-8'),'-----',text[0].quality,n)
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
                text = BarcodeRead.read(temp_1,n,outputpath)
                if text != []:
                    texts.append([text,n.copy()])
                    result1,result2 = BarcodeRead.checkReadResult(texts)
                    if result2 != [-1]:
                        raise MyExpection('Read Same Result')
                temp_1_2 = BarcodeProcess.cv_guidedFilter(temp_1)
                n.append(2)
                text = BarcodeRead.read(temp_1_2,n,outputpath)
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
            #logger_barcode.error(f'Wrong LabelA|{src_path}')
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
            #logger_barcode.error(except_image_process)
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
                #logger_barcode.error(f'Fail to open file|{src_path}')
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
                #logger_barcode.info(f'Success to read|{src_path}')
                if pathlib.Path(outputpath_used,pathlib.Path(src_path).name).exists():
                    new_name = pathlib.Path(src_path).stem+'_COPY '+time.strftime("%Y%m%d%H%M%S", time.localtime())+pathlib.Path(src_path).suffix
                    shutil.move(src_path,pathlib.Path(outputpath_used,new_name))
                else:
                    shutil.move(src_path,outputpath_used)
            else:
                text = ['Fail']
                t1 = ''
                #logger_barcode.warning(f'Fail to read|{src_path}')
                shutil.copy(src_path,outputpath_fail)                     # 识别失败的另存
                if pathlib.Path(outputpath_used,pathlib.Path(src_path).name).exists():
                    new_name = pathlib.Path(src_path).stem+'_COPY'+time.strftime("%Y%m%d%H%M%S", time.localtime())+pathlib.Path(src_path).suffixes
                    shutil.move(src_path,pathlib.Path(outputpath_used,new_name))
                else:
                    shutil.move(src_path,outputpath_used)
            with open(f'{(outputpath_lot)}/{labelA}.txt','w',encoding='utf-8') as f:
                f.write(t1)
        return text,n

def main(scr: str, dst: str):
    read = BarcodeRead(time.time())
    text,n = read.main(scr,dst)
    print(text,n)
    return text,n

if __name__ == '__main__':
    dst = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\Wrong_rec'
    src = r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\A348-USH982-451.jpg"
    src = input('Input the path of the image: ').replace('"','')
    main(src,dst)
