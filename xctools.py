import argparse

from airspace.sources import AixmSource

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Aixm source file")
parser.add_argument("-lb", "--list_borders", help="List borders contained in the source file", action="store_true")
parser.add_argument("-la", "--list_airspaces", help="List airspaces contained in the source file", action="store_true")
parser.add_argument("-eb", "--extract_borders", help="Extract borders from given airspace")
args = parser.parse_args()

source = AixmSource(args.file)

if args.list_borders:
    for border in source.get_borders():
        print(border.text_name + " => " + str(border.uuid))

if args.list_airspaces:
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

print(args.extract_borders)
if not args.extract_borders == "":
    ais = source.get_air_space(args.extract_borders)
    if ais is not None:
        if len(ais.border_crossings) > 0:
            cpt = 1
            for crossing in ais.border_crossings:
                print('# border crossing ' + str(
                    cpt) + ' : ' + crossing.related_border_name + '(' + crossing.related_border_uuid + ')')
                print('')
                pts_txt = ""
                for pt in crossing.common_points:
                    pts_txt += "DP " + pt.get_dms_lat() + " " + pt.get_dms_lon() + " "
                cpt += 1
        else:
            print('airspace uuid : ' + args.extract_borders + " does not cross any border.")
    else:
        print('was not able to find airspace uuid : ' + args.extract_borders)
