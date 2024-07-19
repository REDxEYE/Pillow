/*
 * The Python Imaging Library.
 * $Id$
 *
 * code to convert YCbCr data
 *
 * history:
 * 98-07-01 hk Created
 *
 * Copyright (c) Secret Labs AB 1998
 *
 * See the README file for information on usage and redistribution.
 */

#include "Imaging.h"

/*  JPEG/JFIF YCbCr conversions

    Y  = R *  0.29900 + G *  0.58700 + B *  0.11400
    Cb = R * -0.16874 + G * -0.33126 + B *  0.50000 + 128
    Cr = R *  0.50000 + G * -0.41869 + B * -0.08131 + 128

    R  = Y +                       + (Cr - 128) *  1.40200
    G  = Y + (Cb - 128) * -0.34414 + (Cr - 128) * -0.71414
    B  = Y + (Cb - 128) *  1.77200

*/

#define SCALE 6 /* bits */

static INT16 Y_R[] = {
    0,    19,   38,   57,   77,   96,   115,  134,  153,  172,  191,  210,  230,  249,
    268,  287,  306,  325,  344,  364,  383,  402,  421,  440,  459,  478,  498,  517,
    536,  555,  574,  593,  612,  631,  651,  670,  689,  708,  727,  746,  765,  785,
    804,  823,  842,  861,  880,  899,  919,  938,  957,  976,  995,  1014, 1033, 1052,
    1072, 1091, 1110, 1129, 1148, 1167, 1186, 1206, 1225, 1244, 1263, 1282, 1301, 1320,
    1340, 1359, 1378, 1397, 1416, 1435, 1454, 1473, 1493, 1512, 1531, 1550, 1569, 1588,
    1607, 1627, 1646, 1665, 1684, 1703, 1722, 1741, 1761, 1780, 1799, 1818, 1837, 1856,
    1875, 1894, 1914, 1933, 1952, 1971, 1990, 2009, 2028, 2048, 2067, 2086, 2105, 2124,
    2143, 2162, 2182, 2201, 2220, 2239, 2258, 2277, 2296, 2315, 2335, 2354, 2373, 2392,
    2411, 2430, 2449, 2469, 2488, 2507, 2526, 2545, 2564, 2583, 2602, 2622, 2641, 2660,
    2679, 2698, 2717, 2736, 2756, 2775, 2794, 2813, 2832, 2851, 2870, 2890, 2909, 2928,
    2947, 2966, 2985, 3004, 3023, 3043, 3062, 3081, 3100, 3119, 3138, 3157, 3177, 3196,
    3215, 3234, 3253, 3272, 3291, 3311, 3330, 3349, 3368, 3387, 3406, 3425, 3444, 3464,
    3483, 3502, 3521, 3540, 3559, 3578, 3598, 3617, 3636, 3655, 3674, 3693, 3712, 3732,
    3751, 3770, 3789, 3808, 3827, 3846, 3865, 3885, 3904, 3923, 3942, 3961, 3980, 3999,
    4019, 4038, 4057, 4076, 4095, 4114, 4133, 4153, 4172, 4191, 4210, 4229, 4248, 4267,
    4286, 4306, 4325, 4344, 4363, 4382, 4401, 4420, 4440, 4459, 4478, 4497, 4516, 4535,
    4554, 4574, 4593, 4612, 4631, 4650, 4669, 4688, 4707, 4727, 4746, 4765, 4784, 4803,
    4822, 4841, 4861, 4880
};

