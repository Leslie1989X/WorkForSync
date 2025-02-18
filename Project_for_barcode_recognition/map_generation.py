import numpy as np
import gc

__all__ = ['cal_box',
           'split_sort',
           'main_gen_map',
           'map_generation',
           ]
# 定义label的属性
labels_info = {'w':630,
               'h':105}

def normalization(data):
    if len(data.shape) == 1:
        data = data.reshape(1,-1)
    avg_data = np.mean(np.delete(data,[np.argmax(data),np.argmin(data)])) if data.size >2 else 0
    std_data = np.std(np.delete(data,[np.argmax(data),np.argmin(data)])) if data.size >2 else 0
    x = np.arange(len(data[0]))
    y = (data-avg_data)/std_data
    return x,y
def cal_box(data,n:float=1.5,lower:int=25,upper:int = 75):
    Q1 = np.percentile(data,lower)
    Q2 = np.percentile(data,upper)
    IQR = Q2 - Q1
    Q1m = Q1-n*IQR
    Q2m = Q2+n*IQR
    return Q1m, np.median(data),Q2m
    
def split_sort(data,indices,sort_key:int,*args, **kwargs):
    tems = np.split(data,indices)
    sort_arrays = [tem[np.argsort(tem[:,sort_key])] for tem in tems]
    if 'param_keys' in kwargs.keys():
        key = kwargs['param_keys']
        if 'param_angle' in kwargs.keys() and 'param_size' in kwargs.keys():
            avg_angle,std_angle = kwargs['param_angle']
            (avg_w,std_w),(avg_h,std_h),(avg_a,std_a) = kwargs['param_size']
            for i in sort_arrays:
                #TODO i的长度为1的时候，有0/0的数学问题。
                #TODO 没有针对有异物的时候，进行排除。利用size不同、灰阶不同、角度不同加以区别
                if len(i) == 1:
                    continue
                #np.where(i[:,4] > cal_box(i[:,4],lower=15,upper=85)[2])
                #np.where(i[:,4] < cal_box(i[:,4],lower=15,upper=85)[0])
                sigma = 1#(np.degrees(np.atan(np.ptp(i[:,key[0]])/np.ptp(i[:,key[1]])))-avg_angle)/std_angle
                sigma2 = (np.mean(i[:,key[2]])-avg_w)/std_w
                sigma3 = (np.mean(i[:,key[3]])-avg_h)/std_h
                sigma4 = (np.mean(i[:,key[4]])-avg_a)/std_a
                if np.any(np.abs([sigma,sigma2,sigma3,sigma4])>6):
                    raise Exception('dice size abnormal.')
        """
        for i in sort_arrays:
            if i.shape[0] < 2:
                pass
            else:
                nums = np.ptp(i[:,key[1]])/cal_box(np.diff(i[:,key[1]]))[1]+1
        """    
    data_new = np.concatenate(sort_arrays)
    return data_new

def rotation_coordinates(data:np.ndarray,theta:float):
    cos = np.cos(np.radians(theta))
    sin = np.sin(np.radians(theta))
    M = np.array([[cos,-sin],[sin,cos]])
    dst = data.dot(M)
    return dst

def map_generation(data1:np.ndarray,data2:np.ndarray,axis:int=1):
    assert type(data1) == np.ndarray,'wrong data type'
    assert type(data2) == np.ndarray,'wrong data type'
    assert type(axis) == int,'wrong axis type'
    if data1.dtype != 'int':
        data1 = data1.astype(dtype=int)
    if data2.dtype != 'int':
        data2 = data2.astype(dtype=int)
    data1_ = np.insert(np.cumsum(data1),0,0)-np.min(np.insert(np.cumsum(data1),0,0))
    data2_ = np.insert(np.cumsum(data2),0,0)-np.min(np.insert(np.cumsum(data2),0,0))
    map_item = np.zeros((np.max(data1_)+1,np.max(data2_)+1),dtype=np.int16)
    map_item[data1_,data2_] = 1
    if axis == 0:
        return map_item.T
    return map_item

def cal_simga(data:np.ndarray,avg:float,std:float,value:float=0.15,simga:float=5.0,deta:float=0.1):
    n = 0
    t = 0
    nn = []
    while abs(n)<simga and t<int(simga/deta):
        nn.append(n)
        if len(nn) > 3:
            if nn[-1] == nn[-3]:
                tem_s = np.where(np.abs(tem)>value)[0]
                result = cal_simga(data[tem_s],avg,std)
                if isinstance(result,np.ndarray):
                    a = np.round(dst)
                    a[tem_s] = result
                    return a
                raise Exception('cal sigma error.')
        dst = data/(avg+n*std)
        tem = dst-np.round(dst)
        tem_ = np.where(tem>value,tem-value,np.where(tem<-value,tem+value,0))
        ls = np.where(tem_<0)[0]
        hs = np.where(tem_>0)[0]
        t += 1
        l = ls.size
        h = hs.size
        if l>h:
            n+=deta
        elif l<h:
            n-=deta
        else:
            if l == h == 0:
                break
            else:
                n+=deta/2
    else:
        raise Exception('cal sigma error.')
    return np.round(dst)

