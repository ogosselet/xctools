"""
Author : Ludovic Reenaers (https://github.com/Djang0)
Inspired by the work of Olivier Gosselet (https://github.com/ogosselet/xctools)


This module contains CLI application
"""
import argparse

from airspace.sources import AixmSource

parser = argparse.ArgumentParser(description="Aixm Airspace File CLI parser")
group = parser.add_mutually_exclusive_group()
group.add_argument("-lb", "--list_borders", help="List borders contained in the source file", action="store_true")
group.add_argument("-la", "--list_airspaces", help="List airspaces contained in the source file", action="store_true")
group.add_argument("-ebs", "--extract_borders", help="Extract borders from given airspace", metavar="AIRSPACE_UUID")
group.add_argument("-eb", "--extract_border", help="Extract borders from given airspace", nargs=2,
                   metavar=("AIRSPACE_UUID", "BORDER_UUID"))
group.add_argument("-da", "--dump_airspace", help="Extract airspace geometry in OpenAir format",
                   metavar="AIRSPACE_UUID")
group.add_argument("-ds", "--dump_source", help="Dump source file in OpenAir format", action="store_true")
group.add_argument("-db", "--dump_borders", help="Dump all borders in OpenAir format", action="store_true")
parser.add_argument("file", help="Aixm source file")

args = parser.parse_args()

source = AixmSource(args.file)

if args.list_borders:
    for border in source.get_borders():
        print(border.text_name + " => " + str(border.uuid))

elif args.list_airspaces:
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

elif args.extract_borders is not None:
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
                    pts_txt += "DP " + pt.get_oa_lat() + " " + pt.get_oa_lon() + " "
                print(pts_txt)
                cpt += 1
        else:
            print('airspace uuid : ' + args.extract_borders + " does not cross any border.")
    else:
        print('was not able to find airspace uuid : ' + args.extract_borders)
elif args.dump_airspace is not None:
    ais = source.get_air_space(args.dump_airspace)
    if ais is not None:
        pts_txt = ""
        for point in ais.polygon_points:
            pts_txt += "DP " + point.get_oa_lat() + " " + point.get_oa_lon() + " "
        print(pts_txt)
    else:
        print('was not able to find airspace uuid : ' + args.extract_borders)
elif args.dump_source:
    # TODO : generate appropriate OpenAir output. What about Airspace declaration format?
    pass
elif args.extract_border is not None:
    ais = source.get_air_space(args.extract_border[0])
    if ais is not None:
        crossing = ais.get_border_intersection(args.extract_border[1])
        if crossing is not None:
            pts_txt = ""
            for point in crossing.common_points:
                pts_txt += "DP " + point.get_oa_lat() + " " + point.get_oa_lon() + " "
            print(pts_txt)
    else:
        print('was not able to find airspace uuid : ' + args.extract_borders)
elif args.dump_borders:
    for border in source.get_borders():
        print()
        print("# Dump of border " + border.text_name + " (" + border.uuid + ")")
        print("")
        pts_txt = ""
        for point in border.border_points:
            pts_txt += "DP " + point.get_oa_lat() + " " + point.get_oa_lon() + " "
        print(pts_txt)

else:
    help()