static INT16 Y_G[] = {
    0,    38,   75,   113,  150,  188,  225,  263,  301,  338,  376,  413,  451,  488,
    526,  564,  601,  639,  676,  714,  751,  789,  826,  864,  902,  939,  977,  1014,
    1052, 1089, 1127, 1165, 1202, 1240, 1277, 1315, 1352, 1390, 1428, 1465, 1503, 1540,
    1578, 1615, 1653, 1691, 1728, 1766, 1803, 1841, 1878, 1916, 1954, 1991, 2029, 2066,
    2104, 2141, 2179, 2217, 2254, 2292, 2329, 2367, 2404, 2442, 2479, 2517, 2555, 2592,
    2630, 2667, 2705, 2742, 2780, 2818, 2855, 2893, 2930, 2968, 3005, 3043, 3081, 3118,
    3156, 3193, 3231, 3268, 3306, 3344, 3381, 3419, 3456, 3494, 3531, 3569, 3607, 3644,
    3682, 3719, 3757, 3794, 3832, 3870, 3907, 3945, 3982, 4020, 4057, 4095, 4132, 4170,
    4208, 4245, 4283, 4320, 4358, 4395, 4433, 4471, 4508, 4546, 4583, 4621, 4658, 4696,
    4734, 4771, 4809, 4846, 4884, 4921, 4959, 4997, 5034, 5072, 5109, 5147, 5184, 5222,
    5260, 5297, 5335, 5372, 5410, 5447, 5485, 5522, 5560, 5598, 5635, 5673, 5710, 5748,
    5785, 5823, 5861, 5898, 5936, 5973, 6011, 6048, 6086, 6124, 6161, 6199, 6236, 6274,
    6311, 6349, 6387, 6424, 6462, 6499, 6537, 6574, 6612, 6650, 6687, 6725, 6762, 6800,
    6837, 6875, 6913, 6950, 6988, 7025, 7063, 7100, 7138, 7175, 7213, 7251, 7288, 7326,
    7363, 7401, 7438, 7476, 7514, 7551, 7589, 7626, 7664, 7701, 7739, 7777, 7814, 7852,
    7889, 7927, 7964, 8002, 8040, 8077, 8115, 8152, 8190, 8227, 8265, 8303, 8340, 8378,
    8415, 8453, 8490, 8528, 8566, 8603, 8641, 8678, 8716, 8753, 8791, 8828, 8866, 8904,
    8941, 8979, 9016, 9054, 9091, 9129, 9167, 9204, 9242, 9279, 9317, 9354, 9392, 9430,
    9467, 9505, 9542, 9580
};

static INT16 Y_B[] = {
    0,    7,    15,   22,   29,   36,   44,   51,   58,   66,   73,   80,   88,   95,
    102,  109,  117,  124,  131,  139,  146,  153,  161,  168,  175,  182,  190,  197,
    204,  212,  219,  226,  233,  241,  248,  255,  263,  270,  277,  285,  292,  299,
    306,  314,  321,  328,  336,  343,  350,  358,  365,  372,  379,  387,  394,  401,
    409,  416,  423,  430,  438,  445,  452,  460,  467,  474,  482,  489,  496,  503,
    511,  518,  525,  533,  540,  547,  554,  562,  569,  576,  584,  591,  598,  606,
    613,  620,  627,  635,  642,  649,  657,  664,  671,  679,  686,  693,  700,  708,
    715,  722,  730,  737,  744,  751,  759,  766,  773,  781,  788,  795,  803,  810,
    817,  824,  832,  839,  846,  854,  861,  868,  876,  883,  890,  897,  905,  912,
    919,  927,  934,  941,  948,  956,  963,  970,  978,  985,  992,  1000, 1007, 1014,
    1021, 1029, 1036, 1043, 1051, 1058, 1065, 1073, 1080, 1087, 1094, 1102, 1109, 1116,
    1124, 1131, 1138, 1145, 1153, 1160, 1167, 1175, 1182, 1189, 1197, 1204, 1211, 1218,
    1226, 1233, 1240, 1248, 1255, 1262, 1270, 1277, 1284, 1291, 1299, 1306, 1313, 1321,
    1328, 1335, 1342, 1350, 1357, 1364, 1372, 1379, 1386, 1394, 1401, 1408, 1415, 1423,
    1430, 1437, 1445, 1452, 1459, 1466, 1474, 1481, 1488, 1496, 1503, 1510, 1518, 1525,
    1532, 1539, 1547, 1554, 1561, 1569, 1576, 1583, 1591, 1598, 1605, 1612, 1620, 1627,
    1634, 1642, 1649, 1656, 1663, 1671, 1678, 1685, 1693, 1700, 1707, 1715, 1722, 1729,
    1736, 1744, 1751, 1758, 1766, 1773, 1780, 1788, 1795, 1802, 1809, 1817, 1824, 1831,
    1839, 1846, 1853, 1860
};

