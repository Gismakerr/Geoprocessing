import os
import random
import shutil

def generate_index(input_folder, index_file):
    """生成文件索引，提取文件名（不含扩展名），并保存索引"""
    file_names = set()

    # 遍历文件夹，收集不带后缀的文件名
    for file in os.listdir(input_folder):
        name, _ = os.path.splitext(file)
        file_names.add(name)

    # 保存索引
    with open(index_file, "w") as f:
        for name in sorted(file_names):  # 排序保证一致性
            f.write(name + "\n")
    
    print(f"索引文件已生成，共 {len(file_names)} 个文件")


import arcpy

def sample_and_copy(input_folder, train_folder, test_folder, index_file, test_ratio=0.2, seed=42):
    """根据索引文件对数据进行采样，并复制到目标训练/测试集文件夹"""
    random.seed(seed)

    # 读取索引
    with open(index_file, "r") as f:
        file_names = [line.strip() for line in f.readlines()]

    # 进行随机划分
    random.shuffle(file_names)
    test_size = int(len(file_names) * test_ratio)
    test_files = set(file_names[:test_size])
    train_files = set(file_names[test_size:])

    # 确保目标文件夹存在
    os.makedirs(train_folder, exist_ok=True)
    os.makedirs(test_folder, exist_ok=True)

    # 处理文件复制
    for file in os.listdir(input_folder):
        name, ext = os.path.splitext(file)
        src_path = os.path.join(input_folder, file)

        if name in train_files:
            dst_folder = train_folder
        elif name in test_files:
            dst_folder = test_folder
        else:
            continue  # 如果不在索引中，跳过

        dst_path = os.path.join(dst_folder, file)

        if ext.lower() == ".shp":
            # 处理 Shapefile 及其关联文件
            arcpy.env.overwriteOutput = True  # 允许覆盖
            src_shp = os.path.join(input_folder, name + ".shp")
            dst_shp = os.path.join(dst_folder, name + ".shp")
            if arcpy.Exists(src_shp):
                arcpy.CopyFeatures_management(src_shp, dst_folder)
                print(f"Shapefile 复制完成: {src_shp} -> {dst_shp}")
        else:
            # 直接复制其他文件
            shutil.copy(src_path, dst_path)

    print(f"数据集划分完成：训练集 {len(train_files)}，测试集 {len(test_files)}")


# # 示例调用
# input_folder = "path/to/input"
# train_folder = "path/to/train"
# test_folder = "path/to/test"
# index_file = "index.txt"

# # 第一步：生成索引
# generate_index(input_folder, index_file)




# # 第二步：采样并复制
# sample_and_copy(input_folder, train_folder, test_folder, index_file, test_ratio=0.2, seed=42)
shp_folder = r"D:\青藏高原地形超分\青藏高原\范围\Shp_Clip"
txt_folder = r"D:\青藏高原地形超分\青藏高原\范围\Txt"
input_folder = r"D:\青藏高原地形超分\青藏高原\范围\Clip_DEM"
train_folder_dem = r"D:\青藏高原地形超分\青藏高原\data\Train\DEM"
train_folder_shp =  r"D:\青藏高原地形超分\青藏高原\data\Train\Icesat_shp"
train_folder_txt = r"D:\青藏高原地形超分\青藏高原\data\Train\Icesat_txt"

test_folder_dem = r"D:\青藏高原地形超分\青藏高原\data\Test\DEM"
test_folder_shp =  r"D:\青藏高原地形超分\青藏高原\data\Test\Icesat_shp"
test_folder_txt = r"D:\青藏高原地形超分\青藏高原\data\Test\Icesat_txt"


index_folder = "D:\青藏高原地形超分\青藏高原\data\采样索引"
for i in range(10):
    shp = shp_folder + "\\" + str(i)
    txt = txt_folder + "\\" + str(i)
    dem = input_folder + "\\" + str(i)
    
    train_dem = train_folder_dem + "\\" + str(i)
    train_txt = train_folder_txt + "\\" + str(i)
    train_shp = train_folder_shp + "\\" + str(i)
    test_dem = test_folder_dem + "\\" + str(i)
    test_txt = test_folder_txt + "\\" + str(i)
    test_shp = test_folder_shp + "\\" + str(i)
    
    index_file = index_folder + "\\" + str(i) + ".txt"
    generate_index(dem, index_file)
    sample_and_copy(dem, train_dem, test_dem, index_file, test_ratio=0.2, seed=42)
    sample_and_copy(txt, train_txt, test_txt, index_file, test_ratio=0.2, seed=42)
    sample_and_copy(shp, train_shp, test_shp, index_file, test_ratio=0.2, seed=42)
    
    