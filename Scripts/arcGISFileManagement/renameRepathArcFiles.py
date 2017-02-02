# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: point to a folder with MXDs and a folder with files references by the MXDs, 
# and rename the referenced files and automatically update the MXDs with the new names 
# in order to not break the file paths

import arcpy, os

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

def grabFileName(filepath):
    filename = filepath[findLastSlug(filepath)+1:]
    return filename

def printDict(dic, selectionSet):
    if selectionSet == "NONE":
        for key, value in dic.items():
            arcpy.AddMessage(str(key) + ": " + value)
    else:
        for key, value in dic.items():
            if key in selectionSet:
                arcpy.AddMessage(str(key) + ": " + value)

#printing-style user-input parser:
def selectionToSet(userinp):
        userinp.replace(" ","")
        nums = set([])
        ranges = userinp.split(",")
        for i in ranges:
                if "-" in i:
                        [min, max] = i.split("-")
                        for j in range(int(min), int(max) + 1):
                                nums.add(j)
                else:
                        nums.add(int(i))
        return nums

#printList might not make it to final list
def printList(list):
    for item in list:
        arcpy.AddMessage(item)

# folder input:
# consider allowing multiple folder inputs
Location = raw_input("\nEnter path to project folder containing files to rename and their relevant MXDs : ")

# build file dictionary
fileID = 1
fileDict = {}
for dirpath, dirnames, filenames in arcpy.da.Walk(Location):
    for file in filenames:
        filepath = dirpath + "\\" +file
        fileDict[fileID]= filepath
        fileID += 1

# build map and map layers dictionary object
mapID = 1
mapDict = {}
for root, dirs, files in os.walk(Location):
    for fileName in files:
        basename, extension = os.path.splitext(fileName)
        if extension == ".mxd":
            lyrID = 1
            lyrDict = {}
            fullPath = os.path.join(root, fileName)
            mxd = arcpy.mapping.MapDocument(fullPath)
            for lyr in arcpy.mapping.ListLayers(mxd):
                try:
                    if lyr.isBroken == False:
                        lyrDict[lyrID] = lyr.dataSource
                        lyrID += 1
                except:
                    arcpy.AddMessage("Layer cataloging failed for '" + str(lyr) + "' within the following MXD : " + fullPath)
            mapDict[mapID] = [fullPath,lyrDict]
            mapID += 1

# allow user to build file seletion:
selectedFiles = set([])
while True:
    # print preview of files in folder
    arcpy.AddMessage("\nFILES QUEUED :\n---------------\nID: FILE_PATH")
    printDict(fileDict, "NONE")
    try:
        selection = raw_input("\nPlease enter FileID's you'd like to parse as '1,3,5-8,10...etc',"
                              "or type 'all': ")
        selection = selection.lower()
        if selection == "all":
            selectedFiles = selectionToSet("1-" + str(len(fileDict)))
        else:
            selectedFiles = selectionToSet(selection)
    except:
        arcpy.AddMessage("WRONG ENTRY; TRY AGAIN")
        continue
    arcpy.AddMessage("\nFILES SELECTED :\n---------------\nID: FILE_PATH")
    printDict(fileDict, selectedFiles)
    satisfy = raw_input("\nIf this selection is satisfactory press 'ENTER', otherwise type 'n' to re-select :")
    if len(satisfy) == 0:
        break
    else:
        continue

#create an internal selection set of MXD's containing previously selected layers
def returnMXDsWithLayer(path):
    maps = set([])
    for mapKey, layerDict in mapDict.items():
        for layerKey, layerPath in layerDict[1].items():
            if path == layerPath:
                maps.add(mapKey)
    return maps

# batch renaming:
def createNewPathBatch(oldPath, pathAppend):
    newPath = oldPath
    fileIndex = findLastSlug(newPath)
    fileLocation = newPath[:fileIndex + 1]
    fileName = newPath[fileIndex + 1:]
    fileExt = ""
    try:
        ext = fileName.split(".")
        fileExt = ext[1]
        fileName = ext[0]
    except:
        arcpy.AddMessage("No file extension associated with this layer")
    newName = fileName
    if len(fileExt) > 0:
        newPath = fileLocation + newName + pathAppend + "." + fileExt
    if len(fileExt) == 0:
        newPath = fileLocation + newName + pathAppend
    return newPath

# user-prompted file renaming:
def createNewPath(oldPath):
    arcpy.AddMessage("\nPath selected = " + oldPath)
    newPath = oldPath
    fileIndex = findLastSlug(newPath)
    fileLocation = newPath[:fileIndex+1]
    fileName = newPath[fileIndex+1:]
    fileExt = ""
    try:
        ext = fileName.split(".")
        fileExt = ext[1]
        fileName = ext[0]
    except:
        arcpy.AddMessage("No file extension associated with this layer")
    x=0
    while x == 0:
        renameStyle = raw_input("\nSelect renaming style; 'c' for complete rename, 'a' for appending\n"
                                "(NOTE -- the extension will be automatically maintained if it exists) : ")
        renameStyle = renameStyle.lower()
        if renameStyle == "c" or renameStyle == "a":
            x += 1
        else:
            arcpy.AddMessage("\nWRONG INPUT\n")
            continue
    fileAppend = ""
    if renameStyle == "c":
        newName = raw_input("Enter new name for '" + fileName + "', excluding extension : ")
    if renameStyle == "a":
        newName = fileName
        fileAppend = raw_input("Enter appendation to '" + fileName + "', excluding extension : ")
    if len(fileExt) > 0:
        newPath = fileLocation + newName + fileAppend + "." + fileExt
    if len(fileExt) == 0:
        newPath = fileLocation + newName + fileAppend
    return newPath


arcpy.AddMessage("\nSTARTING RENAMING PROCESS :\n---------------")

# have user decide on renaming style:
while True:
    renameMethod = raw_input("\nSelect renaming method; 'b' for a batch renaming of all selected files (appendation),\n "
                            "'i' for an individual one-by-one renaming (appendation or complete renaming): ")
    renameMethod = renameMethod.lower()
    if renameMethod == "b" or renameMethod == "i":
        break
    else:
        arcpy.AddMessage("\nWRONG INPUT\n")
        continue
if renameMethod == "b":
    appendToPath = raw_input("What would you like appended to the selected files (example : '_2016') ? : ")
# build map selection, rename files, update paths in MXDs:
for key, path in fileDict.items():
    selectedMaps = set([])
    if key in selectedFiles:
        if renameMethod == "i":
            newPath = createNewPath(path)
        if renameMethod == "b":
            newPath = createNewPathBatch(path, appendToPath)
        print path + " ---> " + newPath
        arcpy.Rename_management(path, newPath)
        selectedMaps = returnMXDsWithLayer(path)
        for mapKey, layerDict in mapDict.items():
            if mapKey in selectedMaps:
                mxd = arcpy.mapping.MapDocument(layerDict[0])
                for lyr in arcpy.mapping.ListLayers(mxd):
                    try:
                        if lyr.dataSource == path:
                            workspace_type = determineWorkspace(lyr)
                            print "workspace_type : " + workspace_type
                            workspace_path = newPath[:findLastSlug(newPath)]
                            print "workspace_path : " + workspace_path
                            try:
                                dataset_name = newPath[findLastSlug(newPath)+1:newPath.index(".")]
                            except:
                                dataset_name = newPath[findLastSlug(newPath) + 1:]
                            validate = True
                            lyr.replaceDataSource(workspace_path, workspace_type, dataset_name, validate)
                    except:
                        arcpy.AddMessage("Replace of data source failed for " + newPath + " within " + layerDict[0])
                mxd.save()