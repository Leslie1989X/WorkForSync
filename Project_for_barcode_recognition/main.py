import numpy as np
import pathlib
import time
import cv2
import gc
import sys
from Frame_det_cont import dice_det_main,save_maps
from WAT_IMG_Process import main_image_process
from Gui_body import MainApp,check_pid
import logging
import logging.handlers
import wmi
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re
import json
import queue
import concurrent.futures
import threading

class WatChangeHandler(FileSystemEventHandler):
    def __init__(self,path:str,observer,output_label,output_map) -> None:
        super().__init__()
        self.path = path
        self.observer = observer
        self.events_create = dict()
        self.pattern = re.compile(r'-[^-]+-')
        self.output_label = output_label
        self.output_map = output_map
    
    def on_modified(self, event) -> None:
        if event.is_directory:
            logger_fileChange.info("directory modified|{0}".format(event.src_path))
        elif not event.is_directory:
            logger_fileChange.info("file modified|{0}".format(event.src_path))

    def on_deleted(self, event) -> None:
        if event.is_directory:
            logger_fileChange.info("directory deleted|{0}".format(event.src_path))
            if event.src_path == str(self.path):
                self.observer.stop()
                logger_fileChange.error('TargetFile deleted...')
        else:
            logger_fileChange.info("file deleted|{0}".format(event.src_path))
        pass

    def on_moved(self, event) -> None:
        if event.is_directory:
            logger_fileChange.info("directory moved|from {0} to {1}".format(event.src_path,event.dest_path))
        else:
            logger_fileChange.info("file moved|from {0} to {1}".format(event.src_path,event.dest_path))
        pass

    def on_created(self, event) -> None:
        if event.is_directory:
            logger_fileCreate.info("directory created|{0}".format(event.src_path))
        else:
            logger_fileCreate.info("file created|{0}".format(event.src_path))
            if pathlib.Path(event.src_path).suffix in ['.jpg','.JPG','.BMP','.bmp']:
                if False:
                    pass
                else:
                    logger_fileCreate.info(f'Start to detect barcode|{event.src_path}')

class Controller:
    def __init__(self,loggers:list[logging.Logger]=None):
        self.observer = None
        self.logger_main = loggers[0]
        self.run = False
        self.status = False
        self.thread_s = []
        
    def start_watchdog(self,targetFolder,outputpath1,outputpath2,run:bool):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.run = run
        thread_ = thread_it(self.monitor_folder,'monitor',targetFolder,outputpath1,outputpath2,timeout=45)
        if thread_ is not None:
            self.thread_s.append(thread_)
            return True
        else:
            return False
        
    def stop_watchdog(self,run:bool):
        """if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None"""
        #app.operate_button(app.button_OK1,operate='end')
        self.run = run
        #app.status = False
        #for i in self.thread_s:
        #    i.join()
            
    def monitor_folder(self,targetFolder:pathlib.Path,*args,timeout:int=10): 
        output_label = args[0]
        output_map = args[1]
        while self.run:
            TargetFolderName = str(time.localtime().tm_year)+'_'+str(time.localtime().tm_mon)+'_'+str(time.localtime().tm_hour)
            print(TargetFolderName)
            try:
                if self.check_monitor_folder(targetFolder,TargetFolderName,timeout):
                    targetFilepath = pathlib.Path(targetFolder,TargetFolderName)
                    self.observer = self.observer_create(targetFilepath,output_label,output_map)
                    self.status = app.status = True
                    app.operate_button(app.button_OK1,operate='start')
                    while self.observer.is_alive() and self.run:
                        newTargetFileName = str(time.localtime().tm_year)+'_'+str(time.localtime().tm_mon)+'_'+str(time.localtime().tm_hour)
                        time.sleep(1)
                        if TargetFolderName == newTargetFileName:
                            time.sleep(1)
                            continue
                        else:
                            self.observer.stop()
                    else:
                        self.observer.stop()
                        self.status = app.status = False
                        app.operate_button(app.button_OK1,operate='end')
            except TimeoutError as t:
                self.logger_main.error(str(t))
                self.observer.stop() if self.observer else 0
            finally:
                pass
        else:
            print('closed')
        
    def check_monitor_folder(self,targetFolder,TargetFolderName,timeout:int=120): 
        __start = time.time()
        while not pathlib.Path(targetFolder,TargetFolderName).exists() and self.run:
            time.sleep(2)
            if time.time() - __start > timeout:
                raise TimeoutError(f'timeout | Not found {str(pathlib.Path(targetFolder,TargetFolderName))}.')
        else:
            return True        
    def observer_create(self,targetFilepath,output_label,output_map):
        observer = Observer()
        event_handler = WatChangeHandler(targetFilepath,observer,output_label,output_map)
        observer.schedule(event_handler,targetFilepath,recursive=False)
        observer.daemon = True
        observer.start()
        return observer
    
