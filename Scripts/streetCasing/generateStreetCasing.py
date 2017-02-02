# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: take a group of taxlots and turn it into a streetcasing
# 'closingPolys' can be used to close off large gaps in the taxlot periphery and ensure integration makes a clean whole poly for cookie cutting
# 'erasePolys' and 'erasePoints' can be used together to automatically free off, select, and erase known pieces of the casing known to be erroneous

#***************************************************
# SETUP
# Import system modules -------------------------------------------------------------------------------------------
import arcpy, datetime
import arcpy.cartography as CA
import TigFx_20110209 as TigFx

# Create a log file for writing
strLogFile = "generateStreetCasing.log"
logFile = open(strLogFile, "a")
logFile.truncate(0)

# Capture start time
operation = "Generate street casing."

# Construct data source location variables:
rawTaxlot_loc = 'Database Connections\\TIGGISDB_Pub_WaCo.sde\\sde_pub_waco.GIS.taxlot_clip'
testingOutput_loc = '\\\\192.168.109.61\\Geoprocessing\\DataMaintenance\\DataMaintenance.gdb'
testingClosingPolys_loc = '\\\\192.168.109.61\\Geoprocessing\\DataMaintenance\\DataMaintenance.gdb\\streetCasing_closingPolys'
testingErasePolys_loc = '\\\\192.168.109.61\\Geoprocessing\\DataMaintenance\\DataMaintenance.gdb\\streetCasing_erasePolys'
testingErasePoints_loc = '\\\\192.168.109.61\\Geoprocessing\\DataMaintenance\\DataMaintenance.gdb\\streetCasing_erasePoints'
# publish_loc = 'Database Connections\\TIGGISDB_Prod_Tig.sde\\sde_prod_tig.GIS.Transportation\\sde_prod_tig.GIS.street_casing'

# Construct output location variables:
now = datetime.datetime.now()
year = str(now.year)
month = str(now.month)
if len(month) == 1:
    month = "0" + month
day = str(now.day)
if len(day) == 1:
    day = "0" + day
taxlot1_loc = testingOutput_loc + "\\" + "taxlot_clip_" + year + month + day
taxlotOutline_loc = testingOutput_loc + "\\" + "taxlot_clip_" + "outline_" + year + month + day
intermediates_outline = [
    testingOutput_loc + "\\" + "taxlot_clip_" + "outline_Inter1_" + year + month + day,
    testingOutput_loc + "\\" + "taxlot_clip_" + "outline_Inter2_" + year + month + day,
    testingOutput_loc + "\\" + "taxlot_clip_" + "outline_Inter3_" + year + month + day,
    testingOutput_loc + "\\" + "taxlot_clip_" + "outline_Inter4_" + year + month + day,
    testingOutput_loc + "\\" + "taxlot_clip_" + "outline_Inter5_" + year + month + day
]
intermediates_casing = [
    testingOutput_loc + "\\" + "street_casing_new_" + "Inter1",
    testingOutput_loc + "\\" + "street_casing_new_" + "Inter2",
    testingOutput_loc + "\\" + "street_casing_new_" + "Inter3",
    testingOutput_loc + "\\" + "street_casing_new_" + "Inter4",
    testingOutput_loc + "\\" + "street_casing_new_" + "Inter5"
]
byproducts_casing = [
    testingOutput_loc + "\\" + "street_casing_new_" + "Inter2_" + "Pnt"
]
streetCasing_loc = testingOutput_loc + "\\" + "street_casing_new"

# PROCESSING

arcpy.env.overwriteOutput = True

print "Making copy of taxlots into working GDB" 
taxlot1_loc = testingOutput_loc + "\\" + "taxlot_clip_" + year + month + day
arcpy.CopyFeatures_management(in_features=rawTaxlot_loc,
                              out_feature_class=taxlot1_loc)

print "Repairing taxlot geometry"
arcpy.RepairGeometry_management(in_features=taxlot1_loc)

print "Performing integration on taxlots"
xyTolerance = "0.5 feet"
arcpy.Integrate_management(in_features=taxlot1_loc,
                           cluster_tolerance=xyTolerance)