def cal_shift(cal_avg,cal_std,cal_med,data1,data2,data3,shape,t1,t2):
    if np.abs(cal_std)>=1:
        cal_avg = cal_med
        cal_std = 0.5
    try:
        shift1 = np.concatenate([cal_simga(i,cal_avg,cal_std) for i in np.split(data1,t1+1)])
    except BaseException as e:
        shift1 = False
    try:
        n1 = cal_simga(data2,cal_avg,cal_std)
    except BaseException:
        n1 = False
    try:
        n2 = cal_simga(data3,cal_avg,cal_std)
    except BaseException:
        n2 = False

    shift2_nn2 = np.zeros_like(shape)
    if np.all(n1==n2) or isinstance(n2,np.ndarray):
        shift2_nn2[t2] = n2
    elif isinstance(n1,np.ndarray):
        shift2_nn2[t2] = n1
    else:
        shift2_nn2 = False
    return shift1,shift2_nn2

def main_gen_map(contours_info:np.ndarray,*args):
    # data filter
    global labels_info
    labels_obj = np.where((contours_info[:,2]<labels_info['w']+20) & 
                          (contours_info[:,2]>labels_info['w']-20) & 
                          (contours_info[:,3]>labels_info['h']-20) & 
                          (contours_info[:,3]<labels_info['h']+20))[0]
    contours_info = np.delete(contours_info,labels_obj,axis=0)
    if contours_info.size == 0:
        return np.empty(0,dtype=np.int16),np.empty(0,dtype=np.int16)
    contours_info = np.delete(contours_info,np.where(contours_info[:,5]<16)[0],axis=0)
    contours_info = np.delete(contours_info,np.where(contours_info[:,5]<cal_box(contours_info[:,5])[1]/4)[0],axis=0)
    if contours_info.size == 0:
        return np.empty(0,dtype=np.int16),np.empty(0,dtype=np.int16)
    elif contours_info.size == 1:
        return np.array([1],dtype=np.int16),np.array([1],dtype=np.int16)
    avg_a = np.mean(contours_info[:,5])
    std_a = np.std(contours_info[:,5])
    med_a = np.median(contours_info[:,5])
    avg_h = np.mean(contours_info[:,3])
    std_h = np.std(contours_info[:,3])
    avg_w = np.mean(contours_info[:,2])
    std_w = np.std(contours_info[:,2])
    """
    angle_abnormal_lower = np.where(contours_info[:,4] < cal_box(contours_info[:,4],lower=15,upper=85)[0])[0]
    angle_abnormal_upper = np.where(contours_info[:,4] > cal_box(contours_info[:,4],lower=15,upper=85)[2])[0]
    if angle_abnormal_lower.size>0 or angle_abnormal_upper.size>0:
        raise 'dice angle abnormal.'
    """
    angles_index = np.where((contours_info[:,4] != 0) & (contours_info[:,4] != 90))
    angles = contours_info[angles_index,4]
    std_angle = np.std(np.delete(angles,[np.argmax(angles),np.argmin(angles)])) if angles.size >2 else 0
    avg_angle = np.mean(np.delete(angles,[np.argmax(angles),np.argmin(angles)])) if angles.size >2 else 0
    k = angles.shape[1]/contours_info.shape[0]
    #print(std_angle,avg_angle,round(k,4))
    __contours_info = contours_info.copy()
    xy = rotation_coordinates(contours_info[:,:2],avg_angle*round(np.log(9*k+1)/np.log(10),4))
    contours_info = np.hstack([xy,contours_info[:,2:]])    
    #
    o_x = contours_info[np.lexsort((contours_info[:,1],contours_info[:,0]))]
    o_y = contours_info[np.lexsort((contours_info[:,0],contours_info[:,1]))]
    o_x_x = np.diff(o_x[:,0])       # 找列
    o_y_y = np.diff(o_y[:,1])       # 找行
    col_= np.mean(o_x_x[np.where((o_x_x<1.8*avg_w) & (o_x_x >0.2*avg_w))])/2 if np.mean(o_x_x) > 0.2*avg_w and np.mean(o_x_x) < 1.8*avg_w else 0.25*avg_w   # 包含间距的列宽, 拟定值
    row_= np.mean(o_y_y[np.where((o_y_y<1.8*avg_h) & (o_y_y >0.2*avg_h))])/2 if np.mean(o_y_y) > 0.2*avg_h and np.mean(o_y_y) < 1.8*avg_h else 0.25*avg_h   # 包含间距的行宽, 拟定值
    
    t1 = np.where(o_x_x > col_)[0]    # 列分割索引
    t2 = np.where(o_y_y > row_)[0]    # 行分割索引
    o_x_n = split_sort(o_x,t1+1,1,param_angle = (avg_angle,std_angle),param_keys=(0,1,2,3,5),param_size=((avg_w,std_w),(avg_h,std_h),(avg_a,std_a))) # 每列按行重新排序
    o_y_n = split_sort(o_y,t2+1,0,param_angle = (avg_angle,std_angle),param_keys=(1,0,2,3,5),param_size=((avg_w,std_w),(avg_h,std_h),(avg_a,std_a))) # 每行按列重新排序
    o_x_y = np.diff(o_x_n[:,1])
    o_y_x = np.diff(o_y_n[:,0])
    o_x_x2 = np.diff(o_x_n[:,0])
    o_y_y2 = np.diff(o_y_n[:,1])
    
    t1x = np.insert(t1+1,0,0)
    col_cal1 = np.diff(o_x_n[t1x,0])
    col_cal2 = np.diff(o_x_n[np.append(t1,len(o_x_n)-1),0])
    col_cal = np.append(col_cal1,col_cal2)
    if col_cal.size ==0:
        col_cal_avg = col_cal_med = avg_w
        col_cal_std = std_w
    else:
        col_cal_avg = np.mean(col_cal[np.where(col_cal<1.8*avg_w)])
        col_cal_std = np.std(col_cal[np.where(col_cal<1.8*avg_w)])
        col_cal_med = np.median(col_cal[np.where(col_cal<1.8*avg_w)])
    
    t2y = np.insert(t2+1,0,0)
    row_cal1 = np.diff(o_y_n[t2y,1])
    row_cal2 = np.diff(o_y_n[np.append(t2,len(o_y_n)-1),1])
    row_cal = np.append(row_cal1,row_cal2)
    if row_cal.size == 0:
        row_cal_avg = row_cal_med = avg_h
        row_cal_std = std_h
    else:
        row_cal_avg = np.mean(row_cal[np.where(row_cal<1.8*avg_h)])
        row_cal_std = np.std(row_cal[np.where(row_cal<1.8*avg_h)])
        row_cal_med = np.median(row_cal[np.where(row_cal<1.8*avg_h)])
    
    # 因为行间隔不会超过每个die的高度的一半，所以对row_cal需要核验校正。
    # 因为列间隔不会超过每个die的宽度的一半，所以对col_cal需要核验校正。
    
    # np.degrees(np.atan((np.cumsum(o_x_x)[t[i]-1]-np.cumsum(o_x_x)[t[i-1]])/(o_x[t[i],1]-o_x[t[i-1],1])))
    ratio = 0.1
    min_dis = 10
    
    #o_x_x[0]/(np.tan(np.radians(avg_angle+5*std_angle))*np.abs(o_x_y[0]))
    #sigma = (np.degrees(np.atan(np.sum(o_x_x[:3])/np.abs(np.sum(o_x_y[:3]))))-avg_angle)/std_angle
    i1 = np.diff(np.append(np.insert(t1,0,-1),len(o_x)-1))  # 每列计数
    i2 = np.diff(np.append(np.insert(t2,0,-1),len(o_y)-1))  # 每行计数
    #n1 = o_x_y/np.abs(cal_box(o_x_y)[1]) if np.abs(cal_box(o_x_y)[1]-row_cal_avg)/row_cal_avg<0.1 else o_x_y/row_cal_avg#/np.cos(np.radians(avg_angle+0*std_angle))  # 每颗die的相对位移，逐X，Y方向  因为已经经行了旋转，不需要进行余弦校正
    shift1,shift2_nn2 = cal_shift(row_cal_avg,row_cal_std,row_cal_med,o_x_y,row_cal1,row_cal2,o_y_y,t1,t2)
    shift2,shift1_nn1 = cal_shift(col_cal_avg,col_cal_std,col_cal_med,o_y_x,col_cal1,col_cal2,o_x_x,t2,t1)
    try:
        mapx = map_generation(shift1,shift1_nn1)
        mapy = map_generation(shift2,shift2_nn2,axis=0)
    except Exception as e:
        raise e
    gc.collect()
    return mapx,mapy

