from airspace.sources import AixmSource

source = AixmSource("./airspace/tests/aixm_4.5_extract.xml")
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
