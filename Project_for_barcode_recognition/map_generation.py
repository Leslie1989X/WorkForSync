import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

#data = pd.read_csv(r"E:\CodeProject\VSCodeProjects\My_Projects\Project_daily\Git from OV\Project_for_barcode_recognition\A301-UNN864-416_contours_info.csv",
#                   header=None)
#datas = data.values

def draw(data,_normalization:bool = False):
    if _normalization:
        x,y = normalization(data)
    else:
        if len(data.shape) == 1:
            data = data.reshape(1,-1)
        x = np.arange(len(data[0]))
        y = data
    plt.scatter(x,y[0],s=2,alpha=0.6)
    plt.savefig(r"E:\CodeProject\VSCodeProjects\My_Projects\Project_daily\Git from OV\Project_for_barcode_recognition\data\figure1.png",dpi=300)
def normalization(data):
    if len(data.shape) == 1:
        data = data.reshape(1,-1)
    avg_data = np.mean(np.delete(data,[np.argmax(data),np.argmin(data)])) if data.size >2 else 0
    std_data = np.std(np.delete(data,[np.argmax(data),np.argmin(data)])) if data.size >2 else 0
    x = np.arange(len(data[0]))
    y = (data-avg_data)/std_data
    return x,y
def cal_box(data,n:float=1.5):
    Q1 = np.percentile(data,25)
    Q2 = np.percentile(data,75)
    IQR = Q2 - Q1
    Q1m = Q1-n*IQR
    Q2m = Q2+n*IQR
    return Q1m, np.median(data),Q2m
    
def split_sort(data,indices,sort_key:int,*args, **kwargs):
    tems = np.split(data,indices)
    sort_arrays = [tem[np.argsort(tem[:,sort_key])] for tem in tems]
    if 'param_keys' in kwargs.keys():
        key1,key2 = kwargs['param_keys']
        if 'param_angle' in kwargs.keys():
            avg_angle,std_angle = kwargs['param_angle']
            for i in sort_arrays:
                sigma = (np.degrees(np.atan(np.ptp(i[:,key1])/np.ptp(i[:,key2])))-avg_angle)/std_angle
                if np.abs(sigma)>6:
                    raise
        for i in sort_arrays:
            nums = np.ptp(i[:,key2])/cal_box(np.diff(i[:,key2]))[1]+1
            print(np.around(nums))
            
    (np.atan(np.ptp(i[:,key1])/np.ptp(i[:,key2])))
    data_new = np.concatenate(sort_arrays)
    return data_new
    
contours_info = np.load(r"E:\CodeProject\VSCodeProjects\My_Projects\Project_daily\Git from OV\Project_for_barcode_recognition\A301-UNN864-416_contours_info.npy")
angles = contours_info[np.where((contours_info[:,4] != 0) & (contours_info[:,4] != 90)),4]
std_angle = np.std(np.delete(angles,[np.argmax(angles),np.argmin(angles)])) if angles.size >2 else 0
avg_angle = np.mean(np.delete(angles,[np.argmax(angles),np.argmin(angles)])) if angles.size >2 else 0
o_x = contours_info[np.lexsort((contours_info[:,1],contours_info[:,0]))]
o_y = contours_info[np.lexsort((contours_info[:,0],contours_info[:,1]))]
avg_h = np.mean(o_x[:,3])
std_h = np.std(o_x[:,3])
avg_w = np.mean(o_x[:,2])
std_w = np.std(o_x[:,2])
o_x_x = np.diff(o_x[:,0])       # 找列
o_y_y = np.diff(o_y[:,1])       # 找行
t1 = np.where(o_x_x > np.mean(o_x_x))[0]    # 列分割索引
t2 = np.where(o_y_y > np.mean(o_y_y))[0]    # 行分割索引
o_x_n = split_sort(o_x,t1+1,1,param_angle = (avg_angle,std_angle),param_keys=(0,1)) # 每列按行重新排序
o_y_n = split_sort(o_y,t2+1,0,param_angle = (avg_angle,std_angle),param_keys=(1,0)) # 每行按列重新排序
o_x_y = np.diff(o_x_n[:,1])
o_y_x = np.diff(o_y_n[:,0])
#draw(o_x_x.reshape(1,-1))
#draw(o_x_y.reshape(1,-1))
#draw(o_y_x.reshape(1,-1))
#draw(o_y_y.reshape(1,-1))
pass
#o_x_x[0]/(np.tan(np.radians(avg_angle+5*std_angle))*np.abs(o_x_y[0]))
#sigma = (np.degrees(np.atan(np.sum(o_x_x[:3])/np.abs(np.sum(o_x_y[:3]))))-avg_angle)/std_angle
i1 = np.diff(np.append(np.insert(t1,0,-1),len(o_x)-1))  # 每列计数
i2 = np.diff(np.append(np.insert(t2,0,-1),len(o_y)-1))  # 每行计数
n1 = o_x_y/np.abs(cal_box(o_x_y)[1])/np.cos(np.radians(avg_angle+0*std_angle))
n2 = o_y_x/np.abs(cal_box(o_y_x)[1])/np.cos(np.radians(avg_angle+0*std_angle))
shift1 = np.around(n1) if np.all(np.abs((n1-np.around(n1))/n1)<0.01) else False
shift2 = np.around(n2) if np.all(np.abs((n2-np.around(n2))/n2)<0.01) else False
pass
if not isinstance(shift1,bool):
    tems = ['A']
    x = 0
    for index,i in enumerate(shift1):
        if index in t1:
            x+=1
            a = int(len(tems[x-1])-1+i)
            for index2 in range(x):
                tem = tems[index2]
                if a < 0:
                    tems[index2] = '.'*abs(a)+tem
            tems.append('.'*int(a)+'A' if a>=0 else 'A')
            pass
        else:
            tems[x] +='.'*int(i-1)+'A'
            pass
        pass
    max_length = max(len(item) for item in tems)
    tems = [item.ljust(max_length,'.') for item in tems]
    for i in tems: print(i)
        