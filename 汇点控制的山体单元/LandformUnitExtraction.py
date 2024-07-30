import arcpy
import Files as F
def LandfromUnit(DemPath,OutputPath,Buffer_distance):
    """
        提取以反地形地表汇点为倾斜点的山体单元：
        1.计算不填洼DEM的流向
        2.计算sink栅格
        3.sink栅格转汇矢量点
        4.以汇为中心做缓冲区
        5.缓冲区标识汇
        6.以具有标识信息的汇作为倾斜点，计算集水区栅格
        7.集水区栅格转矢量，得到山体单元
    """
    dem,_ = F.get_file_name_and_path(DemPath)
    demname = dem.split(".tif")[0]
    
    #计算不填洼DEM的流向
    dir = OutputPath + "//dir_D8_" + dem
    out_flow_direction_raster = arcpy.sa.FlowDirection(DemPath, "NORMAL", None, "D8")
    out_flow_direction_raster.save(dir)
    #计算sink栅格
    sink = OutputPath + "//sink_" + dem
    out_raster = arcpy.sa.Sink(dir); 
    out_raster.save(sink)
    #sink栅格转汇矢量点
    Hui = OutputPath + "//汇点_" + demname 
    arcpy.conversion.RasterToPoint(sink, Hui, "Value")
    #以汇为中心做缓冲区
    Hui_buffer = OutputPath + "//汇点_Buffer_" + str(Buffer_distance) + demname
    arcpy.analysis.PairwiseBuffer(Hui, Hui_buffer, Buffer_distance, "ALL", None, "PLANAR", "0 Meters")
    #多部件到单部件
    Buffer_single = OutputPath + "//汇点_Buffer_" + str(Buffer_distance) + "_single_" + demname
    arcpy.management.MultipartToSinglepart(Hui_buffer, Buffer_single)
    #计算字段
    arcpy.management.CalculateField(Buffer_single, "ORIG_FID", "!FID!", "PYTHON3", '', "TEXT", "NO_ENFORCE_DOMAINS")
    #缓冲区标识汇
    Pour = OutputPath + "//Pour_" + demname
    arcpy.analysis.Intersect([Hui,Buffer_single], Pour, "ALL", None, "INPUT")
    #以具有标识信息的汇作为倾斜点，计算集水区栅格
    Watershed = OutputPath + "//watershed_" + dem
    out_raster = arcpy.sa.Watershed(dir, Pour, "ORIG_FID")
    out_raster.save(Watershed)
    #集水区栅格转矢量，得到山体单元
    LUnit = OutputPath + "//集水区_" + dem
    arcpy.conversion.RasterToPolygon(Watershed, LUnit, "SIMPLIFY", "Value", "SINGLE_OUTER_PART", None)
    print(LUnit + "已创建")