# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: take any line feature, break it into pieces, and extract slope information from a DEM into the segments.
# The lines being broken up semi-intelligently to capture major slope differences and then rejoined to simplify neighboring line segments with the same slope threshold.

import arcpy, sys

arcpy.env.overwriteOutput = True

workspace = "\\\\192.168.109.215\\GIS_Projects\\FIS_projects\\2016\\Walking_map_app_project\\walking_map_slope.gdb"
inputName = "route"
input = workspace + "\\" + inputName
DEM_loc = "Database Connections\TIGGISDB_Images.sde\sde_images.GIS.LIDAR_2014_BE_DEM"

# Check for 3D License:
if arcpy.CheckExtension("3D") == "Available":
    arcpy.CheckOutExtension("3D")
else:
    sys.exit("3D Tools Not Licensed")

# Check if the incoming data already has a slope field and remove it for processing
def makeFieldList(input):
    fields = []
    fieldsEnc = arcpy.ListFields(input)
    for field in fieldsEnc:
        fields.append(str(field.name))
    return fields
fields = makeFieldList(input)
if "Avg_Slope" in fields:
    arcpy.DeleteField_management(input, "Avg_Slope")

# Simplify the lines as much as possible by dissolving
arcpy.Dissolve_management(input, input + "_dissolve1", ["ROUTE_TYPE", "SIGNED_TRAIL", "CONNECT_ROUTE"], "", "SINGLE_PART", "DISSOLVE_LINES")
# Utilize Feature To Line tool to break lines at intersections
arcpy.FeatureToLine_management(input + "_dissolve1", input + "_break1", "", "")
# Remove the field/column byproduct of Feature to Line
arcpy.DeleteField_management(input + "_break1", "FID_" + inputName + "_dissolve1")

# Break all line segments greater than the defined value 'divLength' --
# by creating points and using them to Split Line At Point
cursor = arcpy.SearchCursor(input + "_break1")
ptGeoms = []
divLength = 200
for feature in cursor:
    divisions = int(feature.SHAPE_length/divLength)
    pointCount = 0
    while pointCount < divisions:
        division = feature.shape.positionAlongLine(divLength + (divLength*pointCount), False).firstPoint
        pt = arcpy.Point(division.X, division.Y)
        ptGeoms.append(arcpy.PointGeometry(pt))
        pointCount += 1
arcpy.CopyFeatures_management(ptGeoms, workspace + "\\splitPoints_" + str(divLength))
dsc = arcpy.Describe(input)
coord_sys = dsc.spatialReference
arcpy.DefineProjection_management(workspace + "\\splitPoints_" + str(divLength), coord_sys)
arcpy.SplitLineAtPoint_management(input + "_break1", workspace + "\\splitPoints_" + str(divLength), input + "_split1", "1 Foot")

# Provide all line segments with an Avg Slope field
arcpy.ddd.AddSurfaceInformation(input + "_split1", "Database Connections\TIGGISDB_Images.sde\sde_images.GIS.LIDAR_2014_BE_DEM", "AVG_SLOPE", "LINEAR", "", 1, "")

# Use thresholds to group and dissolve line segments by slope in order to simplify data set
arcpy.AddField_management(input + "_split1", "SLOPE_THRESH", "SHORT")
fields = makeFieldList(input + "_split1")
cursor = arcpy.SearchCursor(input + "_split1")
slopeThresholds = [[(0, 4), 1], [(4, 6), 2], [(6, 9), 3], [(9, 14), 4], [(14, 20), 5], [(20, 100), 6]]
with arcpy.da.UpdateCursor(input + "_split1", fields) as cursor:
    for feature in cursor:
        for threshold in slopeThresholds:
            if feature[6] >= threshold[0][0] and feature[6] < threshold[0][1]:
                feature[7] = threshold[1]
                cursor.updateRow(feature)
arcpy.Dissolve_management(input + "_split1", input + "_dissolve2", ["ROUTE_TYPE", "SIGNED_TRAIL", "CONNECT_ROUTE", "SLOPE_THRESH"], "", "SINGLE_PART", "DISSOLVE_LINES")

# Utilize Feature To Line tool to break lines that might have been dissolved together at intersections --
# this will remove the Avg Slope field
arcpy.FeatureToLine_management(input + "_dissolve2", input + "_final", "", "")
# Remove the field/column byproduct of Feature to Line
arcpy.DeleteField_management(input + "_final", ["SLOPE_THRESH", "FID_" + inputName + "_dissolve2"])
# Reprovide the Avg Slope Field
arcpy.ddd.AddSurfaceInformation(input + "_final", DEM_loc, "AVG_SLOPE", "LINEAR", "", 1, "")