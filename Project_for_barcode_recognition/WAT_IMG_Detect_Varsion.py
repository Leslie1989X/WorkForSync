import multiprocessing.pool
import numpy as np
import pathlib
import time
import gc
import sys
from Frame_det_cont import pre_img_process
from IMG_Process import main_img_process
from Gui_body import MainApp,check_pid
import logging
import logging.handlers
import wmi
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import queue
import threading
import multiprocessing
import os
import psutil

class WatChangeHandler(FileSystemEventHandler):
    def __init__(self,path:str,observer,output_label:str=None,output_map:str=None) -> None:
        super().__init__()
        self.path = path
        self.observer = observer
        self.events_create = dict()
        self.output_label = output_label
        self.output_map = output_map
    def dispatch(self, event) -> None:
        """Dispatches events to the appropriate methods.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`FileSystemEvent`
        """
        self.on_any_event(event)
        thread_it(getattr(self, f"on_{event.event_type}"),'tem_thread',event)
        #getattr(self, f"on_{event.event_type}")(event)
    def on_any_event(self, event) -> None:
        pass
        
    def on_opened(self, event) -> None:
        pass
    def on_closed_no_write(self, event) -> None:
        pass
    def on_closed(self, event) -> None:
        pass
    def on_modified(self, event) -> None:
        if event.is_directory:
            logger_fileChange.info("directory modified|{0}".format(event.src_path))
            if event.src_path == str(self.path):
                self.observer.stop()
                logger_fileChange.error('TargetFile modified...')
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
            if event.src_path == str(self.path):
                self.observer.stop()
                logger_fileChange.error('TargetFile moved...')
        else:
            logger_fileChange.info("file moved|from {0} to {1}".format(event.src_path,event.dest_path))
        pass

    def on_created(self, event) -> None:
        if event.is_directory:
            logger_fileCreate.info("directory created|{0}".format(event.src_path))
        else:
            logger_fileCreate.info("file created|{0}".format(event.src_path))
            if pathlib.Path(event.src_path).suffix in ['.jpg','.JPG','.BMP','.bmp','jpeg']:
                if False:
                    pass
                else:
                    event_queue.event_queue.put(event.src_path)
                    #logger_fileCreate.info(f'Start to detect barcode|{event.src_path}')