static INT16 Cb_R[] = {
    0,     -10,   -21,   -31,   -42,   -53,   -64,   -75,   -85,   -96,   -107,  -118,
    -129,  -139,  -150,  -161,  -172,  -183,  -193,  -204,  -215,  -226,  -237,  -247,
    -258,  -269,  -280,  -291,  -301,  -312,  -323,  -334,  -345,  -355,  -366,  -377,
    -388,  -399,  -409,  -420,  -431,  -442,  -453,  -463,  -474,  -485,  -496,  -507,
    -517,  -528,  -539,  -550,  -561,  -571,  -582,  -593,  -604,  -615,  -625,  -636,
    -647,  -658,  -669,  -679,  -690,  -701,  -712,  -723,  -733,  -744,  -755,  -766,
    -777,  -787,  -798,  -809,  -820,  -831,  -841,  -852,  -863,  -874,  -885,  -895,
    -906,  -917,  -928,  -939,  -949,  -960,  -971,  -982,  -993,  -1003, -1014, -1025,
    -1036, -1047, -1057, -1068, -1079, -1090, -1101, -1111, -1122, -1133, -1144, -1155,
    -1165, -1176, -1187, -1198, -1209, -1219, -1230, -1241, -1252, -1263, -1273, -1284,
    -1295, -1306, -1317, -1327, -1338, -1349, -1360, -1371, -1381, -1392, -1403, -1414,
    -1425, -1435, -1446, -1457, -1468, -1479, -1489, -1500, -1511, -1522, -1533, -1543,
    -1554, -1565, -1576, -1587, -1597, -1608, -1619, -1630, -1641, -1651, -1662, -1673,
    -1684, -1694, -1705, -1716, -1727, -1738, -1748, -1759, -1770, -1781, -1792, -1802,
    -1813, -1824, -1835, -1846, -1856, -1867, -1878, -1889, -1900, -1910, -1921, -1932,
    -1943, -1954, -1964, -1975, -1986, -1997, -2008, -2018, -2029, -2040, -2051, -2062,
    -2072, -2083, -2094, -2105, -2116, -2126, -2137, -2148, -2159, -2170, -2180, -2191,
    -2202, -2213, -2224, -2234, -2245, -2256, -2267, -2278, -2288, -2299, -2310, -2321,
    -2332, -2342, -2353, -2364, -2375, -2386, -2396, -2407, -2418, -2429, -2440, -2450,
    -2461, -2472, -2483, -2494, -2504, -2515, -2526, -2537, -2548, -2558, -2569, -2580,
    -2591, -2602, -2612, -2623, -2634, -2645, -2656, -2666, -2677, -2688, -2699, -2710,
    -2720, -2731, -2742, -2753
};

static INT16 Cb_G[] = {
    0,     -20,   -41,   -63,   -84,   -105,  -126,  -147,  -169,  -190,  -211,  -232,
    -253,  -275,  -296,  -317,  -338,  -359,  -381,  -402,  -423,  -444,  -465,  -487,
    -508,  -529,  -550,  -571,  -593,  -614,  -635,  -656,  -677,  -699,  -720,  -741,
    -762,  -783,  -805,  -826,  -847,  -868,  -889,  -911,  -932,  -953,  -974,  -995,
    -1017, -1038, -1059, -1080, -1101, -1123, -1144, -1165, -1186, -1207, -1229, -1250,
    -1271, -1292, -1313, -1335, -1356, -1377, -1398, -1419, -1441, -1462, -1483, -1504,
    -1525, -1547, -1568, -1589, -1610, -1631, -1653, -1674, -1695, -1716, -1737, -1759,
    -1780, -1801, -1822, -1843, -1865, -1886, -1907, -1928, -1949, -1971, -1992, -2013,
    -2034, -2055, -2077, -2098, -2119, -2140, -2161, -2183, -2204, -2225, -2246, -2267,
    -2289, -2310, -2331, -2352, -2373, -2395, -2416, -2437, -2458, -2479, -2501, -2522,
    -2543, -2564, -2585, -2607, -2628, -2649, -2670, -2691, -2713, -2734, -2755, -2776,
    -2797, -2819, -2840, -2861, -2882, -2903, -2925, -2946, -2967, -2988, -3009, -3031,
    -3052, -3073, -3094, -3115, -3137, -3158, -3179, -3200, -3221, -3243, -3264, -3285,
    -3306, -3328, -3349, -3370, -3391, -3412, -3434, -3455, -3476, -3497, -3518, -3540,
    -3561, -3582, -3603, -3624, -3646, -3667, -3688, -3709, -3730, -3752, -3773, -3794,
    -3815, -3836, -3858, -3879, -3900, -3921, -3942, -3964, -3985, -4006, -4027, -4048,
    -4070, -4091, -4112, -4133, -4154, -4176, -4197, -4218, -4239, -4260, -4282, -4303,
    -4324, -4345, -4366, -4388, -4409, -4430, -4451, -4472, -4494, -4515, -4536, -4557,
    -4578, -4600, -4621, -4642, -4663, -4684, -4706, -4727, -4748, -4769, -4790, -4812,
    -4833, -4854, -4875, -4896, -4918, -4939, -4960, -4981, -5002, -5024, -5045, -5066,
    -5087, -5108, -5130, -5151, -5172, -5193, -5214, -5236, -5257, -5278, -5299, -5320,
    -5342, -5363, -5384, -5405
};

