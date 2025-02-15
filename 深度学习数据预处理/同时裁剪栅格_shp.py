import os
import glob
import numpy as np
from osgeo import gdal
import arcpy

def clipgeotiff(inputPath, saveTifPath, saveTxtPath, saveShpPath, patchSize, patchIntersection, startCol, startRow, typeName, index, shpPath, To8bit=False, isSlope=False, isDEM=False, outputShp=False):
    os.makedirs(saveTifPath, exist_ok=True)
    os.makedirs(saveTxtPath, exist_ok=True)
    if outputShp:
        os.makedirs(saveShpPath, exist_ok=True)

    from_names = glob.glob(os.path.join(inputPath, "*.tif"))
    shp_points = read_shapefile_arcpy(shpPath)

    stride = patchSize - int((patchSize - patchIntersection) / 2)
    
    for filePath in from_names:
        inputData, oriPara, nodatavalue = readtiff2array(filePath)  # 设置输入参数
        offsetCor = [startRow, startCol]
        while offsetCor[1] <= inputData.shape[1] - patchSize:
            while offsetCor[0] <= inputData.shape[0] - patchSize:
                filename = f"{typeName}{index}_{offsetCor[1]}_{offsetCor[0]}"
                saveTifName = os.path.join(saveTifPath, filename + ".tif")
                saveTxtName = os.path.join(saveTxtPath, filename + ".txt")

                cliptopatch(inputData, oriPara[2], oriPara[3], saveTifName, offsetCor, patchSize, nodatavalue)
                save_shp_points_in_patch(shp_points, oriPara[2], saveTxtName, offsetCor, patchSize)

                # 输出 SHP 文件
                if outputShp:
                    saveShpName = os.path.join(saveShpPath, f"{filename}.shp")
                    save_shp_points_in_patch_as_shp(shp_points, oriPara[2], saveShpName, offsetCor, patchSize)

                offsetCor[0] += stride
            offsetCor[1] += stride
            offsetCor[0] = 0
        index += 1

def save_shp_points_in_patch_as_shp(shp_points, ori_geoTrans, saveShpName, offsetCor, patchSize):
    x_min = ori_geoTrans[0] + offsetCor[1] * ori_geoTrans[1]
    x_max = x_min + patchSize * ori_geoTrans[1]
    y_max = ori_geoTrans[3] + offsetCor[0] * ori_geoTrans[5]
    y_min = y_max + patchSize * ori_geoTrans[5]

    # 使用 arcpy 写入 SHP 文件
    if arcpy.Exists(saveShpName):
        arcpy.Delete_management(saveShpName)

    # 创建一个空的点要素类，并添加字段
    arcpy.CreateFeatureclass_management(os.path.dirname(saveShpName), os.path.basename(saveShpName), "POINT", spatial_reference=arcpy.SpatialReference(4326))
    
    # 在 SHP 文件中添加字段 'ele'，该字段保存地形高程值
    arcpy.AddField_management(saveShpName, "ele", "DOUBLE")

    cursor = arcpy.da.InsertCursor(saveShpName, ["SHAPE@", "ele"])

    for lon, lat, ele in shp_points:
        if x_min <= lon < x_max and y_min <= lat < y_max:
            point = arcpy.Point(lon, lat)
            cursor.insertRow([point, ele])

    del cursor

def read_shapefile_arcpy(shpPath):
    """ 使用 arcpy 读取 SHP 文件中的点数据 """
    points = []
    with arcpy.da.SearchCursor(shpPath, ["SHAPE@X", "SHAPE@Y", "ele"]) as cursor:
        for row in cursor:
            points.append((row[0], row[1], row[2]))
    return points

def save_shp_points_in_patch(shp_points, ori_geoTrans, saveTxtName, offsetCor, patchSize):
    x_min = ori_geoTrans[0] + offsetCor[1] * ori_geoTrans[1]
    x_max = x_min + patchSize * ori_geoTrans[1]
    y_max = ori_geoTrans[3] + offsetCor[0] * ori_geoTrans[5]
    y_min = y_max + patchSize * ori_geoTrans[5]

    with open(saveTxtName, "w") as f:
        for lon, lat, ele in shp_points:
            if x_min <= lon < x_max and y_min <= lat < y_max:
                f.write(f"{lon}, {lat}, {ele}\n")

