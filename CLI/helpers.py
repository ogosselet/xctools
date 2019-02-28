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
