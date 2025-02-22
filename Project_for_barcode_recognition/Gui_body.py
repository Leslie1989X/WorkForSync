import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import psutil
import pathlib
import time
import re
import hashlib
import logging

# 定义一个MyFrame类，继承自tk.Frame
class MyFrame(tk.Frame):
    # 初始化方法，接收父组件和其他参数
    def __init__(self, parent, **options):
        # 调用父类的初始化方法
        super().__init__(parent, **options)
        # 创建并添加组件到Frame中

# define a menu class
class MyMenu(tk.Menu):
    def __init__(self, master,logger:logging.Logger=None):
        super().__init__(master)
        self.logger = logger
        file_menu = tk.Menu(self, tearoff=0)
        file_menu.add_command(label="Exit", command= self.confirm_exit)
        self.add_cascade(label="File", menu=file_menu)
        edit_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="LogEdit",command=self.logedit)
        help_menu = tk.Menu(self, tearoff=0)
        self.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="help", command=self.help)
    def confirm_exit(self):
        if messagebox.askokcancel("关闭窗口","确定关闭吗？"):
            entry=simpledialog.askstring(title='口令确认：',prompt='请输入口令：')
            if hash(entry) == hash(time.strftime("%Y%m%d%H%M",time.localtime())):
                self.logger.warning('WAT monitor action end by closing windows (SP PW).') if self.logger else 0
                self.master.destroy()
            else:
                mpd_path = pathlib.Path(__file__).parent
                mpd_name = pathlib.Path(__file__).stem
                with open(pathlib.Path(mpd_path,f'password_{mpd_name}.txt'),mode="r") as f:
                    content = f.read()
                    salt = content.split('\n')[0].strip()
                    code = content.split('\n')[1].strip()
                if get_consistent_hash(get_consistent_hash(entry)+salt) == code:
                    self.logger.warning('WAT monitor action end by closing windows.') if self.logger else 0
                    self.master.destroy()
                else:
                    self.logger.warning('Try to close windows.') if self.logger else 0
    def help(self):
        messagebox.showinfo('WAT Process Software','Developed by Engine Xinyu Jia\nE-mail: xinyu.jia@ovt.com\nID: 31235')
    def logedit(self):
        pass
 
