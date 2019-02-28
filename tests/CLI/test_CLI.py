from unittest import TestCase

from CLI.helpers import AirspaceHelper
from airspace.sources import AixmSource


class TestCLI(TestCase):
    source = None

    def __init__(self, *args, **kwargs):
        super(TestCLI, self).__init__(*args, **kwargs)


    def test_list_borders(self):
        source = AixmSource('airspace/tests/aixm_4.5_extract.xml')
        challenge = """+----------------+-------------+
|  Border Name   | Border UUID |
+----------------+-------------+
| BELGIUM_FRANCE |   19048558  |
+----------------+-------------+"""
        payload = str(AirspaceHelper.list_borders(source))
        self.assertEqual(payload, challenge)

    def test_list_airspaces(self):
        source = AixmSource('airspace/tests/aixm_4.5_extract.xml')
        challenge = """+---------------+-----------------+-------------------+
| Airspace Name |  Airspace UUID  |   Border crossed  |
+---------------+-----------------+-------------------+
|  ARDENNES 05  |    100760256    |      19048558     |
|    LESSIVE    | 400001601922575 | no border crossed |
+---------------+-----------------+-------------------+"""
        payload = str(AirspaceHelper.list_airspaces(source))
        self.assertEqual(payload, challenge)

    def test_extract_borders(self):
        source = AixmSource('airspace/tests/aixm_4.5_extract.xml')
        challenge = """# border crossing 1 : BELGIUM_FRANCE(19048558)

DP 49:33:41N 005:45:30E DP 49:33:30N 005:45:35E DP 49:33:22N 005:45:21E DP 49:33:01N 005:45:29E DP 49:32:46N 005:45:21E DP 49:32:34N 005:45:28E DP 49:32:21N 005:44:50E DP 49:32:20N 005:44:24E DP 49:32:37N 005:43:59E DP 49:32:44N 005:44:02E DP 49:32:37N 005:43:33E DP 49:32:38N 005:43:27E DP 49:32:30N 005:43:24E DP 49:32:21N 005:43:07E DP 49:32:24N 005:43:05E DP 49:32:20N 005:42:54E DP 49:32:26N 005:42:49E DP 49:32:20N 005:42:25E DP 49:32:26N 005:41:55E DP 49:32:32N 005:41:58E DP 49:32:35N 005:41:41E DP 49:32:45N 005:41:26E DP 49:32:43N 005:40:52E DP 49:32:52N 005:40:55E DP 49:32:56N 005:40:45E DP 49:32:54N 005:40:09E DP 49:33:10N 005:39:51E DP 49:33:11N 005:39:40E DP 49:33:02N 005:39:14E DP 49:33:04N 005:39:02E DP 49:32:59N 005:38:53E DP 49:33:01N 005:38:33E DP 49:32:49N 005:38:37E DP 49:32:39N 005:38:01E DP 49:32:34N 005:38:04E DP 49:32:31N 005:37:50E DP 49:32:21N 005:37:58E DP 49:32:18N 005:37:42E DP 49:32:04N 005:37:19E DP 49:31:38N 005:36:56E DP 49:31:22N 005:37:14E DP 49:31:08N 005:37:17E DP 49:30:21N 005:36:39E DP 49:30:32N 005:36:12E DP 49:30:37N 005:36:16E DP 49:30:47N 005:36:05E DP 49:30:56N 005:36:05E DP 49:31:22N 005:35:28E DP 49:31:17N 005:35:19E DP 49:31:38N 005:34:19E DP 49:31:39N 005:33:58E DP 49:31:31N 005:33:48E DP 49:31:45N 005:33:24E DP 49:31:37N 005:33:00E DP 49:31:25N 005:32:44E DP 49:31:07N 005:32:39E DP 49:30:54N 005:32:27E DP 49:30:53N 005:32:09E DP 49:30:47N 005:32:00E DP 49:30:32N 005:31:02E DP 49:30:24N 005:29:57E DP 49:30:26N 005:29:02E DP 49:30:13N 005:28:48E DP 49:30:01N 005:28:45E DP 49:29:49N 005:28:22E DP 49:29:55N 005:27:58E DP 49:30:13N 005:27:51E DP 49:30:31N 005:27:57E DP 49:30:47N 005:27:24E DP 49:30:44N 005:27:21E DP 49:30:45N 005:27:14E DP 49:30:50N 005:27:15E DP 49:31:05N 005:26:50E DP 49:31:12N 005:27:19E DP 49:31:32N 005:27:37E DP 49:31:32N 005:27:58E DP 49:32:17N 005:27:56E DP 49:33:06N 005:26:29E DP 49:33:10N 005:26:41E DP 49:33:18N 005:26:52E DP 49:34:00N 005:27:24E DP 49:34:01N 005:26:43E DP 49:34:09N 005:26:16E DP 49:35:23N 005:25:43E DP 49:35:33N 005:25:52E DP 49:35:56N 005:25:23E DP 49:35:58N 005:25:04E DP 49:36:29N 005:24:40E DP 49:36:38N 005:24:03E DP 49:36:56N 005:23:53E DP 49:37:04N 005:23:35E DP 49:37:10N 005:22:55E DP 49:37:25N 005:22:28E DP 49:37:21N 005:22:15E DP 49:37:23N 005:21:50E DP 49:37:34N 005:21:42E DP 49:37:39N 005:21:23E DP 49:37:51N 005:21:07E DP 49:37:50N 005:20:46E DP 49:37:35N 005:20:36E DP 49:37:19N 005:20:36E DP 49:37:06N 005:20:21E DP 49:37:00N 005:20:26E DP 49:36:56N 005:20:13E DP 49:37:00N 005:19:50E DP 49:36:58N 005:19:32E DP 49:36:50N 005:19:20E DP 49:36:52N 005:19:07E DP 49:36:40N 005:18:56E DP 49:36:41N 005:18:44E DP 49:37:06N 005:18:39E DP 49:37:26N 005:18:19E DP 49:37:49N 005:18:18E DP 49:38:10N 005:18:32E DP 49:38:40N 005:19:08E DP 49:38:46N 005:19:05E DP 49:39:10N 005:19:56E DP 49:39:31N 005:19:41E DP 49:40:09N 005:18:39E DP 49:40:18N 005:18:33E DP 49:40:35N 005:17:44E DP 49:40:44N 005:17:33E DP 49:40:56N 005:17:10E DP 49:41:08N 005:16:57E DP 49:41:18N 005:16:53E """
        payload = AirspaceHelper.extract_borders('100760256', source)

        self.assertEqual(payload, challenge)

        challenge = """airspace uuid : 400001601922575 does not cross any border."""
        payload = AirspaceHelper.extract_borders('400001601922575', source)
        self.assertEqual(payload, challenge)

        challenge = """was not able to find airspace uuid : unknown"""
        payload = AirspaceHelper.extract_borders('unknown', source)
        self.assertEqual(payload, challenge)
