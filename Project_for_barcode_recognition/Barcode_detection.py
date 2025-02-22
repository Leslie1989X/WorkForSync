import cv2
import pathlib
import time
import numpy as np
import math
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
    row = img.shape[0]
    col = img.shape[1]  
    img_canny = cv2.Canny(img,70,100)
    cnts = cv2.findContours(img_canny,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)[0]
    cnts = sorted(cnts,key=cv2.contourArea,reverse=True)
    for i in cnts:
        (x,y),r = cv2.minEnclosingCircle(i)
        if max(abs(x-col//2),abs(y-row//2)) < 300 and 900 < r < 1400:
            s = cv2.contourArea(i)
            if 1.05 > s/(math.pi*r**2) > 0.95:
                return (int(x),int(y)),int(r)
    else:
        return [-1]
        
def find_circle(img):
    row = img.shape[0]
    col = img.shape[1]    
    x180_h = cv2.HoughCircles(img,cv2.HOUGH_GRADIENT,1,minDist = 15,param1 = 220,param2 = 140,minRadius = 900,maxRadius= 1400)
    for i in x180_h[0]:
        x,y,r = int(i[0]),int(i[1]),int(i[2])
        if max(abs(x-col//2),abs(y-row//2)) < 100 and 900 < r < 1400:
            return x,y,r
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

def img_det(path:pathlib.Path,*args,need_CV_BarcodeDetector:bool=True,label_ns:list[int] = [1,2,3,4],**kwargs) -> dict[int,list]:
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

def test_main(test_folder:str,*args,need_imwrite:bool=True,**kwargs):
    if type(test_folder) != str:
        raise TypeError('The type of test_folder must be str.')
    output_LabelB = kwargs['output_LabelB'] if 'output_LabelB' in kwargs else None
    tem = get_file(test_folder,pattern='*.jpg')
    filename = time.strftime('%Y_%m_%d',time.localtime())
    if isinstance(need_imwrite,bool) is False:
        print('The type of need_imwrite must be bool.')
        need_imwrite = True
    for i in tem:
        output_LabelB_i = pathlib.Path(output_LabelB,filename).joinpath(i.stem)
        output_LabelB_i.mkdir(parents=True,exist_ok=True)
        labelBs = img_det(i)
        if need_imwrite:
            if not labelBs:
                continue
            if output_LabelB is not None:
                for index,lists in labelBs.items():
                    for index2,j in enumerate(lists):
                        if j is not None:
                            cv2.imwrite(f'{output_LabelB_i}/{i.stem}_label_{index}_{index2}.jpg',j)
            else:
                for index,lists in labelBs.items():
                    for index2,j in enumerate(lists):
                        if j is not None:
                            cv2.imwrite(f'{output_LabelB_i}/{i.stem}_label_{index}_{index2}.jpg',j)
        else:
            return labelBs

        
if __name__ == '__main__':
    output_folder = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\imwrite\findContours'
    output_folder2 = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\imwrite\NoLabelB'
    output_closed = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\imwrite\closed'
    output_LabelB = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\imwrite\CutLabelB'
    output_hists = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\IMG_Black_Normal'
    data_record = [['Center_x','Center_y','x','y','w','h','Angle','Distance','Theta','Label']]
    pathlib.Path(output_folder).mkdir(parents=True,exist_ok=True)
    pathlib.Path(output_folder2).mkdir(parents=True,exist_ok=True)
    pathlib.Path(output_closed).mkdir(parents=True,exist_ok=True)
    pathlib.Path(output_LabelB).mkdir(parents=True,exist_ok=True)
    test_folder = input('Please input the folder path: ').replace('"','')
    a = input('Please input num: ').replace('"','')
    start = time.time()
    if a == '1':
        test_main(test_folder,output_LabelB=output_LabelB)
    print('Time: ',round(time.time()-start,4),'s')
