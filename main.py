from fractions import Fraction

from model import Model


input_string = \
    '''MAX Z = 3000x1 + 2000x2 + 5000x3 + 4000x4 + 6000x5
20x1 + 30x2 + 35x3 + 30x4 + 40x5 <= 3000
40x1 + 20x2 + 60x3 + 35x4 + 25x5 <= 4500
x1 + x2 + x3 + x4 + x5 = 100
x2 >= 10
x1,x2,x3,x4,x5 >= 0'''


model = Model.from_string(input_string)
model.solve()
