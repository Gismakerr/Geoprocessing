import os
import glob
import numpy as np
from osgeo import gdal

def readtiff2array(oriPath):
    in_ds = gdal.Open(oriPath)
    print(f"打开影像文件: {oriPath}")

    row = in_ds.RasterYSize  
    col = in_ds.RasterXSize  
    band = in_ds.RasterCount  
    geoTrans = in_ds.GetGeoTransform()
    geoPro = in_ds.GetProjection()
    nodatavalue = in_ds.GetRasterBand(1).GetNoDataValue()

    datatype_index = in_ds.GetRasterBand(1).DataType
    datatype = gdal.GetDataTypeName(datatype_index)

    if 'GDT_Byte' in datatype:
        newDataType = 'int8'
    elif 'GDT_UInt16' in datatype:
        newDataType = 'int16'
    else:
        newDataType = 'float32'

    data = np.zeros([row, col, band], dtype=newDataType)  

    for i in range(band):
        dt = in_ds.GetRasterBand(i + 1)
        data[:, :, i] = dt.ReadAsArray(0, 0, col, row)

    del in_ds
    return data, [band, datatype, geoTrans, geoPro], nodatavalue

def generate_label(lon, lat):
    """ 生成N1223E0356格式的标签 """
    lon_abs = abs(lon)
    lat_abs = abs(lat)

    lon_prefix = 'E' if lon >= 0 else 'W'
    lat_prefix = 'N' if lat >= 0 else 'S'

    lon_str = f"{lon_prefix}{int(lon_abs * 10):04d}"
    lat_str = f"{lat_prefix}{int(lat_abs * 10):04d}"

    return f"{lat_str}{lon_str}"

def calculateTransform(ori_transform, offsetX, offsetY):
    top_left_x = ori_transform[0]  
    w_e_pixel_resolution = ori_transform[1]  
    top_left_y = ori_transform[3]  
    n_s_pixel_resolution = ori_transform[5]  

    top_left_x = top_left_x + offsetX * w_e_pixel_resolution
    top_left_y = top_left_y + offsetY * n_s_pixel_resolution

    dst_transform = (top_left_x, ori_transform[1], ori_transform[2], top_left_y, ori_transform[4], ori_transform[5])
    return dst_transform  

def cliptopatch1(inputData, ori_geoTrans, ori_geoPro, savePath, offsetCor, patchSize, nodatavalue, decimal_places):
    ori_Datatype = inputData.dtype
    in_bands = inputData.shape[2] if len(inputData.shape) == 3 else 1
    out_band = np.zeros([patchSize, patchSize, in_bands], dtype=ori_Datatype)

    for i in range(in_bands):
        out_band[:, :, i] = inputData[offsetCor[0]:offsetCor[0] + patchSize, offsetCor[1]:offsetCor[1] + patchSize, i]
        out_band[:, :, i] = np.where(out_band[:, :, i] == nodatavalue, -1, out_band[:, :, i])

    dst_transform = calculateTransform(ori_geoTrans, offsetCor[1], offsetCor[0])

    if 'int8' in out_band.dtype.name:
        newDataType = gdal.GDT_Byte
    elif 'int16' in out_band.dtype.name:
        newDataType = gdal.GDT_UInt16
    else:
        newDataType = gdal.GDT_Float32

    # 计算左下角坐标，生成文件名
    left_bottom_x = round(dst_transform[0], decimal_places)
    left_bottom_y = round(dst_transform[3] + patchSize * dst_transform[5], decimal_places)
    filename = f"{generate_label(left_bottom_x, left_bottom_y)}.tif"
    saveName = os.path.join(savePath, filename)

    driver = gdal.GetDriverByName("GTiff")
    dataset = driver.Create(saveName, patchSize, patchSize, in_bands, newDataType)

    if dataset:
        dataset.SetGeoTransform(dst_transform)  
        dataset.SetProjection(ori_geoPro)  
        for i in range(in_bands):
            dataset.GetRasterBand(i + 1).WriteArray(out_band[:, :, i])
        del dataset

    print(f"裁剪文件: {saveName}, 左下角坐标: ({left_bottom_x}, {left_bottom_y})")
    return filename  # 返回文件名

def clipgeotiff(inputPath, savePath, patchSize, patchIntersection, startCol, startRow, decimal_places=1):
    os.makedirs(savePath, exist_ok=True)
    from_names = glob.glob(os.path.join(inputPath, "*.tif"))

    stride = patchSize - int((patchSize - patchIntersection) / 2)

    for filePath in from_names:
        print(f"处理文件: {filePath}")
        inputData, oriPara, nodatavalue = readtiff2array(filePath)

        offsetCor = [startRow, startCol]
        while offsetCor[1] <= inputData.shape[1] - patchSize:
            while offsetCor[0] <= inputData.shape[0] - patchSize:
                cliptopatch1(inputData, oriPara[2], oriPara[3], savePath, offsetCor, patchSize, nodatavalue, decimal_places)
                offsetCor[0] += stride
            offsetCor[1] += stride
            offsetCor[0] = 0  

# 参数设置
inputPath = r"D:\元迁移学习\实验\Data\附加DEM\丘陵"
savePath = r"D:\元迁移学习\实验\Data\附加DEM\Clip_500\Hill\Hill"
patchSize = 360
patchIntersection = 360
startCol = 0
startRow = 0
decimal_places = 1  # 设定保留小数位数

# 运行裁剪函数
clipgeotiff(inputPath, savePath, patchSize, patchIntersection, startCol, startRow, decimal_places)
