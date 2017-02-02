# AUTHOR: Clifton Campbell (contact@cliftoncampbell.net)
# Tool Description: takes a point layer, assigns the points to group based off a 'grouping radius',
# then spaces out the points based off of the 'spacings' array

import arcpy

arcpy.env.overwriteOutput = True

# \\192.168.109.215\GIS_Projects\CD_projects\LRPLN\Agnes\Misc Projects\SRTS\sidewalk_rendering.mxd

signsMaster_loc = '\\\\192.168.109.215\\GIS_Projects\\FIS_projects\\2016\\signPostCartoLayerGeneration\\data.gdb\\signs_master'
workspace_loc = '\\\\192.168.109.215\\GIS_Projects\\FIS_projects\\2016\\signPostCartoLayerGeneration\\data2.gdb'

intermediates = [
    workspace_loc + '\\' + 'int_1',
    workspace_loc + '\\' + 'int_2',
    workspace_loc + '\\' + 'int_3',
    workspace_loc + '\\' + 'int_4',
    workspace_loc + '\\' + 'int_5'
]

finalOutput_loc = workspace_loc + '\\' + 'offsetSigns'

#radius used to group points
groupingRadius = '5 Feet'

# resolution needs to be available for 1:500 --> 1:1000
# spacings are in feet
spacings = [10, 20, 30]

def spreadOutValuesOnYAxis(yVals, ySpacing):
    newYVals = []
    pointCount = len(yVals)
    length = (pointCount - 1) * ySpacing
    yOrigin = yVals[0]
    heightFromOrigin = yOrigin + (length / 2)
    index = 0
    YIndex = heightFromOrigin
    while index < pointCount:
        newYVals.append(YIndex)
        YIndex -= ySpacing
        index += 1
    return newYVals

if arcpy.Exists(intermediates[0]):
    print "ALREADY COMPLETED, SKIPPING: copy of the master signs layer for editing"
else:
    print "Making a copy of the master signs layer for editing"
    arcpy.Copy_management(in_data=signsMaster_loc,
                          out_data=intermediates[0])

if arcpy.Exists(intermediates[1]):
    print "ALREADY COMPLETED, SKIPPING: removing duplicates from sign layer"
else:
    print "Exporting a sorted version of the signs layer"
    arcpy.Sort_management(in_dataset=intermediates[0],
                          out_dataset=intermediates[1],
                          sort_field=[['UNITID_1', 'ASCENDING']])
    print "Deleting duplicates"
    arcpy.MakeFeatureLayer_management(intermediates[1], "points_del")
    cursor_points = arcpy.da.UpdateCursor("points_del", ['UNITID_1'])
    UnIDs = [0, 0]
    for point_row in cursor_points:
        print UnIDs
        UnIDs[1] = point_row[0]
        if UnIDs[1] == UnIDs[0]:
            cursor_points.deleteRow()
            print "deletion"
        else:
            print "non deletion"
        UnIDs[0] = point_row[0]

if arcpy.Exists(intermediates[2]):
    print "ALREADY COMPLETED, SKIPPING: Buffering the signs"
else:
    print "Buffering the signs"
    arcpy.Buffer_analysis(in_features=intermediates[1],
                          out_feature_class=intermediates[2],
                          buffer_distance_or_field=groupingRadius,
                          dissolve_option='ALL')
if arcpy.Exists(intermediates[3]):
    print "ALREADY COMPLETED, SKIPPING: Exploding sign buffers to singleparts"
else:
    print "Exploding sign buffers to singleparts"
    arcpy.MultipartToSinglepart_management(in_features=intermediates[2],
                                           out_feature_class=intermediates[3])

