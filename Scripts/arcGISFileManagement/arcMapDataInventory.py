# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: This script inventories ArcMaps for their referenced data and outputs it to a CSV
# Can be run before and referenced by arcGISFileInventory.py to provide it with reference counts for each file

# Import system modules
import arcpy, os, sys, time, csv
import datetime as dt

arcpy.env.workspace = "C:\temp"

# Checks to see if running in ArcGIS
if len(sys.argv) > 1:
    Location = arcpy.GetParameterAsText(0)
    Name = arcpy.GetParameterAsText(1)
    OutFile= Location + "\\" + Name + ".csv"

else:
    Location = raw_input('Which folder to inventory for MapData? ')
    Extension = "\\MapData_"+dt.datetime.today().strftime("%Y_%m_%d")+".csv"
    OutFile = Location + Extension

ErrorCount = 0

# Creates a new text file with headers
with open(OutFile, 'wb', 0) as csvfile:
    csvwriter = csv.writer(csvfile)
    # Create header row
    csvwriter.writerow(["FileName", "MapLocation", "LayerName", "CatalogPath", "LinkBroken", "DateCreated", "DateModified"])
# find all the MXD's in the directory tree
    for dir, dirs, files in os.walk(Location):
        for filename in files:
            fullpath = os.path.join(dir, filename)
            basename, extension = os.path.splitext(fullpath)
            # Skips EMB's Subfolder
            if "emb" in dirs:
                dirs.remove("emb")
            # Continues
            elif extension.lower() == ".mxd":
                arcpy.AddMessage("-----------------------------------------")
                arcpy.AddMessage(fullpath)
                arcpy.AddMessage("-----------------------------------------")
                # open the map document
                MXD = arcpy.mapping.MapDocument(fullpath)
                brknList = arcpy.mapping.ListBrokenDataSources(MXD)  # Gets broken links
            #  get all the layers
                for lyr in arcpy.mapping.ListLayers(MXD):
                # get the source from the layer
                    if lyr.supports("workspacePath"):
                        try:
                            try:
                                dateEp = os.path.getctime(fullpath)
                                cDate = time.strftime("%d  %b %Y", time.gmtime(dateEp))
                            except:
                                cDate = ""
                            try:
                                dateMod = os.path.getmtime(fullpath)
                                mDate = time.strftime("%d %b %Y", time.gmtime(dateMod))
                            except:
                                mDate = ""
                        except:
                            cDate = ""
                            mDate = ""
                    # Make Path Consistent
                        if str(lyr.dataSource)[:1] == "G" or str(lyr.dataSource)[:1] ==  "g":
                            drLtr = "\\\\ALBGIS\GISDev"
                            tmpSrc = str(lyr.dataSource)[2:]
                            source = "%s%s" % (drLtr, tmpSrc)
                        elif str(lyr.dataSource)[:1] == "Z" or str(lyr.dataSource)[:1] ==  "z":
                            drLtr = "\\\\ALBGIS\GISdata"
                            tmpSrc = str(lyr.dataSource)[2:]
                            source = "%s%s" % (drLtr, tmpSrc)
                        else:
                            source = lyr.dataSource
                    # Displays layer and path to data
                        try:
                            msg = "%s -> %s" % (lyr, source)
                            brkn = "N"
                            arcpy.AddMessage(msg)
                        except:
                            raise
                        if lyr in brknList:
                            brkn = "Y"
                    # Writes information to Text File
                        try:
                            csvwriter.writerow([filename, dir, lyr, source, brkn, cDate, mDate])
                        except (UnicodeEncodeError):
                            csvwriter.writerow([filename, dir,"" , source, brkn, cDate, mDate])
                            arcpy.AddMessage("Unicode Error on: ")
                            arcpy.AddMessage(source)
                            ErrorCount = ErrorCount + 1
                            continue
                    # Cleans up
                        del brkn
                        del msg
                del MXD
# Closing messages
arcpy.AddMessage("-------------------")
arcpy.AddMessage("File written to:")
arcpy.AddMessage(OutFile)
arcpy.AddMessage("# of errors:")
arcpy.AddMessage(ErrorCount)
arcpy.AddMessage("Done!")