import cv2
import pathlib
import time
import numpy as np
import math

from map_generation import main_gen_map
from Barcode_recognition import barcode_reader

import re
import shutil
import gc
"""
    1. 读取图片
    2. 灰度化
    3. 边缘检测
    4. 闭运算
    5. 轮廓检测
    6. 旋转矩形
    7. 旋转图片
    8. 裁剪图片
"""
__all__ = ['get_file',
           'preprocess_img',
           'Rotate2',
           'furprocess_img',
           'barcode_detection',
           'check_img',
           'sharpen',
           'cv_filter2d',
           'cv_guidedFilter',
           'gray',
           'np_clip',
           'sr_models',
           'labels',
           'DetectResult',
           'calculated_polar_coordinates',
           'calc_Hist',
           'save_hist',
           'save_maps',
           'main_img_process',
           'move_img',
           'iswaferID',
           'dice_detection',
           'img_analysis',
           'main_gen_map',
           'findSideling',
           'find_circles',]

sr_models = (r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\opencv_3rdparty\detect.prototxt", 
            r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\opencv_3rdparty\detect.caffemodel", 
            r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\opencv_3rdparty\sr.prototxt", 
            r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\opencv_3rdparty\sr.caffemodel")
# labels = {label:[(theta1,theta2,theta3,theta4,...),(distance1,distance2)]}
labels = {
    1:[(-0.3,0.2),(900,1700)],
    2:[(0.5,0.9),(900,1700)],
    3:[(1.3,1.7),(900,1700)],
    4:[(3.0,3.15,-3.15,-3.0),(900,1700)],
}

class DetectResult:
    def __init__(self):
        self.result_clasify:str = ''
        self.label:dict = {int:tuple[list,list]}
        self.circle: tuple = () # bool
        self.cnts_info: np.ndarray
        self.maps: np.ndarray # bool
        self.time:float = 0.0
        self.history:dict = {int:list[np.ndarray]}

def get_file(path,pattern="*",needDir=False):
    if type(path) != pathlib.Path:
        path = pathlib.Path(path)
    if path.is_file():
        return [path]
    _files = list(pathlib.Path(path).glob(pattern))
    return _files

def find_circles(img):
    """
    return [-1]: no found circle.\n
    return (int,int),int: (x,y),r.\n
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(7,7))
    row, col = img.shape[:2]
    img_closed = cv2.morphologyEx(img,cv2.MORPH_CLOSE,kernel)
    img = cv2.dilate(img_closed,kernel,iterations=5)
    cnts = cv2.findContours(img,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)[0]
    cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
    for i in cnts:
        if cv2.contourArea(i) < 900*900*3.14:
            return [-1]
        (x,y),r = cv2.minEnclosingCircle(i)
        if max(abs(x-col//2),abs(y-row//2)) < 300 and 900 < r < 1500:
            s = cv2.contourArea(i)
            if 1.05 > s/(math.pi*r**2) > 0.95:
                return (int(x),int(y)),int(r)
    else:
        return [-1]

def calculated_polar_coordinates(src:tuple[int,int],dst:tuple[int,int]) -> tuple[int,float]:
    r = math.sqrt((dst[0]-src[0])**2 + (dst[1]-src[1])**2)
    theta = math.atan2(dst[1]-src[1],dst[0]-src[0])
    return int(r),round(theta,6)

def calc_Hist(img,GrayHist:bool=True):
    #img = check_img(img)
    if GrayHist:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY) if len(img.shape) != 2 else img
        hist = cv2.calcHist([img],[0],None,[256],[0,256])
        return hist
    elif len(img.shape) == 3:
        hist = cv2.calcHist([img],[0],None,[256],[0,256])
        hist2 = cv2.calcHist([img],[1],None,[256],[0,256])
        hist3 = cv2.calcHist([img],[2],None,[256],[0,256])
        return hist,hist2,hist3
    
def save_hist(hist,filename):
    with open(filename,'w') as f:
        for i in hist:
            f.write(str(','.join(map(str,i)))+'\n')
            
def save_maps(maps,path):
    assert isinstance(maps,np.ndarray), 'Wrong type of maps'
    if maps.size != 0:
        mapx_ = np.where(maps == 1,'A',maps)
        mapx_ = np.where(mapx_ == '0','.',mapx_)
        with open(path,'w',encoding='utf-8') as f:
            for i in mapx_.tolist():
                f.write(''.join(i)+'\n')
    else:
        with open(path,'w',encoding='utf-8') as f:
            pass

def preprocess_img(img,width:int=70,area:int=10000):
    img1 = img.copy()
    row = img1.shape[0]
    col = img1.shape[1]
    gray1 = cv2.cvtColor(img1,cv2.COLOR_BGR2GRAY)
    ddepth = cv2.CV_32F
    print('Mean brightness: ',cv2.mean(gray1)[0])
    if cv2.mean(gray1)[0] > 127:
        gradX = cv2.Sobel(gray1,ddepth,dx=1,dy=0,ksize=3)  # ksize = -1, Sobel 算子
        gradY = cv2.Sobel(gray1,ddepth,dx=0,dy=1,ksize=3)
        gradXY = cv2.subtract(gradX,gradY)
        gradXY = cv2.convertScaleAbs(gradXY)
    else:
        gradX = cv2.Sobel(gray1,ddepth,dx=1,dy=0,ksize=-1)  # ksize = -1, Scharr 算子
        gradY = cv2.Sobel(gray1,ddepth,dx=0,dy=1,ksize=-1)
        gradXY = cv2.subtract(gradX,gradY)
        gradXY = cv2.convertScaleAbs(gradXY)
    blur = cv2.blur(gradXY,(13,13))                               # 均值滤波
    _,thresh = cv2.threshold(blur,150,255,cv2.THRESH_BINARY)    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
    kernel2 = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
    closed = cv2.morphologyEx(thresh,cv2.MORPH_CLOSE,kernel2)
    closed = cv2.erode(closed,kernel,iterations=9)
    closed = cv2.morphologyEx(closed,cv2.MORPH_OPEN,kernel2)
    closed = cv2.dilate(closed,kernel2,iterations=9)
    cnts = cv2.findContours(closed,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
    label_cnts = findSideling(cnts,row,col,width=width,area=area)
    return label_cnts
def findSideling(cnts,row,col,r:int=950,width:int=60,area:int=10000):
    """_summary_

    Args:
        cnts (_type_): _description_
        row (_type_): _description_
        col (_type_): _description_
        r (int, optional): _description_. Defaults to 950.
        width (int, optional): _description_. Defaults to 60.
        area (int, optional): _description_. Defaults to 10000.

    Returns:
        _type_: _description_
    """
    #cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
    target_rect = None
    target_cnts = []
    label_record = dict()
    for i in range(len(cnts)):
        cnt = cnts[i]
        rect = cv2.minAreaRect(cnt)
        x = rect[0][0]
        y = rect[0][1]
        angle = rect[2]
        w,h = rect[1]
        if min(w,h) < width and cv2.contourArea(cnt) < area:
            continue
        else:
            distance, theta = calculated_polar_coordinates((col//2,row//2),(x,y))
            #print('x: ',round(x,1),'y: ',round(y,1),'w: ',round(w,1),'h: ',round(h,1),'angle: ',round(angle,1))
            #print('distance: ',distance,'theta: ',theta)
            for label,values in labels.items():
                for ii in range(0,len(values[0]),2):
                    if values[0][ii] < theta < values[0][ii+1] and values[1][0] < distance < values[1][1]:
                        target_cnts.append(cnt)
                        #data_record.append([col//2,row//2,x,y,w,h,angle,distance,theta,label])
                        if label in label_record.keys():
                            tem = label_record[label]
                            if cv2.contourArea(tem) < cv2.contourArea(cnt):
                                label_record[label] = cnt
                        else:
                            label_record[label] = cnt
                        #print('Label: ',label)
                        break
                else:
                    continue
                break
            else:
                print('Not Label')
                #data_record.append([col//2,row//2,x,y,w,h,angle,distance,theta,'Not Label'])
            """if 15 < angle < 75 and x > col*0.6 and y > row*0.55:
                target_rect = rect"""
    return label_record
def Rotate2(img,rect:list,dAngle=0.0,dLength=0.0,hh = 0.0,ww = 0.0,reverse=False):
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
        angle = rect[2]+90 if reverse else rect[2]-90
    rotation_matrix = cv2.getRotationMatrix2D(rect[0],round(angle+dAngle,3),1.0)        # 旋转矩阵 angle为正，逆时针旋转；angle为负，顺时针旋转
    img_box = cv2.warpAffine(img.copy(),rotation_matrix,(img.shape[1],img.shape[0]))
    img_box = cv2.getRectSubPix(img_box,tuple(map(lambda x:int(x),(h+hh+dLength,w+ww+dLength))),tuple(map(lambda x:int(x),rect[0])))
    return img_box,rect[0],angle
def furprocess_img(img):
    """图片二次处理\n
    """
    img_g = cv2.cvtColor(img.copy(),cv2.COLOR_BGR2GRAY)
    img_2 = img.copy()
    # 自适应二值化
    bin_img = cv2.adaptiveThreshold(img_g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, -1)
    # 边缘检测
    contours, hierarchy = cv2.findContours(bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour = sorted(contours, key=cv2.contourArea,reverse=True)
    rect = cv2.minAreaRect(contour[0])  # 生成此轮廓的最小外接矩形，中心点，(宽度，高度)，倾斜度。
    return rect

def check_img(img):
    if isinstance(img,str):
        img = cv2.imread(img)
        return img
    elif isinstance(img,pathlib.Path):
        img = cv2.imread(str(img))
        return img
    elif type(img)==cv2.typing.MatLike:
        return img
    elif isinstance(img,np.ndarray):
        return img
    else:
        raise TypeError('img type is not correct.')

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
def multi_process(img):
    img = check_img(img)
    img = cv_filter2d(img)
    img = gray(img)
    img = np_clip(img)
    return img

def barcode_detection(path:pathlib.Path,*args,need_CV_BarcodeDetector:bool=False,label_ns:list[int] = [1,2,3,4],**kwargs) -> dict[int,list[np.ndarray]]:
    if isinstance(need_CV_BarcodeDetector,bool) is False:
        #print('The type of need_CV_BarcodeDetector must be bool.')
        need_CV_BarcodeDetector = False
    if isinstance(path,(str,pathlib.Path)):
        img = cv2.imread(str(path))
        if type(img) != np.ndarray:
            raise ValueError('img is incorrect.')
    if isinstance(path,np.ndarray):
        img = path
    label_cnts = preprocess_img(img)
    result = dict()
    for label_n in label_ns:
        labelB,labelB2,labelB_det,labelB2_det = None,None,None,None
        if label_n in label_cnts.keys():
            rect = cv2.minAreaRect(label_cnts[label_n])
            labelB,center,angle = Rotate2(img.copy(),rect,dAngle=0,hh=400,ww=70,reverse=True)    # 裁剪1次的label B
            labelB_rect = furprocess_img(labelB)
            labelB2,center2,angle2 = Rotate2(labelB.copy(),labelB_rect,dAngle=0,hh=0,ww=0)    # 裁剪2次的label B
            labelB,center3,angle3 = Rotate2(img.copy(),rect,dAngle=angle2,hh=400,ww=70,reverse=True)    # 修正裁剪1次的label B
            if need_CV_BarcodeDetector:
                bardet = cv2.barcode.BarcodeDetector(sr_models[2],sr_models[3])
                ok1, decoded_info1 = bardet.detect(labelB)
                ok2, decoded_info2 = bardet.detect(labelB2)
                if ok1 is True:
                    if len(decoded_info1) == 1:
                        rect1 = cv2.minAreaRect(decoded_info1)
                        labelB_det = Rotate2(labelB,rect1,dAngle=0,hh=0,ww=15,dLength=15)
                if ok2 is True:
                    if len(decoded_info2) == 1:
                        rect2 = cv2.minAreaRect(decoded_info2)
                        labelB2_det = Rotate2(labelB2,rect2,dAngle=0,hh=0,ww=0,dLength=15)
            result[label_n] = [labelB,labelB2,labelB_det,labelB2_det]
        else:
            print(f'Label {label_n} is not found.')
            continue
    else:
        return result
  
def move_img(src_path,use_output:bool=False,output:str='',need_copy:bool=False,copy_path:str='',suffix:list=['bmp','BMP']):
    if use_output:
        outputpath_used = output
    else:
        outputpath_used = pathlib.Path(pathlib.Path(src_path).parent,'Used')
    pathlib.Path(outputpath_used).mkdir(parents=True,exist_ok=True)
    __new_name = pathlib.Path(src_path).stem+'_COPY_'+time.strftime("%Y%m%d%H%M%S", time.localtime())
    if pathlib.Path(src_path).suffix in suffix or '_BW' in pathlib.Path(src_path).stem:
        if need_copy:
            if pathlib.Path(copy_path,pathlib.Path(src_path).name).exists():
                cv2.imwrite(pathlib.Path(copy_path,__new_name+'.jpeg'),cv2.imread(src_path))
            else:
                cv2.imwrite(pathlib.Path(copy_path,pathlib.Path(src_path).stem+'.jpeg'),cv2.imread(src_path))
        if pathlib.Path(outputpath_used,pathlib.Path(src_path).stem+'.jpeg').exists():
            new_name = __new_name+'.jpeg'
        else:
            new_name = pathlib.Path(src_path).stem+'.jpeg'
        cv2.imwrite(pathlib.Path(outputpath_used,new_name),cv2.imread(src_path))
        pathlib.Path(src_path).unlink()
        return
    
    if need_copy:
        if pathlib.Path(copy_path,pathlib.Path(src_path).name).exists():
            shutil.copy(src_path,pathlib.Path(copy_path,__new_name+pathlib.Path(src_path).suffix))
        else:
            shutil.copy(src_path,pathlib.Path(copy_path,pathlib.Path(src_path).name))
    if pathlib.Path(outputpath_used,pathlib.Path(src_path).name).exists():
        shutil.move(src_path,pathlib.Path(outputpath_used,__new_name+pathlib.Path(src_path).suffix))
    else:
        shutil.move(src_path,outputpath_used)
    return

def __img_process(img:np.ndarray,option:int=1):
    blur = cv2.GaussianBlur(img,(9,9),0)
    th3 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, option,11, 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    th3_open = cv2.morphologyEx(th3,cv2.MORPH_OPEN,kernel)
    return th3_open

def dice_detection(img:cv2.typing.MatLike):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    if len(img.shape) != 2:
        raise ValueError('The shape of img is not correct.')
    blur = cv2.GaussianBlur(img,(5,5),0)
    _,thresh = cv2.threshold(blur,50,255,cv2.THRESH_BINARY_INV)
    cir = find_circles(thresh)
    if isinstance(cir,tuple):
        mask = np.zeros_like(thresh,dtype=np.uint8)
        cv2.circle(mask,(cir[0][0],cir[0][1]),cir[1]-5,255,-1)
        thresh2 = cv2.bitwise_and(cv2.bitwise_or(__img_process(img),thresh),mask)
        #_thresh1 = cv2.bitwise_or(thresh1,mask)
    else:
        return cir,[]
    cnts,hierarchy = cv2.findContours(thresh2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts_o,cnts_i,areas_o,rects_o,areas_i,rects_i  = [],[],[],[],[],[]
    del mask,blur,thresh,thresh2,img
    if len(cnts) == 0:
        return cir,np.empty((0,6),dtype=np.float32)
    rects_o = np.array([[rect[0][0],rect[0][1],rect[1][0],rect[1][1],rect[2]] for rect in map(cv2.minAreaRect,cnts)],dtype = np.float32)
    areas_o = np.array(list(map(cv2.contourArea,cnts)),dtype=np.float32)
    # TODO 计算每个轮廓的灰度是个后续判定的方案，可惜目前做不到很快
    contours_info = np.column_stack((rects_o,areas_o))
    del rects_o,areas_o
    _rects_o = contours_info[:,4] > 45
    contours_info[_rects_o,4] -= 90
    contours_info = np.hstack([contours_info[:,0:2],
               np.where(_rects_o,contours_info[:,3],contours_info[:,2]).reshape(-1,1),
               np.where(_rects_o,contours_info[:,2],contours_info[:,3]).reshape(-1,1),
               contours_info[:,4:]])
    """if len(cnts_i) == 0:
        pass
    else:
        areas_i = np.array([cv2.contourArea(cnts[contour]) for contour in cnts_i])
        rects_i = [cv2.minAreaRect(cnts[contour]) for contour in cnts_i]
        rects_i = np.array([[rect[0][0],rect[0][1],rect[1][0],rect[1][1],rect[2]] for rect in rects_i],dtype = np.float16)
        _rects_i = rects_i[:,2] < rects_i[:,3]
        rects_i[_rects_i,4] -= 90"""    
    return cir,contours_info

def img_analysis(img_,threshold1: float = 0.3,threshold2: float = 0.09,label_ns:list[int] = [1,2,3,4],img_path:str=''):
    if isinstance(img_,(str,pathlib.Path)):
        img = cv2.imread(img_)
        if type(img) != np.ndarray:
            raise ValueError('img is incorrect.')
    elif isinstance(img_,np.ndarray):
        img = img_
    result = DetectResult()
    hist = calc_Hist(img,GrayHist=True)
    #cal1,cal2 = np.sum(hist[:16])/np.sum(hist),np.sum(hist[-16:])/np.sum(hist)
    #if cal1 > threshold1 and cal2 > threshold2 or cal1-threshold1-threshold2>0 or '_BW' in pathlib.Path(img_path).stem:
    if '_BW' in pathlib.Path(img_path).stem:    # 图片整体灰暗的情况下不能通过直方分布准确判断是否为背光图片。
        result.result_clasify = 'backlight'
        cir,contours_info = dice_detection(img)
        del img
        gc.collect()
        if isinstance(cir,list):
            result.circle = False
            return result
        else:
            result.circle = cir
        if isinstance(contours_info,np.ndarray):
            result.cnts_info = contours_info
            try:
                mapx,mapy = main_gen_map(contours_info)
            except AssertionError as a:
                print(f"AssertionError: {a}")
                mapx,mapy = 0,0
            except Exception as e:
                print(f"Exception: {e}")
                mapx,mapy = 0,0
            finally:
                if isinstance(mapx,np.ndarray) and np.all(mapx == mapy):
                    result.maps = mapx
                    return result
                else:
                    result.maps = False
                    return result
        else:
            result.cnts_info = contours_info
            result.maps = False
            return result # 不会触发，没有检测到cnts，会返回numpy.empty供map生成空。
    else:
        result.result_clasify = 'frontlight'
        labelAB = barcode_detection(img,label_ns=label_ns)
        result.label = barcode_reader(labelAB,label_ns)
        result.history = labelAB
        #result.label = {key: value[0] for key, value in results.items()}
        #result.approach = {key: value[1] for key, value in results.items()}
        return result

def iswaferID(waferID: str):
    lens = len(waferID)
    if lens >12:
        iswaferID = False
    elif lens == 12 or lens == 11:
        waferID = waferID[:-2].rjust(10,' ')+waferID[-2:]
        waferIDList = list(waferID)
        sum = 0
        for i in range(10):
            sum += (ord(waferIDList[i])-32)*(8**(11-i))
        sum += (ord('A')-32)*(8**(1))
        sum += (ord('0')-32)*(8**(0))
        m = sum % 59
        if m == 0:
            if waferID[-2:] == 'A0':
                iswaferID = True
            else:
                iswaferID = False
        else:
            sub = 59-m
            strsub = bin(int(sub))[2:].rjust(6,'0')
            pre = int(strsub[:3],2)
            last = int(strsub[3:],2)
            c1 = chr(ord('A')+pre)
            c2 = chr(ord('0')+last)
            if chr(ord('A')+pre)+chr(ord('0')+last) == waferID[-2:]:
                iswaferID = True
            else:
                iswaferID = False
    else:
        iswaferID = False
    return iswaferID

def main_img_process(path:str,label_ns:list[int] = [1,2,3,4],suffix:list=['bmp','BMP'],output_label:str='',output_maps:str='',outputpath_history:str='', **kwargs):
    labelA = pathlib.Path(path).stem.strip()
    save_history = kwargs['save_history'] if 'save_history' in kwargs.keys() else True
    try:
        lotID = re.search(re.compile(r'-[^-]+-'),labelA).group().replace('-','')
    except Exception as LabelAError:
        lotID = labelA
    finally:
        if iswaferID(pathlib.Path(path).stem) or iswaferID(pathlib.Path(path).stem.replace('_BW','')):
            outputpath_wafer = pathlib.Path(pathlib.Path(path).parent,'wafer')
            pathlib.Path(outputpath_wafer).mkdir(parents=True,exist_ok=True)
            detect_time = time.time()
            while round(time.time()-detect_time,2) < 5:
                try:
                    img = cv2.imread(path)
                    assert isinstance(img,np.ndarray)
                except AssertionError as a:
                    time.sleep(0.5)
                    continue
                else:
                    del img
                    break
            else:
                raise TimeoutError(f'Fail to open file|{path}')
            move_img(path,use_output=True,output=outputpath_wafer,suffix=suffix)
            result = DetectResult()
            result.result_clasify = '12Inch'
            return result,'12 inch'
        else:
            detect_time = time.time()
            while round(time.time()-detect_time,2) < 3:
                try:
                    img = cv2.imread(path)
                    assert isinstance(img,np.ndarray)
                except AssertionError as a:
                    time.sleep(0.5)
                    continue
                else:
                    break
            else:
                raise TimeoutError(f'Fail to open file|{path}')
            result = img_analysis(img,label_ns = label_ns,img_path=path)
            
            if result.result_clasify == 'backlight':
                pathlib.Path(output_maps,lotID).mkdir(parents=True,exist_ok=True)
                if isinstance(result.circle,bool):
                    pathlib.Path(output_maps,'fail',time.strftime("%Y%m%d", time.localtime())).mkdir(parents=True,exist_ok=True)
                    move_img(path,use_output=False,suffix=suffix,need_copy=True,copy_path=str(pathlib.Path(output_maps,'fail',time.strftime("%Y%m%d", time.localtime()))))
                    return result,"no found circle."
                if isinstance(result.maps,bool):
                    pathlib.Path(output_maps,'fail',time.strftime("%Y%m%d", time.localtime())).mkdir(parents=True,exist_ok=True)
                    move_img(path,use_output=False,suffix=suffix,need_copy=True,copy_path=str(pathlib.Path(output_maps,'fail',time.strftime("%Y%m%d", time.localtime()))))
                    if save_history:
                        pathlib.Path(outputpath_history,lotID).mkdir(parents=True,exist_ok=True)
                        np.save(pathlib.Path(outputpath_history,lotID,pathlib.Path(path).stem+'.npy'),result.cnts_info)
                        with open(pathlib.Path(outputpath_history,lotID,pathlib.Path(path).stem+'.ini'),'w',encoding = 'utf-8') as f:
                            f.write(f'x = {result.circle[0][0]}\n')
                            f.write(f'y = {result.circle[0][1]}\n')
                            f.write(f'r = {result.circle[1]}\n')
                    return result,"fail to generate map."
                if isinstance(result.cnts_info,np.ndarray):
                    save_maps(result.maps,str(pathlib.Path(output_maps,lotID,pathlib.Path(path).stem.replace('_BW','')+'.txt')))
                    move_img(path,use_output=False,suffix=suffix)
                    if save_history:
                        pathlib.Path(outputpath_history,lotID).mkdir(parents=True,exist_ok=True)
                        np.save(pathlib.Path(outputpath_history,lotID,pathlib.Path(path).stem+'.npy'),result.cnts_info)
                        with open(pathlib.Path(outputpath_history,lotID,pathlib.Path(path).stem+'.ini'),'w',encoding = 'utf-8') as f:
                            f.write(f'x = {result.circle[0][0]}\n')
                            f.write(f'y = {result.circle[0][1]}\n')
                            f.write(f'r = {result.circle[1]}\n')
                    return result,"success to generate map."
            if result.result_clasify == 'frontlight':
                pathlib.Path(output_label,lotID).mkdir(parents=True,exist_ok=True)
                if len(label_ns) == 1:
                    for n in label_ns:
                        if n not in result.label.keys():
                            continue
                        if result.label[n] == 'Empty':
                            return result,"Empty."
                        if result.label[n] is not None:
                            with open(f'{pathlib.Path(output_label,lotID)}/{labelA}.txt','w',encoding='utf-8') as f:
                                f.write(result.label[n][0][0].data.decode('utf-8'))
                            move_img(path,use_output=False,suffix=suffix)
                            return result,"Success to read Barcode."
                        else:
                            with open(f'{pathlib.Path(output_label,lotID)}/{labelA}.txt','w',encoding='utf-8') as f:
                                f.write('')
                            pathlib.Path(output_label,'fail',time.strftime("%Y%m%d", time.localtime())).mkdir(parents=True,exist_ok=True)
                            move_img(path,use_output=False,suffix=suffix,need_copy=True,copy_path=str(pathlib.Path(output_label,'fail',time.strftime("%Y%m%d", time.localtime()))))
                            if save_history:
                                pathlib.Path(outputpath_history,lotID).mkdir(parents=True,exist_ok=True)
                                result.history[n][0]
                                cv2.imwrite(pathlib.Path(outputpath_history,lotID,pathlib.Path(path).stem+'.bmp'),result.history[n][0])
                                cv2.imwrite(pathlib.Path(outputpath_history,lotID,pathlib.Path(path).stem+'_small.bmp'),result.history[n][1])
                            return result,"Fail to read Barcode."