while True:
    choice = raw_input("Update sign post editing layer with buffer group ID's and group counts ? (Y or N): ").lower()
    if choice == 'y':
        print "Adding sign group attributes to sings editing layer"
        arcpy.AddField_management(in_table=intermediates[1],
                                  field_name='GROUP_ID',
                                  field_type='SHORT')
        arcpy.AddField_management(in_table=intermediates[1],
                                  field_name='GROUP_COUNT',
                                  field_type='SHORT')
        print "Updating sign post editing layer with buffer group ID's and group counts"
        arcpy.MakeFeatureLayer_management(intermediates[3], "buffers")
        arcpy.MakeFeatureLayer_management(intermediates[1], "points")
        cursor_buffers = arcpy.SearchCursor(dataset=intermediates[3])
        for row_buffer in cursor_buffers:
            oid = row_buffer.getValue("OBJECTID")
            query_expression = '"OBJECTID" = %s' % oid
            arcpy.SelectLayerByAttribute_management("buffers", "NEW_SELECTION", query_expression)
            arcpy.SelectLayerByLocation_management(in_layer="points",
                                                   overlap_type="WITHIN",
                                                   select_features="buffers")
            count = arcpy.GetCount_management("points").getOutput(0)
            cursor_points = arcpy.da.UpdateCursor("points", ['GROUP_ID', 'GROUP_COUNT'])
            for row_point in cursor_points:
                row_point[0] = int(oid)
                row_point[1] = int(count)
                cursor_points.updateRow(row_point)
                print "count = " + str(int(count))
        break
    elif choice == 'n':
        print "Skipping sign post layer update"
        break
    else:
        print "WRONG INPUT!"
        continue

while True:
    choice = raw_input("Space out sign groups ? (Y or N): ").lower()
    if choice == 'y':
        spacingIndex = 0
        groupIDs = set()
        for spacing in spacings:
            if spacingIndex == 0:
                print "Making copy of updated sign layer for first spacing resolution"
                arcpy.Copy_management(in_data=intermediates[1],
                                      out_data=finalOutput_loc)
                print "Adding spacing column to sign layer for querying by resolution"
                arcpy.AddField_management(in_table=finalOutput_loc,
                                          field_name='SPACING_FT',
                                          field_type='SHORT')
                print "Collecting sign group IDs"
                groupIDs_list = []
                scursor_pts = arcpy.da.SearchCursor(finalOutput_loc, ['GROUP_ID'])
                for row_pt in scursor_pts:
                    groupIDs_list.append(row_pt[0])
                groupIDs = set(groupIDs_list)
            else:
                print "Appending another spacing resolution layer to the sign layer"
                arcpy.Append_management(inputs=intermediates[1],
                                        target=finalOutput_loc,
                                        schema_type='NO_TEST')

            print "assigning Spacing value '" + str(spacing) + "' to signs"
            # select rows with empty 'SPACING_FT' field to assign the current spacing value
            arcpy.MakeFeatureLayer_management(in_features=finalOutput_loc,
                                              out_layer="streetSigns")
            arcpy.SelectLayerByAttribute_management(in_layer_or_view="streetSigns",
                                                    selection_type="NEW_SELECTION",
                                                    where_clause='"SPACING_FT" IS NULL')
            arcpy.CalculateField_management(in_table="streetSigns",
                                            field="SPACING_FT",
                                            expression=spacing)

            print "Spacing out sign groups"
            # set these:
            xOffset = spacing
            ySpacing = spacing

            for groupID in groupIDs:
                query_expression = '"GROUP_ID" = %s AND "SPACING_FT" = %s' % (groupID, spacing)

                # first each group is analyzed for total count and for its x and y values
                scursor_groupPts = arcpy.da.SearchCursor(in_table=finalOutput_loc,
                                                         field_names=["SHAPE@XY"],
                                                         where_clause=query_expression)
                count = 0
                xVal = 0
                yVals = []
                for row_point in scursor_groupPts:
                    count += 1
                    x, y = row_point[0]
                    xVal = x
                    yVals.append(y)

                # groups with 0 or 1 members are skipped
                if count == 0:
                    print "ERROR: ZERO COUNT FOUND FOR GROUP"
                elif count == 1:
                    continue

                # groups with 2 or more members are then processed
                else:
                    # add x offset
                    xVal += xOffset
                    # yVals collected in the searchCursor are spread out and then applied within the Update cursor
                    newYVals = spreadOutValuesOnYAxis(yVals, ySpacing)
                    with arcpy.da.UpdateCursor(in_table=finalOutput_loc,
                                               field_names=["SHAPE@XY"],
                                               where_clause=query_expression) as ucursor_groupPts:
                        pointIndex = 0
                        print "NEW GROUP : #" + str(groupID)
                        for row_point in ucursor_groupPts:
                            pnt = arcpy.Point()
                            pnt.X = xVal
                            pnt.Y = newYVals[pointIndex]
                            print [pnt.X, pnt.Y]
                            row_point[0] = pnt
                            ucursor_groupPts.updateRow(row_point)
                            pointIndex += 1
            spacingIndex += 1
        break
    elif choice == 'n':
        print "Skipping sign group spacing"
        break
    else:
        print "WRONG INPUT!"
        continue
