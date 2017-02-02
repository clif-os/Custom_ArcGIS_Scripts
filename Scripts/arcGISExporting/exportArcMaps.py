# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: Export all PDFs of MXD documents in a particular file to a specified folder

# Import system modules:
import arcpy, os, time, datetime

# Define exporting areas :
arcmapLoc = raw_input('Enter filepath of folder to export maps from : ')
exportLoc = raw_input('Enter filepath of folder to export maps to : ')

# Define exporting method :
while True:
    exportMethod = raw_input('Select export method -- \'all\' for all files, \'date\' for date mod, \'single\' for one by one: ')
    if exportMethod.lower() == "all" or exportMethod.lower() == "date" or exportMethod.lower() == "single":
        break
    else:
        arcpy.AddMessage("WRONG ENTRY")
        continue

# Define walking extent:
while True:
    walkExtent = raw_input("Include subfolders in export ? (\'y\' or \'n\') : " )
    if walkExtent.lower() == "y" or walkExtent.lower() == "n":
        break
    else:
        arcpy.AddMessage("WRONG ENTRY")
        continue

exportFails = []

def exportMaptoPDF(fullpath, exportLoc):
    try:
        indexRoll = -1
        index = 0
        while indexRoll > -len(fullpath):
            if fullpath[indexRoll] == "\\":
                index = indexRoll
                break
            indexRoll -= 1
        filename = fullpath[index:]
        arcpy.AddMessage("------------EXPORTING------------")
        arcpy.AddMessage("fullpath: " + fullpath)
        arcpy.AddMessage("filename: " + filename)
        mxd = arcpy.mapping.MapDocument(fullpath)
        exportPath = exportLoc + "\\" + filename
        arcpy.mapping.ExportToPDF(mxd, exportPath, 'PAGE_LAYOUT')
    except:
        arcpy.AddMessage("Failed to Export")
        exportFails.append(fullpath)


# Summarize file contents:
if exportMethod == "date" or exportMethod == "single":
    mapDict = {}
    dates = []
    toExport = []
    # Inventory available arcmap docs into a dictionary :
    for files in os.walk(arcmapLoc):
        for filenames in files:
            for filename in filenames:
                if filename.lower().endswith(".mxd"):
                    fullpath = files[0] + "\\" + filename
                    try:
                        dateMod = time.strftime('%Y/%m/%d', time.gmtime(os.path.getmtime(fullpath)))
                    except:
                        if "unknown" in mapDict:
                            mapDict["unknown"].append(fullpath)
                        else:
                            mapDict["unknown"] = [fullpath]
                    if dateMod in mapDict:
                        mapDict[dateMod].append(fullpath)
                    else:
                        mapDict[dateMod] = [fullpath]
                        dates.append(dateMod)
        if walkExtent == 'n':
            break
    sorted_Dates = sorted(dates, key=lambda x: datetime.datetime.strptime(x, '%Y/%m/%d'))
    sorted_Dates.reverse()
    if exportMethod == "single":
        for date in sorted_Dates:
            for fullpath in mapDict[date]:
                while True:
                    export = raw_input("Export " + fullpath + " ? (\'y\' or \'n\') : ")
                    if export.lower() == 'y' or export.lower() == 'n':
                        break
                    else:
                        arcpy.AddMessage("WRONG ENTRY")
                        continue
                if export.lower() == 'y':
                    toExport.append(fullpath)
                arcpy.AddMessage("--------------------------------------------------")
    if exportMethod == "date":
        arcpy.AddMessage("All dates modified:")
        arcpy.AddMessage(sorted_Dates)
        arcpy.AddMessage("--------------------------------------------------------------------------------------")
        for date in sorted_Dates:
            arcpy.AddMessage("Maps last modified on " + date + " :")
            arcpy.AddMessage(mapDict[date])
            while True:
                export = raw_input("Export maps modified on " + date + " ? (\'y\' or \'n\') : ")
                if export.lower() == 'y' or export.lower() == 'n':
                    break
                else:
                    arcpy.AddMessage("WRONG ENTRY")
                    continue
            if export.lower() == 'y':
                for path in mapDict[date]:
                    toExport.append(path)
            arcpy.AddMessage("--------------------------------------------------")
    for fullpath in toExport:
        exportMaptoPDF(fullpath, exportLoc)

elif exportMethod == "all":
    for files in os.walk(arcmapLoc):
        for filenames in files:
            for filename in filenames:
                if filename.lower().endswith(".mxd"):
                    fullpath = files[0] + "\\" + filename
                    exportMaptoPDF(fullpath, exportLoc)
        if walkExtent == 'n':
            break
arcpy.AddMessage("---------------------DONE EXPORTING---------------------")
if len(exportFails)>0:
    arcpy.AddMessage('The following files failed to export: ')
    for fail in exportFails:
        arcpy.AddMessage(fullpath)
    arcpy.AddMessage("---------------------DONE REPORTING FAILS---------------------")