# 定义一个主应用类，继承自tk.Tk
class MainApp(tk.Tk):
    # 初始化方法
    def __init__(self,baseName: str,params:dict,logger:list[logging.Logger]=None,start_callback=None, controller=None, **kwargs):
        # 调用父类的初始化方法
        super().__init__(baseName=baseName)
        self.withdraw()
        self.root_path = setPassword(params['_root_path'])
        if self.root_path == None:
            self.destroy()
            return
        self.deiconify()
        self.stringvar1 = tk.StringVar()
        self.stringvar2 = tk.StringVar()
        self.stringvar3 = tk.StringVar()
        self.stringvar1.set(str(pathlib.Path(params['targetFolder'])))
        self.stringvar2.set(str(pathlib.Path(self.root_path,params['label_path'])))
        self.stringvar3.set(str(pathlib.Path(self.root_path,params['map_path'])))
        self.logger = logger
        self.start_callback = start_callback
        self.controller = controller
        # 设置窗口标题和大小
        self.title("WAT APP")
        self.label = tk.Label(self,text='WAT Image Analysis',font=('Arial',20,'bold'))
        self.label.pack(side='top',fill='x',expand=False)
        # 创建并布局Frame对象
        self.frame1 = MyFrame(self)
        self.frame1.pack(side='top', fill="both", expand=False)
        self.label1 = tk.Label(self.frame1,text='WAT image路径(默认不变更): ',font=('Arial',12),width=30,justify=tk.RIGHT)
        self.label1.pack(side='left',fill='x',expand=False,anchor='w')
        self.entry1 = tk.Entry(self.frame1,width=40,textvariable=self.stringvar1)
        self.entry1.pack(side='left',fill='x',expand=False,anchor='w')
        self.button_OK_1 = tk.Button(self.frame1, text='Restore',command = self.set_stringvar, activebackground='gray')
        self.button_OK_1.pack(side='left',fill='x',expand=False,anchor='w')
        
        self.frame1_2 = MyFrame(self)
        self.frame1_2.pack(side='top', fill="both", expand=False)
        self.label2 = tk.Label(self.frame1_2,text='WAT Barcode输出路径(默认不变更): ',font=('Arial',12),width=30,justify=tk.RIGHT)
        self.label2.pack(side='left',fill='x',expand=False)
        self.entry2 = tk.Entry(self.frame1_2,width=40,textvariable=self.stringvar2)
        self.entry2.pack(side='left',fill='x',expand=False)
        self.button_OK_2 = tk.Button(self.frame1_2, text='Restore',command = self.set_stringvar, activebackground='gray')
        self.button_OK_2.pack(side='left',fill='x',expand=False,anchor='w')
        
        self.frame1_3 = MyFrame(self)
        self.frame1_3.pack(side='top', fill="both", expand=False)
        self.label2 = tk.Label(self.frame1_3,text='WAT Map输出路径(默认不变更): ',font=('Arial',12),width=30,justify=tk.RIGHT)
        self.label2.pack(side='left',fill='x',expand=False)
        self.entry2 = tk.Entry(self.frame1_3,width=40,textvariable=self.stringvar3)
        self.entry2.pack(side='left',fill='x',expand=False)
        self.button_OK_2 = tk.Button(self.frame1_3, text='Restore',command = self.set_stringvar, activebackground='gray')
        self.button_OK_2.pack(side='left',fill='x',expand=False,anchor='w')
        
        self.frame3 = MyFrame(self,height=30)
        self.frame3.pack(side='top', fill="both", expand=False)
        self.button_OK1 = tk.Button(self.frame3, text='Start',command = self.action_start, activebackground='gray')
        self.button_OK2 = tk.Button(self.frame3, text='End',command = self.action_end, activebackground='gray')   #SystemButtonFace
        self.button_OK1.pack(side=tk.LEFT,padx=(190,180))
        self.button_OK2.pack(side=tk.LEFT,padx=20)
        
        self.frame4 = MyFrame(self)
        self.frame4.pack(side='top', fill="both", expand=False)
        s2 = tk.Scrollbar(self.frame4)
        #b2 = tk.Scrollbar(self.frame4,orient='horizontal')
        s2.pack(side='right',fill='y')
        #b2.pack(side='bottom',fill='x')
        
        self.streamHandlerBox = LoggerBox(self.frame4,maxline=9999,borderwidth=1, relief=tk.RIDGE)
        self.streamHandlerBox.pack(fill='y',expand=True)
        s2.config(command=self.streamHandlerBox.yview)
        self.streamHandlerBox.config(yscrollcommand=s2.set)
        #b2.config(command=streamHandlerBox.xview)
        # 配置 StreamHandler
        if self.logger:
            sh = logging.StreamHandler(self.streamHandlerBox)
            formator = logging.Formatter(fmt="%(asctime)s|%(filename)s|%(levelname)s|%(message)s")    # 日志格式器
            sh.setFormatter(formator)
            for i in self.logger:
                i.addHandler(sh)
            self.my_menu = MyMenu(self,self.logger[0])
        else:
            self.my_menu = MyMenu(self)
        self.config(menu=self.my_menu)
        self.protocol("WM_DELETE_WINDOW",self.my_menu.confirm_exit)  # 退出提示     
        self.set_gui_size()
        self.run = False
        self.status = False
    
    def set_my_menu(self):
        if self.logger:
            sh = logging.StreamHandler(self.streamHandlerBox)
            formator = logging.Formatter(fmt="%(asctime)s|%(filename)s|%(levelname)s|%(message)s")    # 日志格式器
            sh.setFormatter(formator)
            for i in self.logger:
                i.addHandler(sh)
            self.my_menu = MyMenu(self,self.logger[0])
            self.config(menu=self.my_menu)
            self.protocol("WM_DELETE_WINDOW",self.my_menu.confirm_exit)  # 重新绑定
    
    def set_gui_size(self):
        screenWidth = self.winfo_screenwidth()  #获取显示区域宽度
        screenHeigh = self.winfo_screenheight() #获取显示区域高度
        rootwidth = 600 
        rootheight = 500
        left = (screenWidth-rootwidth)/2
        top = (screenHeigh-rootheight)/2
        self.geometry('%dx%d+%d+%d'%(rootwidth,rootheight,left,top))    #宽度x高度+x偏移+y偏移
        self.update_idletasks()
        min_width = self.winfo_reqwidth()
        min_height = self.winfo_reqheight()
        self.minsize(min_width, min_height)
        self.maxsize(min_width+100, min_height+100)
    
    def action_start(self):
        if self.run:
            return
        targetFolder = self.stringvar1.get().replace('"','')
        outputpath_label = self.stringvar2.get().replace('"','')
        outputpath_map = self.stringvar3.get().replace('"','')
        self.run = True
        #self.start_callback(targetFolder,outputpath_label,outputpath_map,self.run)
        result = self.controller.start_watchdog(targetFolder,outputpath_label,outputpath_map,self.run)
        if result == 0:
            self.run = False
            messagebox.showerror('Wrong path',f'Please check: \n{outputpath_label}\n{outputpath_map}')
        else:
            self.status = self.controller.status
        #self.operate_button(self.button_OK1,operate='start')
        
    def action_end(self):
        self.run = False
        self.controller.stop_watchdog(self.run)
        #self.operate_button(self.button_OK1,operate='end')
        
    def set_stringvar(self):
        pass
    def change_button_color(self,button,color1:str='green',color2:str='red'):
        if self.run:
            if self.status: 
                button['bg'] = color1
                return color1
            else:
                button['bg'] = color2
                return color2
        else:
            button['bg'] = 'SystemButtonFace'
            return 'SystemButtonFace'
    def operate_button(self,button,operate):
        bgc = self.change_button_color(button)
        button.config(activebackground=bgc)
        if operate == 'start':
            button.config(relief=tk.SUNKEN)
        elif operate == 'end':
            button.config(relief=tk.RAISED)
    