class Controller:
    def __init__(self,loggers:list[logging.Logger]=None,outputpath_history:str=None):
        self.observer = None
        self.logger_main = loggers[0]
        self.run = False
        self.status = False
        self.thread_s = []
        self.event = threading.Event()
        self.outputpath_history = outputpath_history
        
    def start_watchdog(self,targetFolder,outputpath1,outputpath2,run:bool):
        try:
            pathlib.Path(outputpath1).mkdir(parents=True,exist_ok=True)
            with open(pathlib.Path(outputpath1,'demo.txt'),mode='w',encoding='utf-8') as f:
                f.write('demo')
            pathlib.Path(outputpath1,'demo.txt').unlink()
        except Exception as except_log_output:
            return 0
        try:
            pathlib.Path(outputpath2).mkdir(parents=True,exist_ok=True)
            with open(pathlib.Path(outputpath2,'demo.txt'),mode='w',encoding='utf-8') as f:
                f.write('demo')
            pathlib.Path(outputpath2,'demo.txt').unlink()
        except Exception as except_log_output:
            return 0
        self.logger_main.info(f'start manual|observer {self.observer}')
        self.run = run
        event_queue._stop_flag = False
        thread_monitor = thread_it(self.monitor_folder,'monitor',targetFolder,timeout=5)
        thread_process_events = thread_it(event_queue.process_events,'process_events',outputpath1,outputpath2,self.outputpath_history,timeout=1)
        thread_result = thread_it(event_queue.process_result,'process_result')
        if thread_monitor is not None and thread_process_events is not None and thread_result is not None:
            self.thread_s.append(thread_monitor)
        if thread_process_events is not None:
            self.thread_s.append(thread_process_events)
        if thread_result is not None:    
            self.thread_s.append(thread_result)
        
    def stop_watchdog(self,run:bool):
        event_queue.stop_processing()
        self.logger_main.info(f'end manual|observer {self.observer}')
        self.run = run
        thread_it(self.closed_thread_s,'tem_thread')
        self.event.clear()
    
    def closed_thread_s(self):
        for tem in self.thread_s[:]:
            if not tem.is_alive():
                self.logger_main.debug(f'thread|{tem}')
                self.thread_s.remove(tem)
            else:
                self.logger_main.debug(f'thread|{tem}')
                tem.join()
                self.thread_s.remove(tem)
        print('closed_all_threads')
    
    def monitor_folder(self,targetFolder:pathlib.Path,*args,timeout:int=30): 
        output_label = args[0] if len(args)>0 else None
        output_map = args[1] if len(args)>1 else None
        while self.run:
            app.operate_button(app.button_OK1,operate='start')
            TargetFolderName = str(time.localtime().tm_year)+'_'+str(time.localtime().tm_mon)#+'_'+str(time.localtime().tm_hour)
            try:
                if self.check_monitor_folder(targetFolder,TargetFolderName,timeout):
                    targetFilepath = pathlib.Path(targetFolder,TargetFolderName)
                    self.observer = self.observer_create(targetFilepath,output_label,output_map)
                    self.status = app.status = True
                    app.operate_button(app.button_OK1,operate='start')
                    self.logger_main.info(f'start|observer {self.observer}')
                    while self.observer.is_alive() and self.run:
                        newTargetFileName = str(time.localtime().tm_year)+'_'+str(time.localtime().tm_mon)#+'_'+str(time.localtime().tm_hour)
                        if TargetFolderName == newTargetFileName:
                            self.check_monitor_folder(targetFolder,TargetFolderName,0.1)
                            time.sleep(1)
                            continue
                        else:
                            self.observer.stop()
                    else:
                        self.observer.stop()
                        self.logger_main.info(f'end|observer {self.observer}')
                        self.status = app.status = False
                        app.operate_button(app.button_OK1,operate='end')
                else:
                    self.status = app.status = False
                    app.operate_button(app.button_OK1,operate='end')
            except TimeoutError as t:
                self.status = app.status = False
                app.operate_button(app.button_OK1,operate='end')
                self.logger_main.error(str(t))
                self.observer.stop() if self.observer else 0
            finally:
                pass
        else:
            self.observer.join() if self.observer else 0
            print('closed')
        
    def check_monitor_folder(self,targetFolder,TargetFolderName,timeout:int=120): 
        __start = time.time()
        while not pathlib.Path(targetFolder,TargetFolderName).exists():
            if not self.run:
                return False
            time.sleep(0.5)
            if time.time() - __start > timeout:
                raise TimeoutError(f'timeout|Not found {str(pathlib.Path(targetFolder,TargetFolderName))}.')
        else:
            return True

    def observer_create(self,targetFilepath,output_label:str=None,output_map:str=None):
        observer = Observer()
        event_handler = WatChangeHandler(targetFilepath,observer,output_label,output_map)
        observer.schedule(event_handler,targetFilepath,recursive=False)
        observer.daemon = True
        observer.start()
        return observer