print "Merging closing resource polygons into taxlots in preparation for aggregation"
# combine the manually generated polygons which close off the major highway gaps that cannot be automatically
# closed while also maintaining detail
arcpy.Merge_management(inputs=[taxlot1_loc, testingClosingPolys_loc],
                       output=intermediates_outline[0])

print "Dissolving taxlot layer in preparation for aggregation"
# dissolve together all features to make aggregation simpler
arcpy.Dissolve_management(in_features=intermediates_outline[0],
                          out_feature_class=intermediates_outline[1])

print "Performing first aggregation"
# The first aggregation leaves holes and some island features leftover, must be re-aggregated after holes are filled
CA.AggregatePolygons(in_features=intermediates_outline[1],
                     out_feature_class=intermediates_outline[2],
                     aggregation_distance=250,
                     minimum_area=0,
                     minimum_hole_size="100000000000000000000000000000000000000000000",
                     orthogonality_option="ORTHOGONAL",
                     barrier_features="",
                     out_table="")

print "Eliminating holes in aggregated polygon"
# Eliminate all holes in the aggregated polygon
arcpy.EliminatePolygonPart_management(in_features=intermediates_outline[2],
                                      out_feature_class=intermediates_outline[3],
                                      condition="AREA",
                                      part_area="100000000000000000000000000000000000000000000",
                                      part_area_percent="",
                                      part_option="ANY")

print "Dissolving aggregated polygon to remove leftover interior pieces"
arcpy.Dissolve_management(in_features=intermediates_outline[3],
                          out_feature_class=intermediates_outline[4])

print "Performing final aggregation to include floating peripheral features"
CA.AggregatePolygons(in_features=intermediates_outline[4],
                     out_feature_class=taxlotOutline_loc,
                     aggregation_distance=350,
                     minimum_area=0,
                     minimum_hole_size="100000000000000000000000000000000000000000000",
                     orthogonality_option="NON_ORTHOGONAL",
                     barrier_features="",
                     out_table="")

print "Clean up intermediates from taxlot outline creation"
for intermediate in intermediates_outline:
    try:
        arcpy.Delete_management(in_data=intermediate)
    except:
        print "failed to delete " + intermediate

print "Creating casing: erasing taxlots from taxlot outline"
arcpy.Erase_analysis(in_features=taxlotOutline_loc,
                     erase_features=taxlot1_loc,
                     out_feature_class=intermediates_casing[0])

print "Cleaning up street casing"
CA.SimplifyPolygon(in_features=intermediates_casing[0],
                   out_feature_class=intermediates_casing[1],
                   algorithm="POINT_REMOVE",
                   tolerance="0.5 feet")

print "Using manually generated division polygons to erase and separate out rivers from roads"
arcpy.Erase_analysis(in_features=intermediates_casing[1],
                     erase_features=testingErasePolys_loc,
                     out_feature_class=intermediates_casing[2])

print "Exploding multiparts"
arcpy.MultipartToSinglepart_management(in_features=intermediates_casing[2],
                                       out_feature_class=intermediates_casing[3])

print "Using manually placed points to select and export non-street features"
arcpy.MakeFeatureLayer_management(in_features=intermediates_casing[3],
                                  out_layer='intermediate_4_lyr')
arcpy.SelectLayerByLocation_management(in_layer='intermediate_4_lyr',
                                       overlap_type='intersect',
                                       select_features=testingErasePoints_loc)

print "Export the selected non-street features as a feature class"
arcpy.CopyFeatures_management(in_features='intermediate_4_lyr',
                              out_feature_class=intermediates_casing[4])

print "Use the exported non-street features to erase the non-street features from the street casing layer"
arcpy.Erase_analysis(in_features=intermediates_casing[3],
                     erase_features=intermediates_casing[4],
                     out_feature_class=streetCasing_loc)

print "Cleaning up intermediates and byproducts from street casing clean-up"
for intermediate in intermediates_casing:
    try:
        arcpy.Delete_management(in_data=intermediate)
    except:
        print "failed to delete " + intermediate
for byproduct in byproducts_casing:
    try:
        arcpy.Delete_management(in_data=byproduct)
    except:
        print "failed to delete " + byproduct

#***************************************************
# FINISH UP

print "SUCCESSFULLY COMPLETED generateStreetCasing.py"
