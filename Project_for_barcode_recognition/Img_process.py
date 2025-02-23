import cv2
import pathlib
import time
import numpy as np
import math

__all__ = ['get_file',
           'preprocess_img',
           'Rotate2',
           'furprocess_img',
           'img_det',
           'check_img',
           'sharpen',
           'cv_filter2d',
           'cv_guidedFilter',
           'gray',
           'np_clip',
           'sr_models']
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

def get_file(path,pattern="*",needDir=False):
    if type(path) != pathlib.Path:
        path = pathlib.Path(path)
    if path.is_file():
        return [path]
    _files = list(pathlib.Path(path).glob(pattern))
    return _files

def calculated_polar_coordinates(src:tuple[int,int],dst:tuple[int,int]) -> tuple[int,float]:
    r = math.sqrt((dst[0]-src[0])**2 + (dst[1]-src[1])**2)
    theta = math.atan2(dst[1]-src[1],dst[0]-src[0])
    return int(r),round(theta,6)

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
    return img_box
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

def img_det(path:pathlib.Path,*args,need_CV_BarcodeDetector:bool=False,label_ns:list[int] = [1,2,3,4],**kwargs) -> dict[int,list]:
    if isinstance(need_CV_BarcodeDetector,bool) is False:
        print('The type of need_CV_BarcodeDetector must be bool.')
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
            labelB = Rotate2(img.copy(),rect,dAngle=0,hh=400,ww=70,reverse=True)    # 裁剪1次的label B
            labelB_rect = furprocess_img(labelB)
            labelB2 = Rotate2(labelB.copy(),labelB_rect,dAngle=0,hh=0,ww=0)    # 裁剪2次的label B
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