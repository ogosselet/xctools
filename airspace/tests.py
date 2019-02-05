'''Testing the briefing module
'''
from __future__ import absolute_import, division, print_function

import unittest
import logging

from .aixm_parser import format_decimal_degree, Airspace, AixmSource, GisPoint

logger = logging.getLogger(__name__)

AIRSPACE_TESTS = [
    {
        'name': 'EBD26',
        'ase_uid': '100760256',
        'gis_data': [[50.42666666666666, 5.095277777777778, '9B07939B'], [50.02166666666667, 5.711388888888889, '201AC5EB'], [49.793055555555554, 5.710277777777778, '2847BD34'], [49.69361111111111, 5.273333333333333, '7A533BA3'], [49.696353, 5.268914, 'A84169C8'], [49.694167, 5.2562, 'FEEED9DF'], [49.688669, 5.250836, 'F41124B3'], [49.68475, 5.242647, '1AE5F988'], [49.688666, 5.24286, '73349539'], [49.691697, 5.23155, 'E97B549C'], [49.687874, 5.218426, 'D169D428'], [49.695829, 5.206409, 'F670E8DC'], [49.693395, 5.201941, '3C5D124C'], [49.691964, 5.196258, '0BF4F67F'], [49.693778, 5.196506, 'AFFDFEBE'], [49.694922, 5.191881, '47583DF0'], [49.69395, 5.184978, 'C7F55381'], [49.693286, 5.164878, 'CD1335DF'], [49.700422, 5.163775, '575F183F'], [49.706933, 5.166392, 'A86D2011'], [49.711811, 5.165919, 'C895E0B1'], [49.716958, 5.159108, '8E65F464'], [49.718486, 5.152664, '25B3CCED'], [49.714278, 5.149814, '0E1260A0'], [49.709303, 5.143639, '03C97E2F'], [49.713009, 5.141136, 'BDAB54AF'], [49.713535, 5.131793, '95974573'], [49.712436, 5.126031, '0D8DD428'], [49.716444, 5.125917, '6AA035C2'], [49.717322, 5.12295, '3AC80558'], [49.726978, 5.124928, 'E7D73DBE'], [49.7356, 5.119058, '5182852E'], [49.738328, 5.119094, '2EE80613'], [49.762771, 5.094722, '6E29CB06'], [49.766425, 5.088047, '0A7F3993'], [49.763142, 5.085383, 'D575722D'], [49.760978, 5.071781, '4806C151'], [49.762153, 5.062908, '33E41624'], [49.76692, 5.061894, '15B3E2C1'], [49.771814, 5.037292, 'CD2A99F8'], [49.7819, 5.008169, '0099D9C5'], [49.786394, 5.006823, '30990888'], [49.793806, 5.000836, '97FCA898'], [49.794692, 4.997395, 'E6FB84AB'], [49.799525, 4.998186, '5D1A077A'], [49.800317, 4.996086, '1B017331'], [49.799736, 4.984386, 'F089978D'], [49.801578, 4.968761, '437A6ECB'], [49.798342, 4.967281, 'F605B6EB'], [49.797772, 4.962447, 'F8606DC5'], [49.801414, 4.956638, 'D2DF6B94'], [49.799042, 4.947611, '8DD9388E'], [49.794511, 4.946467, '86A04A71'], [49.790519, 4.942858, '5633479D'], [49.792639, 4.942078, 'E513347D'], [49.793144, 4.938889, 'F4D858DE'], [49.789836, 4.932025, 'D01857DE'], [49.786839, 4.930614, 'AC9DDE3B'], [49.788692, 4.920828, '7FB1934D'], [49.785453, 4.905822, '21CF9552'], [49.786181, 4.901003, 'C6987964'], [49.789064, 4.898308, '9C84CC6D'], [49.788178, 4.887886, '3F1E54E3'], [49.792864, 4.880428, 'DD0C1FF2'], [49.793561, 4.869947, '40FDEE82'], [49.789342, 4.871339, 'AA443B3D'], [49.788769, 4.864061, '06A16788'], [49.793447, 4.851636, '6235EE3C'], [49.797099, 4.859225, '8F57A2D9'], [49.800902, 4.860404, '5D3C6D12'], [49.805264, 4.864882, 'E4907E89'], [49.813294, 4.865522, '314B376A'], [49.817356, 4.876286, 'F2D73CB9'], [49.819492, 4.876281, 'F6B51350'], [49.822989, 4.868864, 'B83D5BE0'], [49.830686, 4.868806, '9BA827CC'], [49.832853, 4.866167, '7D5EDF61'], [49.834169, 4.869242, 'FA325BF3'], [49.842097, 4.867269, 'F441D348'], [49.841336, 4.856881, 'E2F0E7AC'], [49.846814, 4.857456, 'C0BC944C'], [49.852631, 4.851761, '363784F1'], [49.858878, 4.852006, '100D017F'], [49.865625, 4.850653, '59116E68'], [49.867989, 4.847619, 'C49EF57E'], [49.864706, 4.854411, '1B37E9B3'], [49.865197, 4.85945, '842A3EAA'], [49.867194, 4.862928, 'DE9314A1'], [49.870419, 4.861442, 'F048753B'], [49.878475, 4.866711, '73B29769'], [49.878778, 4.871019, '4F8134FB'], [49.879725, 4.871958, 'CA4E8143'], [49.883842, 4.869428, '34C176B6'], [49.8916, 4.8769, '5EF9F89D'], [49.894606, 4.877872, 'B0D37B01'], [49.896308, 4.884339, '246244D9'], [49.898692, 4.8875, '847B28A2'], [49.901989, 4.884964, 'BDD176D2'], [49.901378, 4.876408, 'BE8C97CF'], [49.905347, 4.879068, '153BF0F6'], [49.905881, 4.887, 'BDD57FCB'], [49.908975, 4.890083, '049DBCC5'], [49.915822, 4.881467, 'F7F3D047'], [49.922394, 4.880953, '5BF602A3'], [49.932842, 4.857768, '75FCCEF1'], [49.946747, 4.849678, '34D70129'], [49.948939, 4.847175, '9A7E9C82'], [49.950767, 4.840003, 'BDB0AC72'], [49.949083, 4.830086, 'F13A8C75'], [49.951186, 4.827192, 'D0E9E838'], [49.951414, 4.821956, '39D32EEF'], [49.954294, 4.812869, '9EEBB46D'], [49.954397, 4.806456, 'BD49BB1B'], [49.958081, 4.79635, '51765BD1'], [49.958025, 4.791042, 'A73BEDB6'], [49.968994, 4.790233, 'AEF53826'], [49.976228, 4.795528, 'EF73B304'], [49.982297, 4.793681, 'AD2F5DFE'], [49.982883, 4.804711, '0F8A228F'], [49.988493, 4.812126, 'EC1D268F'], [49.994679, 4.81894, '8302B6D8'], [50.000178, 4.816026, '3A183F71'], [50.012055, 4.821126, '5A79D8BE'], [50.015336, 4.817308, '7DD94EDB'], [50.019944, 4.818594, 'AF7FB21E'], [50.021764, 4.822619, 'EF51A9DE'], [50.02585, 4.819769, '6E102521'], [50.030033, 4.828089, 'C0F095B4'], [50.034061, 4.830256, 'C7081836'], [50.034808, 4.835672, 'CF465E47'], [50.038753, 4.841783, '10823BCD'], [50.046535, 4.840369, '3934CB20'], [50.04692, 4.83244, '04D2810B'], [50.050302, 4.827126, '90AE3F43'], [50.057408, 4.829278, 'E71397A5'], [50.059178, 4.827456, 'CA9EB206'], [50.060564, 4.8196, '38764A0F'], [50.062089, 4.819197, '777E0220'], [50.064336, 4.82205, '2A15ABCB'], [50.066214, 4.819542, 'A39EDAD5'], [50.067631, 4.837917, 'B364CFDE'], [50.077722, 4.842814, '7C41EF01'], [50.083089, 4.840481, '7B7BEEA4'], [50.083578, 4.846978, '1221647B'], [50.091594, 4.842164, 'E03EEFC0'], [50.093381, 4.838306, '6D2E1F7D'], [50.09516, 4.841107, '76F8C9B2'], [50.098736, 4.849828, '819445F2'], [50.101347, 4.849809, 'CC2CA762'], [50.099947, 4.858719, 'D91C8579'], [50.097031, 4.861744, 'F78031CA'], [50.092974, 4.860211, '6CCBAB5E'], [50.087922, 4.871439, '19B61177'], [50.094828, 4.875325, 'BE6FB628'], [50.096742, 4.868461, '45D7328A'], [50.109131, 4.873261, '58CD376A'], [50.11555555555556, 4.8691666666666675, 'DA2F2D08'], [50.12444444444444, 4.9430555555555555, 'DDE69672'], [50.12477951401513, 4.9457767062878055, 14], [50.12794699317587, 4.9655038120456565, 13], [50.13233906267464, 4.984656278649841, 12], [50.13791375119766, 5.00305091401925, 11], [50.14461776981869, 5.0205116015740545, 10], [50.15238701005394, 5.036870956771864, 9], [50.16114714394858, 5.051971909439093, 8], [50.17081432106705, 5.06566919780122, 7], [50.18129595638465, 5.0778307605583155, 6], [50.19249160223543, 5.088339013897073, 5], [50.20429389666713, 5.097092000986595, 4], [50.216589579795695, 5.104004402284568, 3], [50.229260569046495, 5.109008395889306, 2], [50.24218508352668, 5.112054358222126, 1], [50.25523880720028, 5.113111396515952, 0], [50.25523880720028, 5.113111396515952, 65], [50.25523880720027, 5.113111396515952, 64], [50.26829608004544, 5.112167705924231, 63], [50.2812311059684, 5.109230745546892, 62], [50.29391916594286, 5.104327229292461, 61], [50.306237824642345, 5.097502929247794, 60], [50.3180681187462, 5.088822291095065, 59], [50.3292957151336, 5.078367863080836, 58], [50.33981202733781, 5.06623954207992, 57], [50.34951527892278, 5.052553642380918, 56], [50.35831150286276, 5.037441794917041, 55], [50.36611546655725, 5.021049686741385, 54], [50.37285151279346, 5.003535652563588, 53], [50.37845430777179, 4.985069132083686, 52], [50.38286948823127, 4.965829008644011, 51], [50.38605420073865, 4.9460018463307165, 50], [50.38861111111111, 4.930555555555556, 'DD97AE03']]
    },
    {
        'name': 'EBR28',
        'ase_uid': '400001601922575',
        'gis_data': [[50.12987135359859, 5.168274094395682, 0], [50.1285495738265, 5.168172485760857, 1], [50.12724056019234, 5.167869839711628, 2], [50.125956917669875, 5.167369086812833, 3], [50.124711005935126, 5.166675064254632, 4], [50.12351482043233, 5.165794468704473, 5], [50.12237987698063, 5.1647357913213465, 6], [50.121317101028225, 5.163509235576821, 7], [50.120336722613935, 5.162126618689791, 8], [50.119448178041374, 5.160601257635778, 9], [50.11866001920489, 5.158947840835504, 10], [50.11797983143265, 5.157182286760847, 11], [50.11741416063059, 5.15532159081726, 12], [50.11696845042125, 5.153383661970315, 13], [50.11664698987587, 5.151387150677936, 14], [50.11645287233746, 5.1493512697699995, 15], [50.11638796572598, 5.147295609981364, 16], [50.11645289460832, 5.145239951893191, 17], [50.11664703420335, 5.143204076070337, 18], [50.11696851637886, 5.141207573198855, 19], [50.11741424758377, 5.139269656027831, 20], [50.11797993854477, 5.137408974903136, 21], [50.11866014544537, 5.135643438648111, 22], [50.11944832219545, 5.13399004249715, 23], [50.120336883294435, 5.1324647047238585, 24], [50.121317276688856, 5.131082113525389, 25], [50.122380065930784, 5.129855585630474, 26], [50.123515020853326, 5.128796937990413, 27], [50.12471121589777, 5.127916373790873, 28], [50.12595713515288, 5.127222383889406, 29], [50.12724078310187, 5.126721664639386, 30], [50.12854980001624, 5.126419052907174, 31], [50.12987158089044, 5.126317478927316, 32], [50.1311933967755, 5.1264179374713565, 33], [50.132502517345486, 5.126719477631398, 34], [50.13378633351718, 5.127219211341272, 35], [50.135032478941255, 5.127912340577717, 36], [50.136228949193026, 5.128792203003085, 37], [50.137364217510516, 5.129850335631978, 38], [50.138427345961176, 5.131076555927456, 39], [50.13940809095989, 5.1324590595617305, 40], [50.14029700211533, 5.133984533911551, 41], [50.14108551344563, 5.135638286202299, 42], [50.1417660260765, 5.137404385069403, 43], [50.142331981617836, 5.139265814171353, 44], [50.14277792550473, 5.141204636367716, 45], [50.143099559685844, 5.143202166869645, 46], [50.143293784145435, 5.145239153679601, 47], [50.14335872685462, 5.147295963563526, 48], [50.1432937618593, 5.149352771742722, 49], [50.143099515328416, 5.1513897534549695, 50], [50.14277785950365, 5.153387275515495, 51], [50.142331894609335, 5.155326086008342, 52], [50.14176591889934, 5.157187500257777, 53], [50.1410853871329, 5.158953581266894, 54], [50.14029685788452, 5.160607312866709, 55], [50.13940793020113, 5.162132763892499, 56], [50.13842717022383, 5.163515241794944, 57], [50.1373640284881, 5.164741434199179, 58], [50.13622874870697, 5.165799537046642, 59], [50.135032268923304, 5.166679368087772, 60], [50.13378611599069, 5.167372464639863, 61], [50.132502294405995, 5.167872164680469, 62], [50.131193170570484, 5.168173670510871, 63], [50.12987135359859, 5.168274094395682, 64], [50.12987135359859, 5.168274094395682, 65]]
    }
]

