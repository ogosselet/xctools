import argparse

from airspace.sources import AixmSource

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Aixm source file")
parser.add_argument("-lb", "--list_borders", help="List borders contained in the source file", action="store_true")
parser.add_argument("-la", "--list_airspaces", help="List airspaces contained in the source file", action="store_true")
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
        print(air_space.text_name + " => " + str(air_space.uuid)) + " " + crossing_list
