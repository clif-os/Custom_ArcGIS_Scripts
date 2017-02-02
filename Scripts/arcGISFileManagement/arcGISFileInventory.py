# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: This script is used to inventory the data on a given drive.
# If you run ArcMapDataInventory prior to using this tool, you can also collect information like total ArcMap references for each file
# One may point it at a folder and this script will search for all files within the subfolders using ArcPy da.Walk
# LIMITATIONS: can fail with no error message ; ArcPy da.Walk failing on CAD files
# .dwg and .dgn files are being caught by try/except, but this is not solving problem
# http://gis.stackexchange.com/questions/109656/how-to-get-arcpy-da-walk-to-continue-walk-after-encountering-corrupt-problem-fil
# may want to utilize an import of 'multiprocessing'
# If you are using this for rearranging a file system: manually fill in the columns for the new location (NewPath) and new name (NewName)

# Can be used in conjunction with repairMapsWithInventory to both inventory and then subsequently repair broken links

import arcpy, csv, os, sys, time
import datetime as dt

# define workspace
if len(sys.argv) > 1:
    workspace = arcpy.GetParameterAsText(0)
else:
    workspace = raw_input("Enter path to folder for inventory: ")

# define output and decide on whether to avoid .DWG and .DGN files;
# these file types were causing a significant number of errors
while True:
    skip = raw_input("Skip .DWG and .DGN files? (Y or N) : ")
    skip = skip.lower()
    if skip == "y":
        output = workspace + "\\AllDataInventory_"+dt.datetime.today().strftime("%Y_%m_%d")+"_skipCAD.csv"
        break
    elif skip == "n":
        output = workspace + "\\AllDataInventory_"+dt.datetime.today().strftime("%Y_%m_%d")+".csv"
        break
    else:
        arcpy.AddMessage("WRONG INPUT: please input 'y' or 'n'")
        continue

# decide on how to handle inventory of arcMap references
while True:
    mapDataRun = raw_input("Include count of total ArcMap References in file inventory? (Y or N) : ")
    mapDataRun = mapDataRun.lower()
    if mapDataRun == "n":
        arcpy.AddMessage("You've chosen to exclude a count of total ArcMap References from your file inventory.")
        break
    if mapDataRun == "y":
        break
    else:
        arcpy.AddMessage("WRONG INPUT: please input 'y' or 'n'")
        continue
if mapDataRun == "y":
    while True:
        mapDataExist = raw_input("Does the relevant MapData CSV already exist? (Y or N) : ")
        mapDataExist = mapDataExist.lower()
        if mapDataExist == "y":
            mapDataLoc = raw_input("please enter the complete path name for the relevant Map Data file, "
                                   "including filename as 'filepath\\filename.csv : ")
            try:
                with open(mapDataLoc, 'rb', 0) as csvfile:
                    "valid CSV found"
                    break
            except:
                arcpy.AddMessage("WRONG INPUT: please input a valid file path for the Map Data CSV")
                continue
        if mapDataExist == "n": #MapData Script Runs Here
            arcpy.AddMessage("----------------STARTING ARCMAP INVENTORY----------------")
            import MapData
            arcpy.AddMessage("Check to see that a an accurate MapLayers.csv has been created in the correct location")
            mapDataLoc = raw_input("if so, please enter its location as 'filepath\\filename.csv : ")
            try:
                with open(mapDataLoc, 'rb', 0) as csvfile:
                    "valid CSV found"
                    break
            except:
                arcpy.AddMessage("WRONG INPUT: please input a valid file path for the Map Data CSV")
                continue
        else:
            arcpy.AddMessage("WRONG INPUT: please input 'y' or 'n'")
            continue

# map refs within the file inventory loop
def countArcMapRefs(mapDataLoc, sourceFile):
    countRefs = 0
    with open(mapDataLoc, 'rb', 0) as csvfile:
        reader = csv.reader(csvfile)
        try :
            for row in reader:
                if row[3] == sourceFile:
                    countRefs+= 1
        except :
            arcpy.AddMessage("FAILED TO COUNT ARCMAP REFS")
            return "FAILED"
    return countRefs

