import time
import configparser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import pathlib

class ConfigChangeHandler(FileSystemEventHandler):
    def __init__(self, config_path,config_file):
        super().__init__()
        self.config_path = config_path
        self.config_file = config_file
        self.last_config = self.load_config()

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        return config

    def on_modified(self, event):
        if event.src_path == self.config_file:
        #if not event.is_directory:
            self.config_file = event.src_path
            print("Config file modified, checking for changes...")
            new_config = self.load_config()

            for section in new_config.sections():
                if section not in self.last_config:
                    print(f"New section added: [{section}]")
                else:
                    for option in new_config[section]:
                        if option not in self.last_config[section]:
                            print(f"New option added: [{section}] {option} = {new_config[section][option]}")
                        elif new_config[section][option] != self.last_config[section][option]:
                            print(f"Value changed: [{section}] {option}:")
                            print(f"  old: {self.last_config[section][option]}")
                            print(f"  new: {new_config[section][option]}")

            self.last_config = new_config

if __name__ == "__main__":
    # 配置文件路径
    config_path = r"E:\CodeProject\VSCodeProjects\My_Projects\work_data\monitorINI" # 待监控的
    config_file = r"E:\CodeProject\VSCodeProjects\My_Projects\work_data\monitorINI\AlignmentData.ini"
    print(config_path)
    # 监控配置文件变化
    observer = Observer()
    event_handler = ConfigChangeHandler(config_path,config_file)
    observer.schedule(event_handler, path=config_path, recursive=False) # recursive: bool. True: dir_tree, False: dir_only
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
