import arcpy
import Files as F

def SlopeAcc(DemPath,DirPath,OutputPath,Threshold):
    """
    基于优先满水算法提取河网，再计算以河网为源的坡度累积量
    """
    arcpy.env.overwriteOutput = True
    dir,_ = F.get_file_name_and_path(DirPath)
    dirname = dir.split(".tif")[0]
    dem,_ = F.get_file_name_and_path(DemPath)
    demname = dem.split(".tif")[0]
    #定义投影
    desc = arcpy.Describe(DemPath)
    spatial_reference = desc.spatialReference
    arcpy.DefineProjection_management(DirPath, spatial_reference)
    #计算流量
    acc = OutputPath + "\\acc_" + demname + ".tif"
    out_accumulation_raster = arcpy.sa.FlowAccumulation(DirPath, None, "FLOAT", "D8")
    out_accumulation_raster.save(acc)
    #提取河网
    inRaster = arcpy.Raster(acc)
    stream = OutputPath + "\\Stream_" + str(Threshold) + "_" + demname + ".tif"
    out_raster = arcpy.sa.Con(inRaster > Threshold, 1)
    out_raster.save(stream)
    #栅格河网矢量化
    stream_vector = OutputPath + "\\Drainage_" + str(Threshold) + "_" + demname
    arcpy.sa.StreamToFeature(stream, DirPath, stream_vector, "NO_SIMPLIFY")
    #计算坡度
    slope = OutputPath + "\\slope_" + demname + ".tif"
    out_raster = arcpy.sa.Slope(DemPath, "DEGREE", 1, "PLANAR", "METER")
    out_raster.save(slope)
    #坡度加一个很小的值
    inSlope = arcpy.Raster(slope)
    outSlope = OutputPath + "\\slope1_" + demname + ".tif"
    out_raster = arcpy.sa.Plus(inSlope, 1E-07)
    out_raster.save(outSlope)
    #坡度累积
    slope_acc =  OutputPath + "\\Slope_acc_" + str(Threshold) + "_" + demname + ".tif"
    out_distance_accumulation_raster = arcpy.sa.DistanceAccumulation(stream_vector, None, None, outSlope , None, "BINARY 1 -30 30", None, "BINARY 1 45", None, None, None, None, None, None, '', "PLANAR")
    out_distance_accumulation_raster.save(slope_acc)
    
DemPath = r"E:\CHY\data\dem\600\0.tif"
DirPath = r"D:\proproject\geoprocessing\中间数据1\dir0.tif"
OutputPath = r"D:\proproject\geoprocessing\New Folder"
Threshold = 1200
SlopeAcc(DemPath,DirPath,OutputPath,Threshold)