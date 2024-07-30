import os
def get_file_name_and_path(file_path):
    # 获取文件名
    file_name = os.path.basename(file_path)
    # 获取文件路径
    file_directory = os.path.dirname(file_path)
    return file_name, file_directory