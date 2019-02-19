from airspace.sources import AixmSource

source = AixmSource("./airspace/tests/aixm_4.5_extract.xml")
print(source.list_air_spaces())
for air_space in source.get_air_spaces():
    for crossing in air_space.border_crossings:
        print("found " + crossing.related_border_name + " in " + air_space.text_name + " : ")
        for point in crossing.common_points:
            print(str(point.get_float_lat()) + ", " + str(point.get_float_lon()) + '\n')