def getInfo():
    w = wmi.WMI()
    user = pathlib.Path.home().name
    try:
        userdetail = w.Win32_UserAccount(Name =user)[0]
    except Exception:
        user = 'DefaultAccount'
        userdetail = w.Win32_UserAccount(Name =user)[0]
    
    nic_configs = w.Win32_NetworkAdapterConfiguration(IPEnabled=True)
    if nic_configs != []:
        nic = nic_configs[0]
        MAC = nic.MACAddress
        IPV4 = nic.IPAddress[0]
        try:
            DNSHostName = nic.DNSHostName
        except Exception:
            DNSHostName = 'Non-DNSHostName'
    else:
        MAC = 'NA'
        IPV4 = 'NA'
        DNSHostName = 'Non-DNSHostName'
    return MAC,IPV4,DNSHostName,user,userdetail

def create_logger(logpath:str,streamHandlerBox:None=None):
    # 信息获取
    MAC,IPV4,DNSHostName,user,userdetail = getInfo()
    log_name = str(DNSHostName+'_'+IPV4)
    outputpath_log = pathlib.Path(logpath,'log')
    try:
        pathlib.Path(outputpath_log).mkdir(parents=True,exist_ok=True)
        with open(outputpath_log/'demo.txt',mode='w',encoding='utf-8') as f:
            f.write('demo')
        pathlib.Path(outputpath_log/'demo.txt').unlink()
    except Exception as except_log_output:
        outputpath_log = pathlib.Path(pathlib.Path(__file__).parent,'log',time.strftime("%Y%m%d",time.localtime()))
        pathlib.Path(outputpath_log).mkdir(parents=True,exist_ok=True)
        with open(outputpath_log/'demo.txt',mode='w',encoding='utf-8') as f:
            f.write('demo')
        pathlib.Path(outputpath_log/'demo.txt').unlink()
    
    formator = logging.Formatter(fmt="%(asctime)s|%(filename)s|%(levelname)s|%(message)s")    # 日志格式器
    logger_main = logging.Logger('main',level=logging.DEBUG)    # 创建日志器，WAT monitor log main
    logger_fileCreate = logging.getLogger('FileCreate')         # 创建日志器，WAT monitor log Create
    logger_fileCreate.setLevel(logging.DEBUG)                    # Set level
    logger_fileChange = logging.getLogger('FileChange')         # 创建日志器，WAT monitor log file change
    logger_fileChange.setLevel(logging.DEBUG)                    # Set level
    logger_result = logging.getLogger('BarcodeResult')
    logger_result.setLevel(logging.DEBUG)
    logger_result_BW = logging.getLogger('MapResult')
    logger_result_BW.setLevel(logging.DEBUG)
    logger_detect = logging.getLogger('BarcodeRec')
    logger_detect.setLevel(logging.DEBUG)
    logger_detect_BW = logging.getLogger('MapRec')
    logger_detect_BW.setLevel(logging.DEBUG)
    
    loggers = [logger_main,logger_fileCreate,logger_fileChange,logger_result,logger_result_BW,logger_detect,logger_detect_BW]
    handlers = []
    # StreamHandler
    #sh1 = logging.StreamHandler(streamHandlerBox)
    #sh1.setFormatter(formator)
    # TimedRotatingFileHandler
    for self_log in loggers:
        #if self_log.name in ['FileCreate','FileChange',]:
        #    pass
        #else:
        #    self_log.addHandler(sh1)
        handlerDate = logging.handlers.TimedRotatingFileHandler(f"{outputpath_log}\\{log_name}_WATMonitor_{self_log.name}.log",when='W0',backupCount=0,encoding='utf-8')
        handlerDate.setFormatter(formator)
        self_log.addHandler(handlerDate)
        self_log.debug(f'logger [{self_log.name}] is working.')
        handlers.append(handlerDate)
    """
    catalogs = ['main','FileCreate','FileChange','BarcodeResult','MapResult','BarcodeRec','MapRec']
    loggers_dict = dict()
    for i in catalogs:
        loggers_dict[i] = logging.getLogger(str(i))
        loggers_dict[i].setLevel(logging.DEBUG)
        loggers_dict[i].addHandler(sh1)
        handlerDate = logging.handlers.TimedRotatingFileHandler(f"{outputpath_log}\\{log_name}_Test_{loggers_dict[i].name}.log",when='W0',backupCount=0,encoding='utf-8')
        handlerDate.setFormatter(formator)
        loggers_dict[i].addHandler(handlerDate)
        loggers_dict[i].debug(f'logger [{loggers_dict[i].name}] is working.')
    """
    # logging
    for i,j in zip([MAC,IPV4,DNSHostName,user,userdetail],['MAC','IPV4','DNSHostName','User','UserInfo']):
        logger_main.debug(f'{j}: {i}')
    return loggers,handlers

