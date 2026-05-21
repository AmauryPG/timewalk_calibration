from SiPM_CALIBRATION_LIB import *
import os

def get_all_files_in_folder(directory_path):
    """
    Retrieves a list of all files within a given directory and its subdirectories.

    Args:
        directory_path (str): The path to the directory to search.

    Returns:
        list: A list of strings, where each string is the full path to a file.
    """
    file_list = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            if(file.endswith('.bin')):
                file_list.append(os.path.join(root, file).replace("\\", "/"))
    return file_list
    
if __name__ == "__main__":
    absolutePath = ["E:/amaury/dataWeeroc/MatriceMeasurements_Hamamatsu_59.5", 
    "E:/amaury/dataWeeroc/MatriceMeasurements_Hamamatsu_59small",
    "E:/amaury/dataWeeroc/MatriceMeasurements_Hamamatsu_58.5",
    "E:/amaury/dataWeeroc/MatriceMeasurements_Hamamatsu_59"]
    c_handler = SiPM_CALIBRATION_LIB(3, "E:/data_amaury", "lib_TOF_CT.dll")
    
    files =[]
    
    for path in absolutePath:
        temp = get_all_files_in_folder(absolutePath[0])
        for t in temp:
            files.append(t)
    
    c_handler.createAllWorkers()
    
    for file in files:
        print(f"Sending file into C++ queue : {file}")
        c_handler.pushJob(file)
        
    c_handler.waitAllJobsDone()