if __name__ == '__main__':
    import pathlib
    path = input('input path: ').replace('"','')
    if path == '':
        path = r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\IMG_Black_Normal\Blobs\2025_01_20\A301-UNN925-416_info.npy"
    contours_info = np.load(path)
    mapx,mapy = main_gen_map(contours_info)
    output = pathlib.Path(pathlib.Path(path).parent,pathlib.Path(path).stem)
    output.mkdir(parents=True,exist_ok=True)
    if np.all(mapx == mapy) and isinstance(mapx,np.ndarray):
        print('The same map.')
    if isinstance(mapx,np.ndarray):
        mapx_ = np.where(mapx == 1,'A',mapx)
        mapx_ = np.where(mapx_ == '0','.',mapx_)
        with open(f'{output}/{pathlib.Path(path).stem}_mapx.txt','w',encoding='utf-8') as f:
            for i in mapx_.tolist():
                f.write(''.join(i)+'\n')
    if isinstance(mapy,np.ndarray):
        mapy_ = np.where(mapy == 1,'A',mapy)
        mapy_ = np.where(mapy_ == '0','.',mapy_)
        with open(f'{output}/{pathlib.Path(path).stem}_mapy.txt','w',encoding='utf-8') as f:
            for i in mapy_.tolist():
                f.write(''.join(i)+'\n')