static INT16 Cb_B[] = {
    0,    32,   64,   96,   128,  160,  192,  224,  256,  288,  320,  352,  384,  416,
    448,  480,  512,  544,  576,  608,  640,  672,  704,  736,  768,  800,  832,  864,
    896,  928,  960,  992,  1024, 1056, 1088, 1120, 1152, 1184, 1216, 1248, 1280, 1312,
    1344, 1376, 1408, 1440, 1472, 1504, 1536, 1568, 1600, 1632, 1664, 1696, 1728, 1760,
    1792, 1824, 1856, 1888, 1920, 1952, 1984, 2016, 2048, 2080, 2112, 2144, 2176, 2208,
    2240, 2272, 2304, 2336, 2368, 2400, 2432, 2464, 2496, 2528, 2560, 2592, 2624, 2656,
    2688, 2720, 2752, 2784, 2816, 2848, 2880, 2912, 2944, 2976, 3008, 3040, 3072, 3104,
    3136, 3168, 3200, 3232, 3264, 3296, 3328, 3360, 3392, 3424, 3456, 3488, 3520, 3552,
    3584, 3616, 3648, 3680, 3712, 3744, 3776, 3808, 3840, 3872, 3904, 3936, 3968, 4000,
    4032, 4064, 4096, 4128, 4160, 4192, 4224, 4256, 4288, 4320, 4352, 4384, 4416, 4448,
    4480, 4512, 4544, 4576, 4608, 4640, 4672, 4704, 4736, 4768, 4800, 4832, 4864, 4896,
    4928, 4960, 4992, 5024, 5056, 5088, 5120, 5152, 5184, 5216, 5248, 5280, 5312, 5344,
    5376, 5408, 5440, 5472, 5504, 5536, 5568, 5600, 5632, 5664, 5696, 5728, 5760, 5792,
    5824, 5856, 5888, 5920, 5952, 5984, 6016, 6048, 6080, 6112, 6144, 6176, 6208, 6240,
    6272, 6304, 6336, 6368, 6400, 6432, 6464, 6496, 6528, 6560, 6592, 6624, 6656, 6688,
    6720, 6752, 6784, 6816, 6848, 6880, 6912, 6944, 6976, 7008, 7040, 7072, 7104, 7136,
    7168, 7200, 7232, 7264, 7296, 7328, 7360, 7392, 7424, 7456, 7488, 7520, 7552, 7584,
    7616, 7648, 7680, 7712, 7744, 7776, 7808, 7840, 7872, 7904, 7936, 7968, 8000, 8032,
    8064, 8096, 8128, 8160
};

#define Cr_R Cb_B

