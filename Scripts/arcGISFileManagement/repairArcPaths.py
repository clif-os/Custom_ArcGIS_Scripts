# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: This script repairs all broken data links of MXDs within a project folder given :
# 1) the links were broken by a movement of the project folder (and not movement of data within that folder),
# 2) and that all referenced data is contained within that same project folder

import arcpy, os

def findLastSlug(path):
    if path.endswith("\\"):
        path = path[:len(path)-1]
    indexRoll = -1
    idx = 0
    while indexRoll > -len(path):
        if path[indexRoll] == "\\":
            idx = indexRoll
            break
        indexRoll -= 1
    return idx

def determineWorkspace(lyrObj):
    if lyrObj.dataSource.endswith(".gdb"):
        dataType = 'FILEGDB_WORKSPACE'
    elif lyrObj.dataSource.endswith(".mdb"):
        dataType = 'ACCESS_WORKSPACE'

    elif lyrObj.dataSource.endswith(".shp"):
        dataType = 'SHAPEFILE_WORKSPACE'
    elif lyrObj.isRasterLayer:
        dataType = 'RASTER_WORKSPACE'
    # elif row['DataType'] == 'CoverageFeatureClass':
    #    dataType = 'ARCINFO_WORKSPACE'
    # elif row['DataType'] == 'Table' and ".gdb" not in newSource:
    # dataType = 'EXCEL_WORKSPACE'
    else:
        dataType = 'NONE'
    return dataType


pathMaps = raw_input("Please enter the path name to project folder "
                     "containing ArcMap MXD files you'd like to repair : ")
projFolder = pathMaps[findLastSlug(pathMaps)+1:]
projLocation = pathMaps[:findLastSlug(pathMaps)]

countMxd = 0
for root, dirs, files in os.walk(pathMaps):
    for fileName in files:
        basename, extension = os.path.splitext(fileName)
        if extension == ".mxd":
            countLyr = 1
            arcpy.AddMessage(fileName)
            fullPath = os.path.join(root, fileName)
            mxd = arcpy.mapping.MapDocument(fullPath)
            for lyr in arcpy.mapping.ListLayers(mxd):
                arcpy.AddMessage("Layer name : " + str(lyr))
                if lyr.isBroken == False:
                    arcpy.AddMessage("Link status : NOT BROKEN")
                elif lyr.isBroken == True:
                    arcpy.AddMessage("Link status : BROKEN")
                    arcpy.AddMessage("Original layer path : " + lyr.dataSource)
                    # separate/identify filename and new folder name:
                    index = findLastSlug(lyr.dataSource)
                    filename = lyr.dataSource[index+1:]
                    indexFolder = len(lyr.dataSource) + index
                    pathFolderOld = lyr.dataSource[:indexFolder]
                    projectPath = pathFolderOld[pathFolderOld.find(projFolder):]
                    pathFolderNew = projLocation + "\\" + projectPath
                    arcpy.AddMessage("Filename : " + filename)
                    arcpy.AddMessage("New folder location : " + pathFolderNew)
                    # find layer workspace:
                    dataType = determineWorkspace(lyr)
                    arcpy.AddMessage("Layer workspace : " + dataType)
                    try:
                        lyr.replaceDataSource(pathFolderNew, dataType, filename, False)
                        arcpy.AddMessage("Data Source Replaced")
                    except:
                        arcpy.AddMessage("Unable to Replace Data Source!!")

                arcpy.AddMessage("--------DONE WITH LYR "+str(countLyr)+"--------\n")
                countLyr += 1
            countMxd += 1
            mxd.save()
            arcpy.AddMessage("-------------DONE WITH MXD "+str(countMxd)+"-------------\n")

# sources of info on working with layer object and repairing layer data links:
# http://gis.stackexchange.com/questions/19059/use-arcpy-mapping-to-list-broken-data-layers
# http://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy-mapping/layer-class.htm
# http://gis.stackexchange.com/questions/32915/repairing-data-sources-in-multiple-mxds-using-arcpy
# can also pull workspace type prior to breaking : http://support.esri.com/technical-article/000011590
# --> arcpy.AddMessage(arcpy.Describe(pathLayer))