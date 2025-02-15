import arcpy
import pandas as pd
import os

def process_icesat_with_dem_arcpy(dem_file, icesat_txt):
    """
    根据 DEM 文件的真实空间范围，将 ICESat 数据中的经纬度转换到 DEM 的归一化坐标系（[-1, 1]）下，
    并将转换后的 norm_lon、norm_lat 两列直接添加到原 txt 文件中（文件原本无表头，
    第一列为经度，第二列为纬度，第三列为高程）。
    
    如果 norm_lon 和 norm_lat 字段已存在，则直接更新其值，而不是新建字段。
    
    参数：
      dem_file: DEM 文件路径（例如 'dem.tif'），使用 arcpy 获取空间范围
      icesat_txt: 存储 ICESat 数据的 txt 文件路径（无表头，逗号分隔）

    返回：
      若文件为空，则返回 None，否则返回更新后的 DataFrame 对象
    """
    # -------------------------------
    # **Step 0: 检查 txt 文件是否为空**
    if not os.path.exists(icesat_txt) or os.stat(icesat_txt).st_size == 0:
        arcpy.AddMessage(f"ICESat 文件 {icesat_txt} 为空，跳过处理。")
        return None

    # -------------------------------
    # Step 1: 获取 DEM 的真实空间范围
    desc = arcpy.Describe(dem_file)
    extent = desc.extent
    lon_min, lon_max = extent.XMin, extent.XMax
    lat_min, lat_max = extent.YMin, extent.YMax
    arcpy.AddMessage(f"DEM 经度范围: {lon_min} ~ {lon_max}")
    arcpy.AddMessage(f"DEM 纬度范围: {lat_min} ~ {lat_max}")
    
    # -------------------------------
    # Step 2: 读取 ICESat txt 文件，并确保数据格式正确
    df = pd.read_csv(icesat_txt, header=None, delimiter=',', skipinitialspace=True)

    # **检查数据是否符合格式**
    if df.shape[1] < 3:
        raise ValueError(f"ICESat TXT 文件 {icesat_txt} 格式错误，至少需要包含 (lon, lat, elev) 三列数据")

    # **删除空行**
    df = df.replace('', float('nan')).dropna()

    # **转换数据类型**
    df.iloc[:, :3] = df.iloc[:, :3].astype(float)

    # **定义表头**
    col_names = ['lon', 'lat', 'elev']
    
    # **如果已有 norm_lon 和 norm_lat，则保留**
    if df.shape[1] >= 5:
        col_names += ['norm_lon', 'norm_lat']
    
    df.columns = col_names

    # -------------------------------
    # Step 3: 计算归一化坐标
    norm_lon = (df['lon'] - lon_min) / (lon_max - lon_min) * 2 - 1
    norm_lat = (df['lat'] - lat_min) / (lat_max - lat_min) * 2 - 1

    if 'norm_lon' in df.columns and 'norm_lat' in df.columns:
        df['norm_lon'] = norm_lon
        df['norm_lat'] = norm_lat
    else:
        df.insert(len(df.columns), 'norm_lon', norm_lon)
        df.insert(len(df.columns), 'norm_lat', norm_lat)

    # -------------------------------
    # Step 4: 将更新后的 DataFrame 写回原 txt 文件（覆盖写入，并保持原格式）
    df.to_csv(icesat_txt, index=False, header=False, float_format="%.6f")
    arcpy.AddMessage(f"转换后的数据已写回到: {icesat_txt}")
    
    return df




# 示例调用：
# dem_file = r"C:\path\to\dem.tif"
# icesat_txt = r"C:\path\to\icesat.txt"
# df_result = process_icesat_with_dem_arcpy(dem_file, icesat_txt)

# 示例调用
# dem_file = 'dem.tif'
# icesat_txt = 'icesat.txt'
# df_result = process_icesat_with_dem(dem_file, icesat_txt)


#示例调用
demfolder = r"D:\青藏高原地形超分\青藏高原\data_ice\Train\DEM"
icefolder = r"D:\青藏高原地形超分\青藏高原\data_ice\Train\Icesat_txt"
for i in range(10):
   temp_demfolder = demfolder + "\\" + str(i)
   temp_icefolder = icefolder + "\\" + str(i)
   for filename in os.listdir(temp_demfolder):
        if filename.endswith(".tif"):
            name = filename.split(".tif")[0]
            dem_file= os.path.join(temp_demfolder, filename)
            icesat_txt = os.path.join(temp_icefolder, name + ".txt")
            df_result = process_icesat_with_dem_arcpy(dem_file, icesat_txt)