class Processor:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.multiprocessing_results = queue.Queue()
        self._stop_flag = True
        
    def process_events(self,outputpath1,outputpath2,outputpath_history,timeout:int=1):
        self.pool = multiprocessing.Pool()
            
        while not self._stop_flag:
            try:
                event_src_path = self.event_queue.get(timeout=timeout)
                #print(event_src_path)
                result = self.pool.apply_async(self.multiprocessing_main,args=(event_src_path,outputpath1,outputpath2,outputpath_history),error_callback=self.error_callback)
                self.multiprocessing_results.put((event_src_path,result))
                
            except queue.Empty:
                #time.sleep(1)
                continue
            self.event_queue.task_done()
    @staticmethod
    def error_callback(e):
        (f"任务执行出错: {e}")
        
    def process_result(self):
        while not self._stop_flag:
            while not self.multiprocessing_results.empty():
                path, res = self.multiprocessing_results.get()
                if res.ready():
                    try:
                        final_result = res.get()
                        if isinstance(final_result,tuple):
                            result,info = final_result
                            if result.result_clasify == '12Inch':
                                pass
                            if result.result_clasify == 'backlight':
                                logger_result_BW.info(f'{info}|{pathlib.Path(path).name}|{result.time}s|{result.circle}')
                            if result.result_clasify == 'frontlight':
                                logger_result.info(f'{info}|{pathlib.Path(path).name}|{result.time}s')
                                for n in result.label.keys():
                                    if isinstance(result.label[n],tuple):
                                        logger_detect.info(f"{pathlib.Path(path).name}|label {n}|{result.label[n][0][0].data.decode('utf-8')}|{result.label[n][1]}|{result.label[n][0][0]}")
                                        continue
                                    if result.label[n] == 'Empty':
                                        logger_detect.info(f"{pathlib.Path(path).name}|label {n}|Empty|[]|[]")
                                        continue
                                    if result.label[n] is None:
                                        logger_detect.info(f"{pathlib.Path(path).name}|label {n}|Fail to read barcode|[]|[]")
                                        continue
                        else:
                            pass
                    except Exception as e:
                        print(f"Error getting result for {path}: {e}")
                else:
                    self.multiprocessing_results.put((path, res))
                self.multiprocessing_results.task_done()
                if self._stop_flag:
                    break
            else:
                time.sleep(1)
                #show_process_info()
        
    @staticmethod 
    def multiprocessing_main(path:str,output_label:str,output_maps:str,outputpath_history:str):
        start = time.time()
        results = main_img_process(path,label_ns = [2],output_label=output_label,output_maps=output_maps,outputpath_history=outputpath_history)
        if results is not None:
            result = results[0]
            result2 = results[1]
            result.time = round(time.time()-start,3)
            del results
            return result,result2
        else:
            return round(time.time()-start,3)
    
    def stop_processing(self):
        self._stop_flag = True
        while not self.event_queue.empty():
            self.event_queue.get()
            self.event_queue.task_done()
        else:
            self.event_queue.join()
        while not self.multiprocessing_results.empty():
            self.multiprocessing_results.get()
            self.multiprocessing_results.task_done()
        else:
            self.multiprocessing_results.join()
        if self.pool:
            self.pool.terminate()
            self.pool.join()

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
    outputpath_history = pathlib.Path(logpath,'history')
    try:
        pathlib.Path(outputpath_log).mkdir(parents=True,exist_ok=True)
        pathlib.Path(outputpath_history).mkdir(parents=True,exist_ok=True)
        with open(outputpath_log/'demo.txt',mode='w',encoding='utf-8') as f:
            f.write('demo')
        pathlib.Path(outputpath_log/'demo.txt').unlink()
    except Exception as except_log_output:
        outputpath_log = pathlib.Path(pathlib.Path(__file__).parent,'log',time.strftime("%Y%m%d",time.localtime()))
        outputpath_history = pathlib.Path(pathlib.Path(__file__).parent,'history',time.strftime("%Y%m%d",time.localtime()))
        pathlib.Path(outputpath_log).mkdir(parents=True,exist_ok=True)
        pathlib.Path(outputpath_history).mkdir(parents=True,exist_ok=True)
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
    return loggers,handlers,outputpath_history

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
    if name == 'tem_thread' or not repeat_thread_detection(funcN=name):
        t = threading.Thread(target=func,name=name,args=args,kwargs=kwargs)
        t.daemon = True
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

def show_process_info():
    current_pid = os.getpid()
    print(f"当前进程的 PID 是: {current_pid}")
    try:
        process = psutil.Process(current_pid)
        print(f"进程名称: {process.name()}")
        print(f"进程状态: {process.status()}")
        print(f"进程创建时间: {process.create_time()}")
        print(f"进程使用的 CPU 百分比: {process.cpu_percent(interval=1)}%")
        print(f"进程使用的内存百分比: {process.memory_percent()}%")
    except psutil.NoSuchProcess:
        print(f"进程 {current_pid} 不存在。")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        if check_pid(__file__) != None:
            gc.collect()
            sys.exit(0)
        else:            
            params = get_config()
            app = MainApp(baseName='JXY',params=params)
            app.withdraw()
            log_path = pathlib.Path(app.root_path,params['log_path'])
            loggers,handlers,outputpath_history = create_logger(log_path)
            controller = Controller(loggers,outputpath_history)
            event_queue = Processor()
            [logger_main,logger_fileCreate,logger_fileChange,logger_result,logger_result_BW,logger_detect,logger_detect_BW] = loggers
            app.logger = [logger_main,logger_result,logger_result_BW,logger_detect,logger_detect_BW]
            app.controller = controller
            app.set_my_menu()
            app.deiconify()
            #show_process_info()
            app.after(800,app.action_start)
            app.mainloop()
            
            # tk关闭后进行清理
            controller.run = False
            controller.status = False
            for i in controller.thread_s:
                i.stop()
                i.join()
            event_queue.stop_processing()
            if controller.observer:
                controller.observer.stop()
                controller.observer.join()
            for index in range(len(logger_main.handlers)):
                if type(logger_main.handlers[index]) == logging.StreamHandler:
                    del logger_main.handlers[index]
            logger_main.info("exit|program exit.")            
    finally:
        gc.collect()
        sys.exit(0)
