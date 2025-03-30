import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from main import *

#Constantes de projeto relativos ao método dos estados limites 

# Tabela 3 , item 4.9.2.3 da NBR 8800:2024 (combinações últimas normais) 
gamma_a1 = 1.1
gamma_a2 = 1.35
gamma=[gamma_a1,gamma_a2]
#Criação dos objetos de ligação mais utilizados

#Aços

ASTM_A36 = Aço('ASTM A36', 250, 400, 200, 7850)
MR250 = Aço('MR250', 250, 400, 200, 7850)
AR350 = Aço('AR350', 350, 450, 200, 7850)
AR350COR = Aço('AR350COR', 350, 485, 200, 7850) #resistente a corrosão
AR415COR = Aço('AR415COR', 415, 520, 200, 7850) #resistente a corrosão
ASTM_A572 = Aço('ASTM A572', 345, 450, 200, 7850)

espessuras = [1/2, 5/8, 3/4, 7/8, 1, 1.1/8, 1.1/4, 1.3/8, 1.1/2, 1.3/4, 2]

#Parafusos
ASTM_A307 = Parafuso('ASTM A307', None, 415)
ASTM_A325 = Parafuso('ASTM A325', 635, 830)
ASTM_490 = Parafuso('ASTM 490', 895, 1040)


## Diâmetros comerciais dos parafusos