def create_alogger(logger:logging.Logger=None,streamHandlerBox:None=None):
    # 创建一个队列
    log_queue = queue.Queue()

    # 创建一个 QueueHandler，将日志消息放入队列
    queue_handler = logging.handlers.QueueHandler(log_queue)

    # 创建一个日志记录器，并添加 QueueHandler
    logger = logging.getLogger()
    logger.addHandler(queue_handler)
    logger.setLevel(logging.DEBUG)
    
    # 创建 TimedRotatingFileHandler，用于实际记录日志
    file_handler = logging.handlers.TimedRotatingFileHandler('app.log', when='D', interval=1, backupCount=7)
    formator = logging.Formatter(fmt="%(asctime)s|%(filename)s|%(levelname)s|%(message)s")    # 日志格式器
    file_handler.setFormatter(formator)
    
    sh1 = logging.StreamHandler(streamHandlerBox)
    sh1.setFormatter(formator)
    logger.addHandler(sh1)
    
    # 创建一个 QueueListener，从队列中取出日志消息并交给 TimedRotatingFileHandler 处理
    queue_listener = logging.handlers.QueueListener(log_queue, file_handler)
    queue_listener.start()
    # 模拟记录日志
    for i in range(2000):
        logger.debug(f"Logging message {i}")
    # 停止 QueueListener
    queue_listener.stop()

def thread_it(func,name:str,*args,**kwargs):
    if not repeat_thread_detection(funcN=name):
        global event
        event = threading.Event()
        t = threading.Thread(target=func,name=name,args=args,kwargs=kwargs)
        t.setDaemon(True)                               # 守护线程，True: 主进程退出则退出。
        t.start()
        return t
def repeat_thread_detection(funcN):
    for item in threading.enumerate():
        if funcN==item.name:
            return True
    return False    

def get_config():
    param = {'targetFolder':r'E:\WDCM_IMG',
             'map_path':'WAT Validation/WAT Mapping',
             'label_path':'WAT Validation/Frame Label B',
             '_root_path':{"SX":r'\\10.162.2.50\sx_eng_data\rwfabdata',"OSC":r"\\172.34.12.5\rwfabdata"},
             'log_path':'WAT Validation/Data',
             }
    try:
        with open('config.json','r') as f:
            data = json.load(f)
        assert 'targetFolder' in data.keys(), 'lacking of targetFolder'
        assert 'map_path' in data.keys(), 'lacking of map_path'
        assert 'label_path' in data.keys(), 'lacking of label_path'
        assert '_root_path' in data.keys(), 'lacking of _root_path'
        assert 'log_path' in data.keys(), 'lacking of log_path'
        
        for k,v in data.items():
            if isinstance(v,str) or isinstance(v,dict):
                continue
            else:
                raise Exception('json文件解析错误,将使用默认json配置。')
    except Exception as e:
        print(e)
        with open('config.json','w') as f:
            json.dump(param,f,indent=4,ensure_ascii=False)
        return param
    else:
        return data

if __name__ == '__main__':
    try:
        if check_pid(__file__) != None:
            gc.collect()
            sys.exit(0)
        else:
            params = get_config()
            app = MainApp(baseName='JXY',params=params)
            app.withdraw()
            log_path = pathlib.Path(app.root_path,params['log_path'])
            loggers,handlers = create_logger(log_path)
            controller = Controller(loggers)
            [logger_main,logger_fileCreate,logger_fileChange,logger_result,logger_result_BW,logger_detect,logger_detect_BW] = loggers
            app.logger = loggers
            app.controller = controller
            app.set_my_menu()
            app.deiconify()
            #app = MainApp(baseName='JXY',params=params,logger=loggers ,controller=controller)
            app.mainloop()
    finally:
        gc.collect()
        sys.exit(0)