static INT16 Cr_G[] = {
    0,     -26,   -53,   -79,   -106,  -133,  -160,  -187,  -213,  -240,  -267,  -294,
    -321,  -347,  -374,  -401,  -428,  -455,  -481,  -508,  -535,  -562,  -589,  -615,
    -642,  -669,  -696,  -722,  -749,  -776,  -803,  -830,  -856,  -883,  -910,  -937,
    -964,  -990,  -1017, -1044, -1071, -1098, -1124, -1151, -1178, -1205, -1232, -1258,
    -1285, -1312, -1339, -1366, -1392, -1419, -1446, -1473, -1500, -1526, -1553, -1580,
    -1607, -1634, -1660, -1687, -1714, -1741, -1768, -1794, -1821, -1848, -1875, -1902,
    -1928, -1955, -1982, -2009, -2036, -2062, -2089, -2116, -2143, -2169, -2196, -2223,
    -2250, -2277, -2303, -2330, -2357, -2384, -2411, -2437, -2464, -2491, -2518, -2545,
    -2571, -2598, -2625, -2652, -2679, -2705, -2732, -2759, -2786, -2813, -2839, -2866,
    -2893, -2920, -2947, -2973, -3000, -3027, -3054, -3081, -3107, -3134, -3161, -3188,
    -3215, -3241, -3268, -3295, -3322, -3349, -3375, -3402, -3429, -3456, -3483, -3509,
    -3536, -3563, -3590, -3616, -3643, -3670, -3697, -3724, -3750, -3777, -3804, -3831,
    -3858, -3884, -3911, -3938, -3965, -3992, -4018, -4045, -4072, -4099, -4126, -4152,
    -4179, -4206, -4233, -4260, -4286, -4313, -4340, -4367, -4394, -4420, -4447, -4474,
    -4501, -4528, -4554, -4581, -4608, -4635, -4662, -4688, -4715, -4742, -4769, -4796,
    -4822, -4849, -4876, -4903, -4929, -4956, -4983, -5010, -5037, -5063, -5090, -5117,
    -5144, -5171, -5197, -5224, -5251, -5278, -5305, -5331, -5358, -5385, -5412, -5439,
    -5465, -5492, -5519, -5546, -5573, -5599, -5626, -5653, -5680, -5707, -5733, -5760,
    -5787, -5814, -5841, -5867, -5894, -5921, -5948, -5975, -6001, -6028, -6055, -6082,
    -6109, -6135, -6162, -6189, -6216, -6243, -6269, -6296, -6323, -6350, -6376, -6403,
    -6430, -6457, -6484, -6510, -6537, -6564, -6591, -6618, -6644, -6671, -6698, -6725,
    -6752, -6778, -6805, -6832
};

static INT16 Cr_B[] = {
    0,     -4,    -9,    -15,   -20,   -25,   -30,   -35,   -41,   -46,   -51,   -56,
    -61,   -67,   -72,   -77,   -82,   -87,   -93,   -98,   -103,  -108,  -113,  -119,
    -124,  -129,  -134,  -140,  -145,  -150,  -155,  -160,  -166,  -171,  -176,  -181,
    -186,  -192,  -197,  -202,  -207,  -212,  -218,  -223,  -228,  -233,  -238,  -244,
    -249,  -254,  -259,  -264,  -270,  -275,  -280,  -285,  -290,  -296,  -301,  -306,
    -311,  -316,  -322,  -327,  -332,  -337,  -342,  -348,  -353,  -358,  -363,  -368,
    -374,  -379,  -384,  -389,  -394,  -400,  -405,  -410,  -415,  -421,  -426,  -431,
    -436,  -441,  -447,  -452,  -457,  -462,  -467,  -473,  -478,  -483,  -488,  -493,
    -499,  -504,  -509,  -514,  -519,  -525,  -530,  -535,  -540,  -545,  -551,  -556,
    -561,  -566,  -571,  -577,  -582,  -587,  -592,  -597,  -603,  -608,  -613,  -618,
    -623,  -629,  -634,  -639,  -644,  -649,  -655,  -660,  -665,  -670,  -675,  -681,
    -686,  -691,  -696,  -702,  -707,  -712,  -717,  -722,  -728,  -733,  -738,  -743,
    -748,  -754,  -759,  -764,  -769,  -774,  -780,  -785,  -790,  -795,  -800,  -806,
    -811,  -816,  -821,  -826,  -832,  -837,  -842,  -847,  -852,  -858,  -863,  -868,
    -873,  -878,  -884,  -889,  -894,  -899,  -904,  -910,  -915,  -920,  -925,  -930,
    -936,  -941,  -946,  -951,  -957,  -962,  -967,  -972,  -977,  -983,  -988,  -993,
    -998,  -1003, -1009, -1014, -1019, -1024, -1029, -1035, -1040, -1045, -1050, -1055,
    -1061, -1066, -1071, -1076, -1081, -1087, -1092, -1097, -1102, -1107, -1113, -1118,
    -1123, -1128, -1133, -1139, -1144, -1149, -1154, -1159, -1165, -1170, -1175, -1180,
    -1185, -1191, -1196, -1201, -1206, -1211, -1217, -1222, -1227, -1232, -1238, -1243,
    -1248, -1253, -1258, -1264, -1269, -1274, -1279, -1284, -1290, -1295, -1300, -1305,
    -1310, -1316, -1321, -1326
};

