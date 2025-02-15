import os
import re
import shutil
def group_and_move_tif(source_folder, target_folder):
    """
    按前缀（如 W0, W1, W2）分组 .tif 文件，并移动到目标文件夹下的对应子文件夹。

    :param source_folder: 原始 .tif 文件存储路径
    :param target_folder: 目标存储路径（会在其中创建子文件夹）
    """
    os.makedirs(target_folder, exist_ok=True)  # 确保目标文件夹存在
    
    # 遍历文件夹
    for filename in os.listdir(source_folder):
        if filename.endswith(".tif"):
            # 使用正则匹配类似 W0, W1, W2 的前缀
            match = re.match(r"(W\d+)", filename)
            if match:
                prefix = match.group(1)  # 提取前缀
                prefix_folder = os.path.join(target_folder, prefix)  # 目标子文件夹
                
                os.makedirs(prefix_folder, exist_ok=True)  # 确保子文件夹存在
                
                # 移动文件到相应的子文件夹
                src_path = os.path.join(source_folder, filename)
                dst_path = os.path.join(prefix_folder, filename)
                shutil.move(src_path, dst_path)
                
                print(f"✅ {filename} → {prefix_folder}")

for i in range(10):
    source_folder = r"D:\青藏高原地形超分\青藏高原\范围\AsterDEM_Clip"  # 你的 .tif 文件所在文件夹
    target_folder = source_folder + "\\" + str(i)   # 目标文件夹
    group_and_move_tif(source_folder, target_folder)
    print("🎯 所有 .tif 文件已成功分类并移动！")