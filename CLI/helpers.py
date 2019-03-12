from prettytable import PrettyTable


class AirspaceHelper:

    @staticmethod
    def list_borders(source):
        table = PrettyTable(['Border Name', 'Border UUID'])
        for border in source.get_borders():
            table.add_row([border.text_name, str(border.uuid)])
        return table

    @staticmethod
    def list_airspaces(source):
        table = PrettyTable(['Airspace Name', 'Airspace UUID', 'Border crossed'])
        for air_space in source.get_air_spaces():
            if len(air_space.border_crossings) > 0:
                crossing_list = ""
                for crossing in air_space.border_crossings:
                    if crossing_list == "":
                        crossing_list += str(crossing.related_border_uuid)
                    else:
                        crossing_list += ", " + str(crossing.related_border_uuid)
            else:
                crossing_list = "no border crossed"
            table.add_row([air_space.text_name, str(air_space.uuid), crossing_list])
        return table

    @staticmethod
    def extract_borders(airspace_uuid, source):
        output = ""
        ais = source.get_air_space(airspace_uuid)
        if ais is not None:
            if len(ais.border_crossings) > 0:
                cpt = 1
                for crossing in ais.border_crossings:
                    output += '# border crossing ' + str(
                        cpt) + ' : ' + crossing.related_border_name + '(' + crossing.related_border_uuid + ')\n'
                    output += '\n'
                    pts_txt = ""
                    for pt in crossing.common_points:
                        pts_txt += "DP " + pt.get_oa_lat() + " " + pt.get_oa_lon() + '\n'
                    output += pts_txt
                    cpt += 1
            else:
                output = 'airspace uuid : ' + airspace_uuid + " does not cross any border."
        else:
            output = 'was not able to find airspace uuid : ' + airspace_uuid

        return output
