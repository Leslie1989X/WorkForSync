import cv2
from pyzbar import pyzbar

__all__ = ['sr_img','algorithm','algoname']
algorithm = {"edsr":"D:\\OmniVision\\RW\\VScodeProject\\project_for_barcodeRecognition\\super_resolution\\EDSR_Tensorflow\\models\\EDSR_x{}.pb",
             "espcn":"D:\\OmniVision\\RW\\VScodeProject\\project_for_barcodeRecognition\\super_resolution\\TF-ESPCN\\export\\ESPCN_x{}.pb",
             "lapsrn":"D:\\OmniVision\\RW\\VScodeProject\\project_for_barcodeRecognition\\super_resolution\\TF-LapSRN\\export\\LapSRN_x{}.pb"}
algoname = ["edsr","espcn","lapsrn"]
def sr_img(img_path: str,algoname: str,algorithm: dict[str,str],scale=2):
    sr = cv2.dnn_superres.DnnSuperResImpl.create()
    sr.readModel(algorithm[algoname].replace('{}',str(scale)))
    
    sr.setModel(algoname, scale)
    print(sr.getAlgorithm())
    img = cv2.imread(img_path) if isinstance(img_path,str) else img_path
    result = sr.upsample(img)
    return result
    cv2.namedWindow("result", cv2.WINDOW_NORMAL)
    cv2.imshow("result", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_img = r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\NeedReadBarCode\testResult\20241214\tiff\A301-AP4K642.00-422.tiff"
    test_img = r"D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\Wrong_rec\AP40173.00\A341-AP40173.00-428.png"
    test_out = r'D:\OmniVision\RW\VScodeProject\project_for_barcodeRecognition\Data\Wrong_rec\AP40173.00'
    #test_img = input('Input the path of the image: ').replace('"','')
    sr_result = sr_img(test_img,algoname[0],algorithm,scale=4)
    cv2.imwrite(test_out + f'/{algoname[0]}_result.png',sr_result,[cv2.IMWRITE_PNG_COMPRESSION,1])
    pyt_result = pyzbar.decode(sr_result)
    print(pyt_result)