static INT16 R_Cr[] = {
    -11484, -11394, -11305, -11215, -11125, -11036, -10946, -10856, -10766, -10677,
    -10587, -10497, -10407, -10318, -10228, -10138, -10049, -9959,  -9869,  -9779,
    -9690,  -9600,  -9510,  -9420,  -9331,  -9241,  -9151,  -9062,  -8972,  -8882,
    -8792,  -8703,  -8613,  -8523,  -8433,  -8344,  -8254,  -8164,  -8075,  -7985,
    -7895,  -7805,  -7716,  -7626,  -7536,  -7446,  -7357,  -7267,  -7177,  -7088,
    -6998,  -6908,  -6818,  -6729,  -6639,  -6549,  -6459,  -6370,  -6280,  -6190,
    -6101,  -6011,  -5921,  -5831,  -5742,  -5652,  -5562,  -5472,  -5383,  -5293,
    -5203,  -5113,  -5024,  -4934,  -4844,  -4755,  -4665,  -4575,  -4485,  -4396,
    -4306,  -4216,  -4126,  -4037,  -3947,  -3857,  -3768,  -3678,  -3588,  -3498,
    -3409,  -3319,  -3229,  -3139,  -3050,  -2960,  -2870,  -2781,  -2691,  -2601,
    -2511,  -2422,  -2332,  -2242,  -2152,  -2063,  -1973,  -1883,  -1794,  -1704,
    -1614,  -1524,  -1435,  -1345,  -1255,  -1165,  -1076,  -986,   -896,   -807,
    -717,   -627,   -537,   -448,   -358,   -268,   -178,   -89,    0,      90,
    179,    269,    359,    449,    538,    628,    718,    808,    897,    987,
    1077,   1166,   1256,   1346,   1436,   1525,   1615,   1705,   1795,   1884,
    1974,   2064,   2153,   2243,   2333,   2423,   2512,   2602,   2692,   2782,
    2871,   2961,   3051,   3140,   3230,   3320,   3410,   3499,   3589,   3679,
    3769,   3858,   3948,   4038,   4127,   4217,   4307,   4397,   4486,   4576,
    4666,   4756,   4845,   4935,   5025,   5114,   5204,   5294,   5384,   5473,
    5563,   5653,   5743,   5832,   5922,   6012,   6102,   6191,   6281,   6371,
    6460,   6550,   6640,   6730,   6819,   6909,   6999,   7089,   7178,   7268,
    7358,   7447,   7537,   7627,   7717,   7806,   7896,   7986,   8076,   8165,
    8255,   8345,   8434,   8524,   8614,   8704,   8793,   8883,   8973,   9063,
    9152,   9242,   9332,   9421,   9511,   9601,   9691,   9780,   9870,   9960,
    10050,  10139,  10229,  10319,  10408,  10498,  10588,  10678,  10767,  10857,
    10947,  11037,  11126,  11216,  11306,  11395
};

