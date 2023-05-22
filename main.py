from model import Model


input_string = \
    '''MIN Z = 2x1 + 4x2 + 3x3 + 3x4 + 2x5 + 5x6 + 5x7 + 3x8 + 6x9
x1 + x2 + x3 <= 400
x4 + x5 + x6 <= 300
x7 + x8 + x9 <= 280
30x1 + 20x4 + 60x7 = 6000
20x2 + 30x5 + 40x8 = 50000
40x3 + 50x6 + 20x9 = 8000
and x1,x2,x3,x4,x5,x6,x7,x8,x9 >= 0'''
model = Model.from_string(input_string)
model.solve()
print('-' * 80)

input_string = \
    '''MIN Z = 2x1 + 4x2 + 3x3 + 3x4 + 2x5 + 5x6 + 5x7 + 3x8 + 6x9
x1 + x2 + x3 <= 400
x4 + x5 + x6 <= 300
x7 + x8 + x9 <= 280
30x1 + 20x4 + 60x7 = 6000
20x2 + 30x5 + 40x8 = 11200
40x3 + 50x6 + 20x9 = 8000
and x1,x2,x3,x4,x5,x6,x7,x8,x9 >= 0'''
model = Model.from_string(input_string)
model.solve()
print('-' * 80)

input_string = \
    '''MAX Z = 1x1 + 1x2
1/600x1 + 1/1200x2 <= 1
1/1200x1 + 1/800x2 <= 1
and x1, x2 >= 0'''
model = Model.from_string(input_string)
model.solve()
print('-' * 80)

input_string = \
    '''MAX Z = 3000x1 + 2000x2 + 5000x3 + 4000x4 + 6000x5
20x1 + 30x2 + 35x3 + 30x4 + 40x5 <= 3000
40x1 + 20x2 + 60x3 + 35x4 + 25x5 <= 4500
x1 + x2 + x3 + x4 + x5 = 100
x2 >= 10
and x1,x2,x3,x4,x5 >= 0'''
model = Model.from_string(input_string)
model.solve()
print('-' * 80)

input_string = \
    '''MAX Z = 8x1 + 6x2
2x1 + 5x2 <= 11
4x1 + x2 <= 10
and x1, x2 non-negative integers'''
model = Model.from_string(input_string)
model.solve()

for table in model.json['tables']:
    for row in table:
        for column in row:
            print(f'{str(column):^10}', end='')
        print()
    print('-' * 80)
