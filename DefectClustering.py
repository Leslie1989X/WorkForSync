"""
用于学习二维坐标的聚类。
"""
import pandas as pd
import numpy as np
import pathlib
import matplotlib.pyplot as plt
import time
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        results = func(*args,**kwargs)
        print('timer record: ',round(time.time()-start,4),'s')
        return results
    return wrapper
@timer
def clustering(X:np.ndarray,eps:float=30.00,min_sample:int=1):
    dbscan = DBSCAN(eps=eps,min_samples=min_sample)
    clusters = dbscan.fit_predict(X)
    core_samples_mask = np.zeros_like(clusters,dtype=bool)
    core_samples_mask[dbscan.core_sample_indices_] = True
    try:
        silhouette_avg = silhouette_score(X,clusters)
    except ValueError as e:
        silhouette_avg = -2
    return clusters,silhouette_avg,core_samples_mask
def draw(X:np.ndarray,clusters:np.ndarray,s=15,alpha=0.5,needRect=True,core_samples_mask:np.ndarray=None):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    # 绘制聚类结果
    if type(core_samples_mask) == np.ndarray:
        plt.scatter(X[:,0],X[:,1],c=np.where(clusters==-1,'gray','blue'),s=s,alpha=alpha)
        plt.scatter(X[core_samples_mask,0],X[core_samples_mask,1],c='r',s=s+5,marker='o')
    else:
        plt.scatter(X[:,0],X[:,1],c=clusters,s=s,alpha=alpha)
    if needRect:
        shift = 9
        tem = np.unique(clusters)
        tem = np.delete(tem,np.where(tem==-1))        
        for i in range(len(tem)):
            _tem = X[np.where(clusters==tem[i])[0]]
            xmax,ymax = np.max(_tem,axis=0)
            xmin,ymin = np.min(_tem,axis=0)
            rect = plt.Rectangle((xmin-shift,ymin-shift),xmax-xmin+shift*2,ymax-ymin+shift*2,fill = False,edgecolor = 'g',linewidth = 2)
            plt.gca().add_patch(rect)
    plt.gca().set_aspect('equal')
    plt.title("基于固定距离的聚类结果")
    plt.xlabel("X轴")
    plt.ylabel("Y轴")
    plt.show()
def clustering_fur(RawData:pd.DataFrame,clusters:np.ndarray,core_samples_mask:np.ndarray,min_dice:int = 3):
    tem = np.delete(np.unique(clusters),np.where(np.unique(clusters)==-1))        
    for i in tem:
        _cache = RawData.iloc[np.where(clusters == i)]
        if len(set(zip(_cache['Col'],_cache['Row']))) >= min_dice:
            print(_cache)
        else:
            core_samples_mask[np.where(clusters == i)] = False
            clusters = np.where(clusters==i,-1,clusters)
    return clusters, core_samples_mask
eps = 60
min_sample = 4
min_dice = 3
test = r"E:\CodeProject\VSCodeProjects\My_Projects\work_data\test_csv\2.csv"
df = pd.read_csv(test)
data = df.loc[:,['X','Y']].values
np.random.seed(0)
#data = np.random.randint(100,5000,size=(999,2))

clusters, silhouette_avg,core_samples_mask = clustering(data,eps,min_sample)
clusters, core_samples_mask = clustering_fur(df,clusters,core_samples_mask,min_dice)
print(f"silhouette_score: {silhouette_avg}")
draw(data,clusters,s=7,needRect=True,core_samples_mask=core_samples_mask)
#print(df.loc[np.where(clusters!= -1)[0],:])