def cliptopatch(inputData, ori_geoTrans, ori_geoPro, saveName, offsetCor, patchSize, nodatavalue):
    if not os.path.exists(saveName):
        ori_Datatype = inputData.dtype
        in_bands = inputData.shape[2] if len(inputData.shape) == 3 else 1
        out_band = np.zeros([patchSize, patchSize, in_bands], ori_Datatype)

        for i in range(in_bands):
            out_band[:, :, i] = inputData[offsetCor[0]:offsetCor[0] + patchSize, offsetCor[1]:offsetCor[1] + patchSize, i]
            out_band[:, :, i] = np.where(out_band[:, :, i] == nodatavalue, -1, out_band[:, :, i])

        dst_transform = calculateTransform(ori_geoTrans, offsetCor[1], offsetCor[0])
        newDataType = gdal.GDT_Byte if 'int8' in out_band.dtype.name else (gdal.GDT_UInt16 if 'int16' in out_band.dtype.name else gdal.GDT_Float32)

        driver = gdal.GetDriverByName("GTiff")
        if not np.any(out_band[:, :, i] == -1):
            dataset = driver.Create(saveName, patchSize, patchSize, in_bands, newDataType)
            if dataset:
                dataset.SetGeoTransform(dst_transform)
                dataset.SetProjection(ori_geoPro)
                for i in range(in_bands):
                    dataset.GetRasterBand(i + 1).WriteArray(out_band[:, :, i])
            del dataset

def readtiff2array(oriPath):
    in_ds = gdal.Open(oriPath)
    row, col, band = in_ds.RasterYSize, in_ds.RasterXSize, in_ds.RasterCount
    geoTrans, geoPro = in_ds.GetGeoTransform(), in_ds.GetProjection()
    nodatavalue = in_ds.GetRasterBand(1).GetNoDataValue()
    
    datatype_index = in_ds.GetRasterBand(1).DataType
    datatype = gdal.GetDataTypeName(datatype_index)
    newDataType = 'int8' if 'GDT_Byte' in datatype else ('int16' if 'GDT_UInt16' in datatype else 'float32')

    data = np.zeros([row, col, band], newDataType)
    for i in range(band):
        data[:, :, i] = in_ds.GetRasterBand(i + 1).ReadAsArray(0, 0, col, row)
    
    del in_ds
    return data, [band, datatype, geoTrans, geoPro], nodatavalue

def calculateTransform(ori_transform, offsetX, offsetY):
    top_left_x = ori_transform[0] + offsetX * ori_transform[1]
    top_left_y = ori_transform[3] + offsetY * ori_transform[5]
    return (top_left_x, ori_transform[1], ori_transform[2], top_left_y, ori_transform[4], ori_transform[5])

ShpFolder = r"D:\青藏高原地形超分\青藏高原\范围\Shp_Clip"
TxtFolder = r"D:\青藏高原地形超分\青藏高原\范围\Txt"
DEMFolder = r"D:\青藏高原地形超分\青藏高原\范围\AsterDEM"
ClipDEMFolder = r"D:\青藏高原地形超分\青藏高原\范围\Clip_DEM"
PointFolder = r"D:\青藏高原地形超分\青藏高原\范围\采样点"

for i in range(10):
    inputPath = DEMFolder + "\\" + str(i)  # 输入 TIFF 影像的文件夹路径
    saveTifPath = ClipDEMFolder + "\\" + str(i)  # 存放裁剪后 TIFF 的文件夹
    saveTxtPath = TxtFolder + "\\" + str(i)   # 存放裁剪后 TXT 的文件夹
    saveShpPath = ShpFolder + "\\" + str(i)  # 裁剪后的 SHP 文件保存路径
    shpPath = PointFolder + "\\" + str(i) + ".shp"  # 点 shapefile 的路径
    patchSize = 60  # 每个裁剪块的大小
    patchIntersection = 60  # 裁剪块之间的重叠区域大小
    startCol = 0  # 开始列位置
    startRow = 0  # 开始行位置
    typeName = "patch"  # 裁剪块的文件名前缀
    index = 0  # 裁剪块索引
    outputShp = True  # 是否输出 SHP 文件

    # 调用函数进行裁剪
    clipgeotiff(inputPath, saveTifPath, saveTxtPath, saveShpPath, patchSize, patchIntersection, startCol, startRow, typeName, index, shpPath, outputShp=outputShp)