static INT16 G_Cb[] = {
    2819,  2797,  2775,  2753,  2731,  2709,  2687,  2665,  2643,  2621,  2599,  2577,
    2555,  2533,  2511,  2489,  2467,  2445,  2423,  2401,  2379,  2357,  2335,  2313,
    2291,  2269,  2247,  2225,  2202,  2180,  2158,  2136,  2114,  2092,  2070,  2048,
    2026,  2004,  1982,  1960,  1938,  1916,  1894,  1872,  1850,  1828,  1806,  1784,
    1762,  1740,  1718,  1696,  1674,  1652,  1630,  1608,  1586,  1564,  1542,  1520,
    1498,  1476,  1454,  1432,  1410,  1388,  1366,  1344,  1321,  1299,  1277,  1255,
    1233,  1211,  1189,  1167,  1145,  1123,  1101,  1079,  1057,  1035,  1013,  991,
    969,   947,   925,   903,   881,   859,   837,   815,   793,   771,   749,   727,
    705,   683,   661,   639,   617,   595,   573,   551,   529,   507,   485,   463,
    440,   418,   396,   374,   352,   330,   308,   286,   264,   242,   220,   198,
    176,   154,   132,   110,   88,    66,    44,    22,    0,     -21,   -43,   -65,
    -87,   -109,  -131,  -153,  -175,  -197,  -219,  -241,  -263,  -285,  -307,  -329,
    -351,  -373,  -395,  -417,  -439,  -462,  -484,  -506,  -528,  -550,  -572,  -594,
    -616,  -638,  -660,  -682,  -704,  -726,  -748,  -770,  -792,  -814,  -836,  -858,
    -880,  -902,  -924,  -946,  -968,  -990,  -1012, -1034, -1056, -1078, -1100, -1122,
    -1144, -1166, -1188, -1210, -1232, -1254, -1276, -1298, -1320, -1343, -1365, -1387,
    -1409, -1431, -1453, -1475, -1497, -1519, -1541, -1563, -1585, -1607, -1629, -1651,
    -1673, -1695, -1717, -1739, -1761, -1783, -1805, -1827, -1849, -1871, -1893, -1915,
    -1937, -1959, -1981, -2003, -2025, -2047, -2069, -2091, -2113, -2135, -2157, -2179,
    -2201, -2224, -2246, -2268, -2290, -2312, -2334, -2356, -2378, -2400, -2422, -2444,
    -2466, -2488, -2510, -2532, -2554, -2576, -2598, -2620, -2642, -2664, -2686, -2708,
    -2730, -2752, -2774, -2796
};

static INT16 G_Cr[] = {
    5850,  5805,  5759,  5713,  5667,  5622,  5576,  5530,  5485,  5439,  5393,  5347,
    5302,  5256,  5210,  5165,  5119,  5073,  5028,  4982,  4936,  4890,  4845,  4799,
    4753,  4708,  4662,  4616,  4570,  4525,  4479,  4433,  4388,  4342,  4296,  4251,
    4205,  4159,  4113,  4068,  4022,  3976,  3931,  3885,  3839,  3794,  3748,  3702,
    3656,  3611,  3565,  3519,  3474,  3428,  3382,  3336,  3291,  3245,  3199,  3154,
    3108,  3062,  3017,  2971,  2925,  2879,  2834,  2788,  2742,  2697,  2651,  2605,
    2559,  2514,  2468,  2422,  2377,  2331,  2285,  2240,  2194,  2148,  2102,  2057,
    2011,  1965,  1920,  1874,  1828,  1782,  1737,  1691,  1645,  1600,  1554,  1508,
    1463,  1417,  1371,  1325,  1280,  1234,  1188,  1143,  1097,  1051,  1006,  960,
    914,   868,   823,   777,   731,   686,   640,   594,   548,   503,   457,   411,
    366,   320,   274,   229,   183,   137,   91,    46,    0,     -45,   -90,   -136,
    -182,  -228,  -273,  -319,  -365,  -410,  -456,  -502,  -547,  -593,  -639,  -685,
    -730,  -776,  -822,  -867,  -913,  -959,  -1005, -1050, -1096, -1142, -1187, -1233,
    -1279, -1324, -1370, -1416, -1462, -1507, -1553, -1599, -1644, -1690, -1736, -1781,
    -1827, -1873, -1919, -1964, -2010, -2056, -2101, -2147, -2193, -2239, -2284, -2330,
    -2376, -2421, -2467, -2513, -2558, -2604, -2650, -2696, -2741, -2787, -2833, -2878,
    -2924, -2970, -3016, -3061, -3107, -3153, -3198, -3244, -3290, -3335, -3381, -3427,
    -3473, -3518, -3564, -3610, -3655, -3701, -3747, -3793, -3838, -3884, -3930, -3975,
    -4021, -4067, -4112, -4158, -4204, -4250, -4295, -4341, -4387, -4432, -4478, -4524,
    -4569, -4615, -4661, -4707, -4752, -4798, -4844, -4889, -4935, -4981, -5027, -5072,
    -5118, -5164, -5209, -5255, -5301, -5346, -5392, -5438, -5484, -5529, -5575, -5621,
    -5666, -5712, -5758, -5804
};

