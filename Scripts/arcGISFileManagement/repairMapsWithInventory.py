#  AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
#  This script is to be used in conjunction with the output csv of  "FullDataInventory.py"
#  Once the replacement data paths have been fully filled into the csv,
#  this script will remap the data source for all maps it finds in a folder and it's successive subfolders.

# Import modules
import csv, sys, arcpy, os

# Set initial variables
found = 0
MapCount = 0
LayerCount = 0
PassCount = 0
FailCount = 0
dataType = ''
FData = []

locMaps = raw_input("For which ArcMap folder would you like to update the data sources? : ")

# identify and verify location of relevant data inventory file:
while True:
    locInventory = raw_input("Enter path to relevant FileInventory.csv : ")
    try:
        with open(locInventory, 'rb', 0) as csvfile:
            "valid CSV found"
            break
    except:
        arcpy.AddMessage("INVALID INPUT: please input a valid file path for the inventory CSV")
        continue

# decide whether or not to overwrite affected maps:
while True:
    Overwrite = raw_input('Overwrite maps? (Y/N) ')
    Overwrite = Overwrite.lower()
    if Overwrite == "n":
        arcpy.AddMessage("You've chosen to NOT overwrite the specified ArcMaps.")
        break
    if Overwrite == "y":
        arcpy.AddMessage("You've chosen to overwrite the specified ArcMaps.")
        break
    else:
        arcpy.AddMessage("INVALID INPUT: please input 'y' or 'n'")

# start list creation :
for dir, dirs, files in os.walk(locMaps):
    for filename in files:
        fullpath = os.path.join(dir, filename)
        basename, extension = os.path.splitext(fullpath)
        if "emb" in dirs:              # Skips EMB's folder because it causes the script to fail
            dirs.remove("emb")
        elif extension.lower() == ".mxd":                         # Opens map documents
            # open the map document
            MXD = arcpy.mapping.MapDocument(fullpath)
            print '-----------------------------------------------------'
            print fullpath            
            print '-----------------------------------------------------'
            # get all the layers
            for lyr in arcpy.mapping.ListLayers(MXD):               # Looks at all layers in the Map Document
                LayerCount += 1
                # get the source from the layer
                if lyr.supports("workspacePath"):
                   with open(locInventory, 'rb') as csvfile:                      # Matches datasources for each layer
                        reader = csv.DictReader(csvfile)
                        for row in reader:                          # Standardizes drives to UNC, which matches in CSV
                            oldSource = row['CatalogPath'] + "\\" + row['FileName']
                            newSource = row['NewPath']  # new data location
                            newName = row['NewName']
                            if str(lyr.dataSource)[:1] == "G" or str(lyr.dataSource)[:1] ==  "g":
                                drLtr = "\\\\ALBGIS\GISDev"
                                tmpSrc = str(lyr.dataSource)[2:]
                                source = "%s%s" % (drLtr, tmpSrc)
                            elif str(lyr.dataSource)[:1] == "Z" or str(lyr.dataSource)[:1] ==  "z":
                                drLtr = "\\\\ALBGIS\GISdata"
                                tmpSrc = str(lyr.dataSource)[2:]
                                source = "%s%s" % (drLtr, tmpSrc)
                            else:
                                source = str(lyr.dataSource)
                        # When a match from ArcGIS to old data is found in the inventory CSV, replaces the datasource :
                            if source== oldSource:
                                print oldSource
                                print newSource
                                base, ext = os.path.splitext(newName)
                                if ".gdb" in newSource:
                                    dataType = 'FILEGDB_WORKSPACE'
                                elif ".mdb" in newSource:
                                     dataType = 'ACCESS_WORKSPACE'
                                elif row['DataType'] == 'Table' and ".gdb" not in newSource:
                                    dataType = 'EXCEL_WORKSPACE'
                                elif row['DataType'] == 'ShapeFile':
                                    if '.shp' in newName:
                                        newName = base
                                    dataType = 'SHAPEFILE_WORKSPACE'
                                elif row['DataType'] == 'RasterDataset':
                                    dataType = 'RASTER_WORKSPACE'
                                elif row['DataType'] == 'CoverageFeatureClass':
                                    dataType = 'ARCINFO_WORKSPACE'
                                else:
                                    dataType = 'NONE'
                                try:
                                    lyr.replaceDataSource(newSource, dataType, newName, True)  # Action Step for replacement
                                    PassCount +=1
                                except Exception, e:        # Skips the layer if something goes wrong
                                    FailCount+=1
                                    print '---------------------------------------------------'
                                    print e
                                    print newSource
                                    print dataType
                                    print newName
                                    print '---------------------------------------------------'
                                    FData.append(str(newSource + ' - ' + newName))
                            else:
                                pass
            if Overwrite.lower() == 'y':  # Overwrites mxd if overwrite chosen
                MXD.save()
            else:
                MXD.saveACopy(basename + "-updated" + extension)  # Saves a new copy if overwrite disabled

            MapCount += 1
            del MXD

arcpy.AddMessage("Maps Completed: ")
arcpy.AddMessage(MapCount)
arcpy.AddMessage("Number of Layers: ")
arcpy.AddMessage(LayerCount)
arcpy.AddMessage("Layers Succeeded: ")
arcpy.AddMessage(PassCount)
arcpy.AddMessage("Layers failed: ")
arcpy.AddMessage(FailCount)
if len(FData) > 0:
    PrntFData = raw_input("View Failed Datasets? (Y/N) ")
    if PrntFData.lower() == 'y':
        arcpy.AddMessage("--------------------------------------------")
        arcpy.AddMessage("Failed Datasets - Fix in CSV")
        # 'set' converts list to a set (which can have no duplicates) and then 'list' converts 'set' back to a list
        list(set(FData))
        for item in FData:
            arcpy.AddMessage(item)
            arcpy.AddMessage("--------------------------------------------")
        done = raw_input("Done? (Press Enter)")
        arcpy.AddMessage("DONE!")
else:
    arcpy.AddMessage("--------------------------------------------")
    arcpy.AddMessage("DONE!")