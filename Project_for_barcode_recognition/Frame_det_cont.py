import cv2
import pathlib
import time
import numpy as np
import math
from map_generation import main_gen_map,split_sort,cal_box
import concurrent.futures
from Barcode_detection import get_file,img_det
import gc

__all__ = ['find_circles','calc_Hist','save_hist','save_maps','img_process','dice_det','dice_det_main','cal_gray']

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

def calc_Hist(img:np.ndarray,GrayHist:bool=True):
    if GrayHist or len(img.shape) == 2:
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

def blob_det(img):
    params = cv2.SimpleBlobDetector.Params()
    params.filterByColor = True         # 过滤颜色
    params.blobColor = 255
    params.filterByArea = True          # 过滤面积
    params.minArea = 100
    params.maxArea = 1000000
    params.filterByCircularity = False   # 过滤圆度
    params.minCircularity = 0.8
    params.filterByConvexity = False     # 过滤凸度
    params.minConvexity = 0.8
    params.filterByInertia = False       # 过滤惯性
    params.minInertiaRatio = 0.8
    detector = cv2.SimpleBlobDetector.create(params)
    if len(img.shape) == 3:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    if len(img.shape) == 2:
        blur = cv2.GaussianBlur(img,(5,5),0)
        _,thresh = cv2.threshold(blur,50,255,cv2.THRESH_BINARY)
    else:
        raise ValueError('The shape of img is not correct.')
    tem = find_circles(thresh)
    if tem != [-1]:
        mask = np.zeros_like(thresh,dtype=np.uint8)
        cv2.circle(mask,(tem[0][0],tem[0][1]),tem[1]-10,255,-1)
        mask = cv2.bitwise_not(mask)
        thresh = cv2.bitwise_or(thresh,mask)
        thresh = cv2.bitwise_not(thresh)
    keypoints = detector.detect(thresh)
    if len(keypoints) < 0:
        for j in keypoints:
            x,y = j.pt
            d = j.size
            x_min = max(0,int(x-d))
            x_max = min(img.shape[1],int(x+d))
            y_min = max(0,int(y-d))
            y_max = min(img.shape[0],int(y+d))
            img_blob = thresh[y_min:y_max,x_min:x_max]
            cnts = cv2.findContours(img_blob,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[0]
            rect = cv2.minAreaRect(cnts[0])
    return keypoints,tem

def img_process(img:np.ndarray,option:int=1):
    blur = cv2.GaussianBlur(img,(9,9),0)
    th3 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, option,11, 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    th3_open = cv2.morphologyEx(th3,cv2.MORPH_OPEN,kernel)
    return th3_open

def cal_gray(contour):
    pass

def dice_det(img:cv2.typing.MatLike):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    if len(img.shape) != 2:
        raise ValueError('The shape of img is not correct.')
    blur = cv2.GaussianBlur(img,(5,5),0)
    _,thresh = cv2.threshold(blur,50,255,cv2.THRESH_BINARY_INV)
    cir = find_circles(thresh)
    if isinstance(cir,tuple):
        mask = np.zeros_like(thresh,dtype=np.uint8)
        cv2.circle(mask,(cir[0][0],cir[0][1]),cir[1]-5,255,-1)
        thresh2 = cv2.bitwise_and(cv2.bitwise_or(img_process(img),thresh),mask)
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

def dice_det_main(img_path,threshold1: float = 0.3,threshold2: float = 0.09,label_ns:list[int] = [1,2,3,4]):
    if isinstance(img_path,(str,pathlib.Path)):
        img = cv2.imread(img_path)
        if type(img) != np.ndarray:
            raise ValueError('img is incorrect.')
    elif isinstance(img_path,np.ndarray):
        img = img_path
    hist = calc_Hist(img,GrayHist=True)
    cal1,cal2 = np.sum(hist[:16])/np.sum(hist),np.sum(hist[-16:])/np.sum(hist)
    if cal1 > threshold1 and cal2 > threshold2 or cal1-threshold1-threshold2>0:
        cir,contours_info = dice_det(img)
        del img
        gc.collect()
        if isinstance(cir,list):
            return -1
        elif isinstance(contours_info,np.ndarray):
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
                    return cir,contours_info,mapx
                else:
                    return cir,contours_info,0
        else:
            return cir,contours_info,[]
    else:
        labelAB = img_det(img,label_ns=label_ns)
        return labelAB

def test_main_hist(test_folder,*args, pattern='*.jpg',**kwargs):
    tem = get_file(test_folder,pattern)
    output = kwargs['output'] if 'output' in kwargs else None
    hists = np.empty((256,0))
    names = []
    filename = time.strftime('%Y_%m_%d',time.localtime())
    output_n = pathlib.Path(output,'Blobs',filename,'success')
    output_n.mkdir(parents=True,exist_ok=True)
    output_fail = pathlib.Path(output,'Blobs',filename,'fail')
    output_fail.mkdir(parents=True,exist_ok=True)
    
    for i in tem:
        #cir,(contours_info,areas_i,rects_i) = main(i)
        img = cv2.imread(i)
        hist = calc_Hist(img,GrayHist=True)
        hists = np.hstack((hists,hist))
        names.append(i.stem)
        cal1,cal2 = np.sum(hist[:16])/np.sum(hist),np.sum(hist[-16:])/np.sum(hist)
        print(f"DF: {cal1},BF: {cal2}")
        if cal1 > 0.3 and cal2 > 0.09 or cal1 > 0.45:
            print(i.stem,' is backlighting photo.')
            cir,contours_info = dice_det(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY))
            print('rects: ',len(contours_info))
            if cir == [-1]:
                print(i.name,'----------')
                cv2.imwrite(f'{output_fail}/{i.stem}_cir.jpg',img)
                continue
            tem_blob = cv2.circle(img.copy(),(cir[0][0],cir[0][1]),cir[1],(0,0,255),2) if cir != [-1] else img.copy()
            tem_blob = cv2.circle(tem_blob,(cir[0][0],cir[0][1]),cir[1]-5,(0,0,255),2) if cir != [-1] else img.copy()
            if len(contours_info)>0:
                for rect in contours_info: cv2.drawContours(tem_blob,[np.intp(cv2.boxPoints([(rect[0],rect[1]),(rect[2],rect[3]),rect[4]]))],-1,(100,155,1),2)
                for rect in contours_info: cv2.circle(tem_blob,(int(rect[0]),int(rect[1])),int(rect[3]/5),(100,155,1),2)
                try:
                    mapx,mapy = main_gen_map(contours_info)
                except AssertionError as a:
                    print(a)
                    mapx,mapy = None,None
                except Exception as a:
                    print(a)
                    mapx,mapy = None,None
                if np.all(mapx == mapy) and isinstance(mapx,np.ndarray):
                    print('The same map.')
                    cv2.imwrite(f'{output_n}/{i.stem}_dice.jpg',tem_blob)
                    np.save(f'{output_n}/{i.stem}_info.npy',contours_info)
                    save_maps(mapx,f'{output_n}/{i.stem}_map.txt')
                else:
                    cv2.imwrite(f'{output_fail}/{i.stem}_dice.jpg',tem_blob)
                    np.save(f'{output_fail}/{i.stem}_info.npy',contours_info)
                    print('The different map.')
                    if isinstance(mapx,np.ndarray):
                        save_maps(mapx,f'{output_n}/{i.stem}_mapx.txt')
                    if isinstance(mapy,np.ndarray):
                        save_maps(mapy,f'{output_n}/{i.stem}_mapy.txt')
            print(f'{i.stem}_____end.')
            """
            keypoints,cir = blob_det(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY))
            print('keypoints: ',len(keypoints))
            tem_blob = cv2.drawKeypoints(img.copy(),keypoints,None,(0,255,0),cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            tem_blob = cv2.drawKeypoints(tem_blob,keypoints,None,(0,255,0),cv2.DRAW_MATCHES_FLAGS_DEFAULT)
            tem_blob = cv2.circle(tem_blob,(cir[0][0],cir[0][1]),cir[1],(0,0,255),5)
            cv2.imwrite(f'{output}/Blobs/{filename}/{i.stem}_blob.jpg',tem_blob)
            """
        else:
            print(i.stem,' is frontlighting photo.')
            # TODO process frontlighting photo
    if output is not None:
        save_hist(hists,f'{output_n}/hists.txt')
        with open(f'{output_n}/hists_columns.txt','w') as f:
            f.write(str(','.join(map(str,names)))+'\n')
    else:
        save_hist(hists,'hists.txt')
        with open(f'hists_columns.txt','w') as f:
            f.write(str(','.join(map(str,names)))+'\n')

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
    start = time.time()
    test_main_hist(test_folder,output=output_hists,pattern='*.bmp')
    #test_main(test_folder,output_LabelB=output_LabelB)
    #test_main_hist(test_folder,output=output_hists)
    #with open(f'{output_LabelB}/{pathlib.Path(test_folder).stem}_data_record.csv','w') as f:
    #    for i in data_record:
    #        f.write(','.join(map(str,i))+'\n')
    print('Time: ',round(time.time()-start,4),'s')
