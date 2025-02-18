import numpy as np
import pathlib
import asyncio
import time
import cv2
import aiofiles
import gc
from Frame_det_cont import dice_det_main,save_maps
from Barcode_detection import get_file

# 限制并发任务数量
batch_size = 20
semaphore = asyncio.Semaphore(batch_size) 

async def async_read_image(file_path):
    async with semaphore:
        # 异步读取文件
        async with aiofiles.open(file_path, mode='rb') as f:
            image_data = await f.read()
        # 将字节数据转换为 NumPy 数组
        image_np = np.frombuffer(image_data, dtype=np.uint8)
        # 使用 OpenCV 解码图像
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        # 图像的检测和处理
        result = await asyncio.to_thread(dice_det_main,image)
        return result

async def test_main(path,output):
    paths = get_file(path,pattern='*.bmp')
    tasks = [async_read_image(file_path) for file_path in paths]
    #results = await asyncio.gather(*tasks,return_exceptions=True)
    # 分批处理任务
    results = []
    for i in range(0, len(tasks), batch_size):
        batch_tasks = tasks[i:i + batch_size]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)
        gc.collect()
    for i , result in enumerate(results):
        if isinstance(result,Exception):
            print(f'Expected error in processing: {str(paths[i])}. Error: {result}')
        if isinstance(result,int):
            print(f'no found circle, -- {str(paths[i].name)} is backlighting image.')
        elif isinstance(result,dict):
            print(f'{str(paths[i].name)} is frontlighting image.')
            print(f"labels: {list(result.keys())}")
        elif isinstance(result[2],np.ndarray):
            print(f'map correct, -- {str(paths[i].name)} is backlighting image.')
            save_maps(result[2],f'{output}/{paths[i].stem}_map.txt')
        elif isinstance(result[2],int):
            print(f'map wrong, -- {str(paths[i].name)} is backlighting image.')

def main_image_process(path:str,output:str):
    result = dice_det_main(path,label_ns = [2])
    if isinstance(result,int):
        print(f'no found circle -- {str(pathlib.Path(path).name)} is backlighting image.')
    elif isinstance(result,dict):
        print(f'{str(pathlib.Path(path).name)} is frontlighting image.')
        print(f"labels: {list(result.keys())}")
    elif isinstance(result[2],np.ndarray):
        print(f'map correct -- {str(pathlib.Path(path).name)} is backlighting image.')
        save_maps(result[2],f'{output}/{pathlib.Path(path).stem}_map.txt')
        cir,contours_info,mapx = result
    elif isinstance(result[2],int):
        print(f'map wrong -- {str(pathlib.Path(path).name)} is backlighting image.')

if __name__ == '__main__':
    path = input('Please input the folder path: ').replace('"','')
    filename = time.strftime('%Y_%m_%d',time.localtime())
    output_path = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\IMG_Black_Normal\output'+"\\"+filename
    pathlib.Path(output_path).mkdir(parents=True,exist_ok=True)
    start = time.time()
    asyncio.run(test_main(path,output_path))
    #main_image_process(path,output_path)
    input(f'total time cost: {round(time.time()-start,4)}s')
