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
    plt.savefig(r"E:\CodeProject\VSCodeProjects\My_Projects\Project_daily\Git from OV\Project_for_barcode_recognition\figure1.png",dpi=300)
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
o_x_x = np.diff(o_x[:,0])
o_x_y = np.diff(o_x[:,1])
o_y_x = np.diff(o_y[:,0])
o_y_y = np.diff(o_y[:,1])
#draw(o_x_x.reshape(1,-1))
#draw(o_x_y.reshape(1,-1))
draw(o_y_x.reshape(1,-1))
draw(o_y_y.reshape(1,-1))
pass
o_x_x[0]/(np.tan(np.radians(avg_angle+5*std_angle))*np.abs(o_x_y[0]))
t = np.where(o_x_x > np.mean(o_x_x))[0]
o_x_y[t]/np.abs(cal_box(o_x_y)[1])/np.cos(np.radians(avg_angle+0*std_angle))