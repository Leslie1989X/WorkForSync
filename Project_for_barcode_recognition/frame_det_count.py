import cv2
import pathlib
import time
import numpy as np
import math


def get_file(path,pattern="*",needDir=False):
    if type(path) != pathlib.Path:
        path = pathlib.Path(path)
    if path.is_file():
        return [path]
    _files = list(pathlib.Path(path).glob(pattern))
    return _files

def find_circles(img):
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(7,7))
    
    row = img.shape[0]
    col = img.shape[1]
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

def img_process(img,option:int=1):
    cv2.THRESH_BINARY_INV
    cv2.THRESH_BINARY
    blur = cv2.GaussianBlur(img,(9,9),0)
    th3 = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, option,11, 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    th3_open = cv2.morphologyEx(th3,cv2.MORPH_OPEN,kernel)
    return th3_open

def dice_det(img:cv2.typing.MatLike):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    if len(img.shape) == 2:
        blur = cv2.GaussianBlur(img,(5,5),0)
        _,thresh = cv2.threshold(blur,50,255,cv2.THRESH_BINARY_INV)
        #_thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,11,3)
    else:
        raise ValueError('The shape of img is not correct.')
    cir = find_circles(thresh)
    if cir != [-1]:
        mask = np.zeros_like(thresh,dtype=np.uint8)
        cv2.circle(mask,(cir[0][0],cir[0][1]),cir[1]-10,255,-1)
        thresh2 = cv2.bitwise_and(cv2.bitwise_or(img_process(img),thresh),mask)
        #_thresh1 = cv2.bitwise_or(thresh1,mask)
    else:
        return cir,([],[],[],[])
    cnts,hierarchy = cv2.findContours(thresh2,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts_o,cnts_i,areas_o,rects_o,areas_i,rects_i  = [],[],[],[],[],[]
    if len(cnts) == 0:
        return cir,(cnts_o,areas_i,rects_i)
    """
    for index, j in enumerate(hierarchy[0]):
        if j[2] != -1 or j[2] == j[3] == -1:
            cnts_o.append(index)
        else:
            cnts_i.append(index)
    """
    rects_o = np.array([[rect[0][0],rect[0][1],rect[1][0],rect[1][1],rect[2]] for rect in map(cv2.minAreaRect,cnts)],dtype = np.float32)
    areas_o = np.array(list(map(cv2.contourArea,cnts)),dtype=np.float32)
    contours_info = np.column_stack((rects_o,areas_o))
    del rects_o,areas_o
    """
    _rects_o = rects_o[:,2] < rects_o[:,3]
    rects_o[_rects_o,4] -= 90
    rects_o = np.hstack([rects_o[:,0:2],
               np.where(_rects_o,rects_o[:,3],rects_o[:,2]).reshape(-1,1),
               np.where(_rects_o,rects_o[:,2],rects_o[:,3]).reshape(-1,1),
               rects_o[:,4:]])
    """
    _rects_o = contours_info[:,4] > 45
    contours_info[_rects_o,4] -= 90
    contours_info = np.hstack([contours_info[:,0:2],
               np.where(_rects_o,contours_info[:,3],contours_info[:,2]).reshape(-1,1),
               np.where(_rects_o,contours_info[:,2],contours_info[:,3]).reshape(-1,1),
               contours_info[:,4:]])
    angles = contours_info[np.where((contours_info[:,4] != 0) & (contours_info[:,4] != 90)),4]
    std_angle = np.std(np.delete(angles,[np.argmax(angles),np.argmin(angles)])) if angles.size >2 else 0
    avg_angle = np.mean(np.delete(angles,[np.argmax(angles),np.argmin(angles)])) if angles.size >2 else 0
    print('STD_angle: ',std_angle,'AVG_angle: ',avg_angle)
    o_x = contours_info[np.lexsort((contours_info[:,1],contours_info[:,0]))]
    o_y = contours_info[np.lexsort((contours_info[:,0],contours_info[:,1]))]
    o_x_x = np.diff(o_x[:,0])
    o_x_y = np.diff(o_x[:,1])
    #theta = np.degrees(np.atan2(-np.sum(np.diff(rects_o[:,0])[:3]),np.sum(np.diff(rects_o[:,1])[:3])))
    #h = np.mean(rects_o[:,3])
    #w = np.mean(rects_o[:,2])
    #np.where((np.diff(rects_o[:,0])>w*0.2))[0]+1
    if len(cnts_i) == 0:
        pass
    else:
        areas_i = np.array([cv2.contourArea(cnts[contour]) for contour in cnts_i])
        rects_i = [cv2.minAreaRect(cnts[contour]) for contour in cnts_i]
        rects_i = np.array([[rect[0][0],rect[0][1],rect[1][0],rect[1][1],rect[2]] for rect in rects_i],dtype = np.float16)
        _rects_i = rects_i[:,2] < rects_i[:,3]
        rects_i[_rects_i,4] -= 90    
    return cir,(contours_info,areas_i,rects_i)

def main(img_path,threshold1: float = 0.3,threshold2: float = 0.09):
    img = cv2.imread(img_path)
    hist = calc_Hist(img,GrayHist=True)
    cal1,cal2 = np.sum(hist[:16])/np.sum(hist),np.sum(hist[-16:])/np.sum(hist)
    if cal1 > threshold1 and cal2 > threshold2 or cal1-threshold1-threshold2>0:
        cir,(contours_info,areas_i,rects_i) = dice_det(img)
        return cir,(contours_info,areas_i,rects_i)
    else:
        return 0

def test_main_hist(test_folder,*args, **kwargs):
    tem = get_file(test_folder,pattern='*.jpg')
    output = kwargs['output'] if 'output' in kwargs else None
    hists = np.empty((256,0))
    names = []
    filename = time.strftime('%Y_%m_%d',time.localtime())
    pathlib.Path(output,'Blobs',filename).mkdir(parents=True,exist_ok=True)
    for i in tem:
        #cir,(areas_o,rects_o,areas_i,rects_i) = main(i)
        img = cv2.imread(i)
        hist = calc_Hist(img,GrayHist=True)
        hists = np.hstack((hists,hist))
        names.append(i.stem)
        cal1,cal2 = np.sum(hist[:16])/np.sum(hist),np.sum(hist[-16:])/np.sum(hist)
        print(cal1,cal2)
        if cal1 > 0.3 and cal2 > 0.09 or cal1 > 0.45:
            print(i.stem,' is backlighting photo.')
            cir,(contours_info,areas_i,rects_i) = dice_det(cv2.cvtColor(img,cv2.COLOR_BGR2GRAY))
            print('rects: ',len(contours_info))
            if cir == [-1]:
                print(i.name,'----------')
                continue
            tem_blob = cv2.circle(img.copy(),(cir[0][0],cir[0][1]),cir[1],(0,0,255),2) if cir != [-1] else img.copy()
            tem_blob = cv2.circle(tem_blob,(cir[0][0],cir[0][1]),cir[1]-10,(0,0,255),2) if cir != [-1] else img.copy()
            if len(contours_info)>0:
                for rect in contours_info: cv2.drawContours(tem_blob,[np.intp(cv2.boxPoints([(rect[0],rect[1]),(rect[2],rect[3]),rect[4]]))],-1,(100,155,1),2)
                for rect in contours_info: cv2.circle(tem_blob,(int(rect[0]),int(rect[1])),int(rect[3]/5),(100,155,1),2)
            #for ii in rects: cv2.circle(tem_blob,(int(ii[0]),int(ii[1])),int(min(ii[3],ii[2])/2),(122,0,255),2)
            #for ii in rects_i: cv2.circle(tem_blob,(int(ii[0]),int(ii[1])),int(min(ii[3],ii[2])/2),(122,122,0),2)
            cv2.imwrite(f'{output}/Blobs/{filename}/{i.stem}_dice.jpg',tem_blob)
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
        save_hist(hists,f'{output}/hists.txt')
        with open(f'{output}/hists_columns.txt','w') as f:
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
    test_main_hist(test_folder,output=output_hists)
    #test_main(test_folder,output_LabelB=output_LabelB)
    #test_main_hist(test_folder,output=output_hists)
    #with open(f'{output_LabelB}/{pathlib.Path(test_folder).stem}_data_record.csv','w') as f:
    #    for i in data_record:
    #        f.write(','.join(map(str,i))+'\n')
    print('Time: ',round(time.time()-start,4),'s')
