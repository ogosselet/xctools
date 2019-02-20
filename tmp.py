from airspace.sources import AixmSource

source = AixmSource("./airspace/tests/aixm_4.5_extract.xml")
for border in source.get_borders():
    print(border.text_name + " => " + str(border.uuid))

for air_space in source.get_air_spaces():
    if len(air_space.border_crossings) > 0:
        crossing_list = "(borders : "
        for crossing in air_space.border_crossings:
            if crossing_list == "(borders : ":
                crossing_list += str(crossing.related_border_uuid)
            else:
                crossing_list += ", " + str(crossing.related_border_uuid)
        crossing_list += ")"
    else:
        crossing_list = "(no border crossed)"
    print(air_space.text_name + " => " + str(air_space.uuid) + " " + crossing_list)

ais = source.get_air_space('100760256')
if ais is not None:
    if len(ais.border_crossings) > 0:
        cpt = 1
        for crossing in ais.border_crossings:
            print('# border crossing ' + str(
                cpt) + ' : ' + crossing.related_border_name + '(' + crossing.related_border_uuid + ')')
            print('')
            pts_txt = ""
            for pt in crossing.common_points:
                pts_txt += "DP " + pt.get_oa_lat() + " " + pt.get_oa_lon() + " "
            print(pts_txt)
            cpt += 1
    else:
        print('airspace uuid : 100760256 does not cross any border.')
else:
    print('was not able to find airspace uuid : 100760256')

ais = source.get_air_space('100760256')
if ais is not None:
    pts_txt = ""
    for point in ais.polygon_points:
        pts_txt += "DP " + point.get_oa_lat() + " " + point.get_oa_lon() + " "
    print(pts_txt)
else:
    print('was not able to find airspace uuid : 100760256')

ais = source.get_air_space('100760256')
if ais is not None:
    crossing = ais.get_border_intersection('19048558')
    if crossing is not None:
        pts_txt = ""
        for point in crossing.common_points:
            pts_txt += "DP " + point.get_oa_lat() + " " + point.get_oa_lon() + " "
        print(pts_txt)
else:
    print('was not able to find airspace uuid : ')

for border in source.get_borders():
    print()
    print("# Dump of border " + border.text_name + " (" + border.uuid + ")")
    print("")
    pts_txt = ""
    for point in border.border_points:
        pts_txt += "DP " + point.get_oa_lat() + " " + point.get_oa_lon() + " "
    print(pts_txt)