static INT16 B_Cb[] = {
    -14515, -14402, -14288, -14175, -14062, -13948, -13835, -13721, -13608, -13495,
    -13381, -13268, -13154, -13041, -12928, -12814, -12701, -12587, -12474, -12360,
    -12247, -12134, -12020, -11907, -11793, -11680, -11567, -11453, -11340, -11226,
    -11113, -11000, -10886, -10773, -10659, -10546, -10433, -10319, -10206, -10092,
    -9979,  -9865,  -9752,  -9639,  -9525,  -9412,  -9298,  -9185,  -9072,  -8958,
    -8845,  -8731,  -8618,  -8505,  -8391,  -8278,  -8164,  -8051,  -7938,  -7824,
    -7711,  -7597,  -7484,  -7371,  -7257,  -7144,  -7030,  -6917,  -6803,  -6690,
    -6577,  -6463,  -6350,  -6236,  -6123,  -6010,  -5896,  -5783,  -5669,  -5556,
    -5443,  -5329,  -5216,  -5102,  -4989,  -4876,  -4762,  -4649,  -4535,  -4422,
    -4309,  -4195,  -4082,  -3968,  -3855,  -3741,  -3628,  -3515,  -3401,  -3288,
    -3174,  -3061,  -2948,  -2834,  -2721,  -2607,  -2494,  -2381,  -2267,  -2154,
    -2040,  -1927,  -1814,  -1700,  -1587,  -1473,  -1360,  -1246,  -1133,  -1020,
    -906,   -793,   -679,   -566,   -453,   -339,   -226,   -112,   0,      113,
    227,    340,    454,    567,    680,    794,    907,    1021,   1134,   1247,
    1361,   1474,   1588,   1701,   1815,   1928,   2041,   2155,   2268,   2382,
    2495,   2608,   2722,   2835,   2949,   3062,   3175,   3289,   3402,   3516,
    3629,   3742,   3856,   3969,   4083,   4196,   4310,   4423,   4536,   4650,
    4763,   4877,   4990,   5103,   5217,   5330,   5444,   5557,   5670,   5784,
    5897,   6011,   6124,   6237,   6351,   6464,   6578,   6691,   6804,   6918,
    7031,   7145,   7258,   7372,   7485,   7598,   7712,   7825,   7939,   8052,
    8165,   8279,   8392,   8506,   8619,   8732,   8846,   8959,   9073,   9186,
    9299,   9413,   9526,   9640,   9753,   9866,   9980,   10093,  10207,  10320,
    10434,  10547,  10660,  10774,  10887,  11001,  11114,  11227,  11341,  11454,
    11568,  11681,  11794,  11908,  12021,  12135,  12248,  12361,  12475,  12588,
    12702,  12815,  12929,  13042,  13155,  13269,  13382,  13496,  13609,  13722,
    13836,  13949,  14063,  14176,  14289,  14403
};

void
ImagingConvertRGB2YCbCr(UINT8 *out, const UINT8 *in, int pixels) {
    int x;
    UINT8 a;
    int r, g, b;
    int y, cr, cb;

    for (x = 0; x < pixels; x++, in += 4, out += 4) {
        r = in[0];
        g = in[1];
        b = in[2];
        a = in[3];

        y = (Y_R[r] + Y_G[g] + Y_B[b]) >> SCALE;
        cb = ((Cb_R[r] + Cb_G[g] + Cb_B[b]) >> SCALE) + 128;
        cr = ((Cr_R[r] + Cr_G[g] + Cr_B[b]) >> SCALE) + 128;

        out[0] = (UINT8)y;
        out[1] = (UINT8)cb;
        out[2] = (UINT8)cr;
        out[3] = a;
    }
}

void
ImagingConvertYCbCr2RGB(UINT8 *out, const UINT8 *in, int pixels) {
    int x;
    UINT8 a;
    int r, g, b;
    int y, cr, cb;

    for (x = 0; x < pixels; x++, in += 4, out += 4) {
        y = in[0];
        cb = in[1];
        cr = in[2];
        a = in[3];

        r = y + ((R_Cr[cr]) >> SCALE);
        g = y + ((G_Cb[cb] + G_Cr[cr]) >> SCALE);
        b = y + ((B_Cb[cb]) >> SCALE);

        out[0] = (r <= 0) ? 0 : (r >= 255) ? 255 : r;
        out[1] = (g <= 0) ? 0 : (g >= 255) ? 255 : g;
        out[2] = (b <= 0) ? 0 : (b >= 255) ? 255 : b;
        out[3] = a;
    }
}