diametros_A307 = ["1/2", "9/16", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8","1.1/2", "1.3/4", "2", "2.1/4", "2.1/2", "2.3/4", "3", "3.1/4","3.1/2", "3.3/4", "4" ]
diametros_A325 = ["1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]
diametros_A490 = ["1/2", "5/8", "3/4", "7/8", "1", "1.1/8", "1.1/4", "1.3/8", "1.1/2", "1.3/4", "2"]

#Soldas

E60XX = Solda('E60XX', 60)
E70XX = Solda('E70XX', 70)
E80XX = Solda('E80XX', 80)

# Comprimento b de cantoneiras

L_1_2x1_8 = Cantoneira("1/2", "1/8")
L_5_8x1_8 = Cantoneira("5/8", "1/8")
L_3_4x1_8 = Cantoneira("3/4", "1/8")
L_7_8x1_8 = Cantoneira("7/8", "1/8")

L_1_2x1_8 = Cantoneira("1/2", "1/8")
L_5_8x1_8 = Cantoneira("5/8", "1/8")
L_3_4x1_8 = Cantoneira("3/4", "1/8")
L_7_8x1_8 = Cantoneira("7/8", "1/8")

# family of 1 inch angles
L_1x1_8   = Cantoneira("1", "1/8")
L_1x3_16  = Cantoneira("1", "3/16")
L_1x1_4   = Cantoneira("1", "1/4")

# family of 1.1/4 inch angles
L_1_1_4x1_8  = Cantoneira("1.1/4", "1/8")
L_1_1_4x3_16 = Cantoneira("1.1/4", "3/16")
L_1_1_4x1_4  = Cantoneira("1.1/4", "1/4")

# family of 1.1/2 inch angles
L_1_1_2x1_8  = Cantoneira("1.1/2", "1/8")
L_1_1_2x3_16 = Cantoneira("1.1/2", "3/16")
L_1_1_2x1_4  = Cantoneira("1.1/2", "1/4")

# family of 1.3/4 inch angles
L_1_3_4x1_8  = Cantoneira("1.3/4", "1/8")
L_1_3_4x3_16 = Cantoneira("1.3/4", "3/16")
L_1_3_4x1_4  = Cantoneira("1.3/4", "1/4")

# family of 2 inch angles
L_2x1_8   = Cantoneira("2", "1/8")
L_2x3_16  = Cantoneira("2", "3/16")
L_2x1_4   = Cantoneira("2", "1/4")
L_2x5_16  = Cantoneira("2", "5/16")
L_2x3_8   = Cantoneira("2", "3/8")

# family of 2.1/2 inch angles
L_2_1_2x3_16 = Cantoneira("2.1/2", "3/16")
L_2_1_2x1_4  = Cantoneira("2.1/2", "1/4")
L_2_1_2x5_16 = Cantoneira("2.1/2", "5/16")
L_2_1_2x3_8  = Cantoneira("2.1/2", "3/8")

# family of 3 inch angles
L_3x3_16 = Cantoneira("3", "3/16")
L_3x1_4  = Cantoneira("3", "1/4")
L_3x5_16 = Cantoneira("3", "5/16")
L_3x3_8  = Cantoneira("3", "3/8")
L_3x1_2  = Cantoneira("3", "1/2")

# family of 3.1/2 inch angles
L_3_1_2x1_4  = Cantoneira("3.1/2", "1/4")
L_3_1_2x5_16 = Cantoneira("3.1/2", "5/16")
L_3_1_2x3_8  = Cantoneira("3.1/2", "3/8")

# family of 4 inch angles
L_4x1_4  = Cantoneira("4", "1/4")
L_4x5_16 = Cantoneira("4", "5/16")
L_4x3_8  = Cantoneira("4", "3/8")
L_4x7_16 = Cantoneira("4", "7/16")
L_4x1_2  = Cantoneira("4", "1/2")

# family of 5 inch angles
L_5x1_4  = Cantoneira("5", "1/4")
L_5x5_16 = Cantoneira("5", "5/16")
L_5x3_8  = Cantoneira("5", "3/8")
L_5x1_2  = Cantoneira("5", "1/2")
L_5x5_8  = Cantoneira("5", "5/8")
L_5x7_16 = Cantoneira("5", "7/16")

# family of 6 inch angles
L_6x3_8  = Cantoneira("6", "3/8")
L_6x1_2  = Cantoneira("6", "1/2")
L_6x5_8  = Cantoneira("6", "5/8")
L_6x3_4  = Cantoneira("6", "3/4")

# family of 8 inch angles
L_8x5_8  = Cantoneira("8", "5/8")
L_8x3_4  = Cantoneira("8", "3/4")

#Dicionário de cantoneiras

cantoneiras_dict = {
    0: L_1_2x1_8,
    1: L_5_8x1_8,
    2: L_3_4x1_8,
    3: L_7_8x1_8,
    4: L_1x1_8,
    5: L_1x3_16,
    6: L_1x1_4,
    7: L_1_1_4x1_8,
    8: L_1_1_4x3_16,
    9: L_1_1_4x1_4,
    10: L_1_1_2x1_8,
    11: L_1_1_2x3_16,
    12: L_1_1_2x1_4,
    13: L_1_3_4x1_8,
    14: L_1_3_4x3_16,
    15: L_1_3_4x1_4,
    16: L_2x1_8,
    17: L_2x3_16,
    18: L_2x1_4,
    19: L_2x5_16,
    20: L_2x3_8,
    21: L_2_1_2x3_16,
    22: L_2_1_2x1_4,
    23: L_2_1_2x5_16,
    24: L_2_1_2x3_8,
    25: L_3x3_16,
    26: L_3x1_4,
    27: L_3x5_16,
    28: L_3x3_8,
    29: L_3x1_2,
    30: L_3_1_2x1_4,
    31: L_3_1_2x5_16,
    32: L_3_1_2x3_8,
    33: L_4x1_4,
    34: L_4x5_16,
    35: L_4x3_8,
    36: L_4x7_16,
    37: L_4x1_2,
    38: L_5x1_4,
    39: L_5x5_16,
    40: L_5x3_8,
    41: L_5x1_2,
    42: L_5x5_8,
    43: L_5x7_16,
    44: L_6x3_8,
    45: L_6x1_2,
    46: L_6x5_8,
    47: L_6x3_4,
    48: L_8x5_8,
    49: L_8x3_4,
}


# Perfis W

W_150x13_0 = Perfil("W_150x13_0", 4.9, 100, 148,4.3)
W_150x18_0 = Perfil("W_150x18_0", 5.8, 102, 153,5.8)
W_150x24_0 = Perfil("W_150x24_0", 10.3, 102, 160,6.6)

W_200x15_0 = Perfil("W_200x15_0", 5.2, 100, 200, 4.3)
W_200x19_3 = Perfil("W_200x19_3", 6.5, 102, 203, 5.8)
W_200x22_5 = Perfil("W_200x22_5", 8.0, 102, 206, 6.2)

W_200x26_6 = Perfil("W_200x26_6", 8.4, 133, 207, 5.8)
W_200x31_3 = Perfil("W_200x31_3", 10.2, 134, 210, 6.4)

W_250x17_9 = Perfil("W_250x17_9", 5.3, 101, 251, 4.8)
W_250x22_3 = Perfil("W_250x22_3", 6.9, 102, 254, 5.8)

W_250x25_3 = Perfil("W_250x25_3", 8.4, 102, 257, 6.1)
W_250x28_4 = Perfil("W_250x28_4", 10, 102, 260, 6.4)

W_250x32_7 = Perfil("W_250x32_7", 9.1, 146, 258, 6.1)
W_250x38_5 = Perfil("W_250x38_5", 11.2, 147, 262, 6.6)
W_250x44_8 = Perfil("W_250x44_8", 13, 148, 266, 7.6)

W_310x21_0 = Perfil("W_310x21_0", 5.7, 101, 303, 5.1)
W_310x23_8 = Perfil("W_310x23_8", 6.7, 101, 305, 5.6)
W_310x28_3 = Perfil("W_310x28_3", 8.9, 102, 309, 6)
W_310x32_7 = Perfil("W_310x32_7", 10.8, 102, 313, 6.6)

W_310x38_7 = Perfil("W_310x38_7", 9.7, 165, 310, 5.8)
W_310x44_5 = Perfil("W_310x44_5", 11.2, 166, 313, 6.6)
W_310x52_0 = Perfil("W_310x52_0", 13.2, 167, 317, 7.6)

W_360x32_9 = Perfil("W_360x32_9", 8.5, 127, 349, 5.8)
W_360x39_0 = Perfil("W_360x39_0", 10.7, 128, 353, 6.5)

W_360x44_6 = Perfil("W_360x44_6", 9.8, 171, 352, 6.9)
W_300x51_0 = Perfil("W_300x51_0", 11.6, 171, 355, 7.2)
W_360x58_0 = Perfil("W_360x58_0", 13.1, 172, 358, 7.9)

W_360x64_0 = Perfil("W_360x64_0", 13.5, 203, 347, 7.7)
W_360x72_0 = Perfil("W_360x72_0", 15.1, 204, 350, 8.6)
W_300x79_0 = Perfil("W_300x79_0", 16.8, 205, 354, 9.4)

W_410x38_8 = Perfil("W_410x38_8", 8.8, 140, 399, 6.4)
W_410x46_1 = Perfil("W_410x46_1", 11.2, 140, 403, 7)

W_410x53_0 = Perfil("W_410x53_0", 10.9, 177, 403, 7.5)
W_410x60_0 = Perfil("W_410x60_0", 12.8, 178, 407, 7.7)
W_410x67_0 = Perfil("W_410x67_0", 14.4, 179, 410, 8.8)
W_410x75_0 = Perfil("W_410x75_0", 16, 180, 413, 9.7)
W_410x85_0 = Perfil("W_410x85_0", 18.2, 181, 417, 10.9)

W_460x52_0 = Perfil("W_460x52_0", 10.8 , 152, 450, 7.6)
W_460x60_0 = Perfil("W_460x60_0", 13.3 , 153, 455, 8)
W_460x68_0 = Perfil("W_460x68_0", 15.4 , 154, 459, 9.1)

W_460x74_0 = Perfil("W_460x74_0", 14.5 , 190, 457, 9)
W_460x82_0 = Perfil("W_460x82_0", 16  , 191, 460, 9.9)
W_460x89_0 = Perfil("W_460x89_0", 17.7 , 192, 463, 10.5)

W_530x66_0 = Perfil("W_530x66_0", 11.4, 165, 525, 8.9)
W_530x74_0 = Perfil("W_530x74_0", 13.6, 165, 529, 9.7)
W_530x85_0 = Perfil("W_530x85_0", 16.5, 166, 535, 10.3)

W_460x97_0 = Perfil("W_460x97_0", 19 , 193, 466,11.4)
W_460x106_0 = Perfil("W_460x106_0", 20.6 , 104, 469, 12.6)

W_530x72_0 = Perfil("W_530x72_0", 10.9, 207, 524, 9)
W_530x82_0 = Perfil("W_530x82_0", 13.3, 209, 530, 9.5)
W_530x92_0 = Perfil("W_530x92_0", 15.6, 209, 533, 10.2)

W_530x101_0 = Perfil("W_530x101_0", 17.4, 210, 537, 10.9)
W_530x109_0 = Perfil("W_530x109_0", 18.8, 211, 539, 11.6)

W_610x101_0 = Perfil("W_610x101_0", 14.9, 228, 603, 10.5)
W_610x113_0 = Perfil("W_610x113_0", 17.3, 228, 608, 11.2)
W_610x125_0 = Perfil("W_610x125_0", 19.6, 229, 612, 11.9)
W_610x140_0 = Perfil("W_610x140_0", 22.2, 230, 617, 13.1)
W_610x155_0 = Perfil("W_610x155_0", 19.0, 324, 611, 12.7)
W_610x174_0 = Perfil("W_610x174_0", 21.6, 325, 616, 14)