# 控制台输出    https://blog.csdn.net/bigcarp/article/details/123428577
class LoggerBox(tk.Text):
    def __init__(self,master=None,maxline=9999,**kwargs):
        super().__init__(master,**kwargs)
        self.maxline = maxline
    def write(self,message):
        self.insert('end',message)
        self.see(tk.END)
        lines = int(self.index('end-1c').split('.')[0])
        if lines > self.maxline:
            self.delete('1.0','2.0')
        self.update()
        
    def flush(self):
        pass
         
def get_consistent_hash(input_string,salt=None):
    # 创建一个 SHA-256 哈希对象
    hash_object = hashlib.sha256()
    # 将输入字符串编码为字节串并更新哈希对象
    if salt == None:
        salt = "JXY31235"
    hash_object.update(str(str(salt)+str(input_string)).encode('utf-8'))
    # 获取十六进制表示的哈希值
    return hash_object.hexdigest()
def check_pid(filename):
    PID_name = pathlib.Path(filename).stem
    PID_name = PID_name+'.exe'
    n = 0
    for pid in psutil.process_iter():
        if pid.name() == PID_name and pid.status()=='running':
            n += 1
            print(pid.name(),pid.status())
            if n>1:
                return pid
    return None
def setPassword(_root_path:dict[str:str]):
    mpd_path = pathlib.Path(__file__).parent
    mpd_name = pathlib.Path(__file__).stem
    result = messagebox.askquestion("请选择公司: ","OSC请选择是, \nSX请选择否。")
    if result == 'yes':
        root_path = _root_path['OSC']
    else:
        root_path = _root_path['SX']
    while True:
        entry=simpledialog.askstring(title='口令设置：',prompt='请输入口令(长度大于等于5位, 仅限数字、字母): ')
        if entry != None:
            x = len(entry)
            if x < 5:
                continue
            else:
                p = '^[0-9a-zA-Z]{5,%s}$' % x
                p = re.compile(p)
                if re.match(p,entry) != None:
                    salt = get_consistent_hash(int(time.time()))
                    code = get_consistent_hash(get_consistent_hash(entry)+salt)
                    del entry
                    with open(pathlib.Path(mpd_path,f'password_{mpd_name}.txt'),mode="w") as f:
                        f.write(str(salt)+'\n'+str(code))
                    return root_path
        else:
            return None

def start_app():
    _root_path = {"SX":r'\\10.162.2.50\sx_eng_data\rwfabdata',"OSC":r"\\172.34.12.5\rwfabdata"}
    # 创建主应用对象
    app = MainApp(baseName='JXY')
    app.withdraw()
    if check_pid(__file__) != None:
        messagebox.showerror('Wrong','程序已经在运行。')
        sys.exit(0)
    else:
        #messagebox.showinfo('Right','Program start.')
        app.withdraw()
        root_path=setPassword(_root_path)
        if root_path == None:
            app.destroy()
        else:
            app.deiconify()
    # 启动主循环
    app.mainloop()

if __name__ == '__main__':
    start_app()