class TestAixmParser(unittest.TestCase):

    def test_format_decimal_degree(self):

        self.assertEqual(
            float(-50.1234),
            format_decimal_degree('050.1234W')
        )
        self.assertEqual(
            float(50.12345),
            format_decimal_degree('050.12345E')
        )
        self.assertEqual(
            float(50.1234),
            format_decimal_degree('50.1234N')
        )
        self.assertEqual(
            float(-50.12345),
            format_decimal_degree('50.12345S')
        )

        self.assertEqual(
            float(-50.12345),
            format_decimal_degree('50.12345S')
        )

        self.assertEqual(
            float('50.172286111111106'),
            format_decimal_degree('501020.23N')
        )

        self.assertEqual(
            float('-50.172286111111106'),
            format_decimal_degree('501020.23S')
        )

        self.assertEqual(
            float('-120.17249722222223'),
            format_decimal_degree('1201020.99W')
        )

        self.assertEqual(
            float('120.17249722222223'),
            format_decimal_degree('1201020.99E')
        )

        self.assertEqual(
            float('90.17222222222223'),
            format_decimal_degree('0901020E')
        )


    def test_airspace_geometry(self):

        aixm_source = AixmSource('./airspace/tests/aixm_4.5_extract.xml')

        for airspace_test in AIRSPACE_TESTS:
            airspace = Airspace(aixm_source, airspace_test['ase_uid'])
            airspace.parse_airspace()
            self.assertEqual(airspace.gis_data, airspace_test['gis_data'])
    # Demonstrates GisPoint equality after truncating precicion
    def test_gis_points(self):
        a =GisPoint (50.1234567890123,4.1234567890123, 52)
        b = GisPoint(50.1234567890023, 4.1234567890023, 52)
        print (a)
        self.assertEqual(a,b)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