# setup counters and error list
FinalCount = 0  # successful
SkipCount = 0  # unsuccessful
errorList = []

# start file parsing and CSV work
with open(output, 'wb', 0) as csvfile: # 'wb' = write buffered
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["FileName", "CatalogPath", "FilePath", "DataType",
                        "DateCreated", "ArcMapReferences", "NewPath", "NewName"])  # header row
    for dirpath, dirnames, filenames in arcpy.da.Walk(workspace):
        try:
            arcpy.AddMessage("----------------------------------------------------------")
            for filename in filenames:
                arcpy.AddMessage("------------------------")

                arcpy.AddMessage("dirpath " + dirpath)
                arcpy.AddMessage("filename: " + filename)

                # avoiding interpreting .dwg and .dgn files
                if dirpath.endswith(".dwg") or dirpath.endswith(".dgn"):
                    arcpy.AddMessage(dirpath[-4:] + " file encountered")
                    dType = dirpath[-4:0]
                    dName = dirpath, "\\", filename
                    if skip == "y":
                        csvwriter.writerow([dName, "-", "-", dType, "-", "-"])
                        arcpy.AddMessage("SKIPPING")
                        continue
                # describe files not avoided in previous section
                else:
                    desc = arcpy.Describe(os.path.join(dirpath, filename))
                    dName = desc.name
                    dType = desc.dataType
                # Skips EMB's Folder
                if "emb" in dirnames:
                    dirnames.remove("emb")
                # path names:
                if dirpath[:1].lower() == "z" or dirpath[:1].lower() == "g":
                    if dirpath[:1].lower() == "z":
                        drLtr = "\\\\ALBGIS\GISdata"  # true path of Z Drive
                    else:
                        drLtr = "\\\\ALBGIS\GISDev"  # true path of G Drive
                    tmpSrc = str(os.path.join(dirpath))[2:]
                    source = "%s%s" % (drLtr, tmpSrc)  # constructing true/"UNC" path
                    sourceFile = source + '\\' + filename
                    # date created:
                    try:
                        dateEp = os.path.getctime(source)
                        date = time.strftime("%d %b %Y", time.gmtime(dateEp))
                    except:
                        date = ""
                    # total references in arcMap Docs:
                    if mapDataRun == "y":
                        refs = countArcMapRefs(mapDataLoc, sourceFile)
                    if mapDataRun == "n":
                        refs = "-"
                    # commit to CSV :
                    csvwriter.writerow([dName, source, sourceFile, dType, date, refs])
                    FinalCount += 1
                    del drLtr, tmpSrc, source
                    continue
                else: # if neither Z or G (nonstandard drive letter)
                    csvwriter.writerow([dName, str(os.path.join(dirpath)), "", dType, date, ""])
                    FinalCount += 1

        except (IOError, RuntimeError):
            arcpy.AddMessage("Skipping file, an error has occurred")
            arcpy.AddMessage("error occurred for: %s\\%s" % (dirpath, filename))
            SkipCount += 1
            errorList.append("%s\\%s" % (dirpath, filename))
            arcpy.AddMessage(SkipCount)
            continue

# Display number of files added to the CSV
arcpy.AddMessage("Files inventoried and added to the table:")
arcpy.AddMessage(FinalCount)

# Display number of skipped files
arcpy.AddMessage("Files with errors:")
arcpy.AddMessage(SkipCount)
if len(errorList)>0 :
    arcpy.AddMessage("Errors occurred for the following files within the Data Inventory script : ")
    for p in errorList:
        arcpy.AddMessage(p)

# Where the file is stored
arcpy.AddMessage("You can find the inventory table at: ")
arcpy.AddMessage(output)

# Notify finished
arcpy.AddMessage("_______________________________")
arcpy.AddMessage("DONE")