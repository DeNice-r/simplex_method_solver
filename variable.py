from util import dismantled_variable_re
from fractions import Fraction
from sympy import Symbol


class Variable:
    name: str
    index: int
    coefficient: Fraction

    def __init__(self, coefficient, name, index, *args, **kwargs):
        super().__init__()
        self.coefficient = Fraction.from_float(coefficient)
        self.name = name
        self.index = index

    @classmethod
    def from_string(cls, string: str):
        coefficient_str, name, index = dismantled_variable_re.match(string).groups()
        if coefficient_str in ['+', '-']:
            coefficient_str = coefficient_str + '1'
        return cls(float(coefficient_str or 1), name, int(index))

    def __str__(self):
        return f'{self.coefficient}{self.name}{self.index}'

    def __repr__(self):
        return self.__str__()

    def __add__(self, other):
        from expression import Expression
        if isinstance(other, int | float):
            new_instance = self.copy()
            new_instance.coefficient += other
            return new_instance
        elif isinstance(other, Variable):
            if self.name == other.name:
                new_instance = self.copy()
                new_instance.coefficient += other.coefficient
                return new_instance
            else:
                return Expression(self, other)

    def __mul__(self, other):
        if isinstance(other, int | float):
            new_instance = self.copy()
            new_instance.coefficient *= other
            return new_instance
        elif isinstance(other, Variable):
            if self.name == other.name:
                new_instance = self.copy()
                new_instance.coefficient *= other.coefficient
                return new_instance
            else:
                raise ValueError('Multiplication of different variables')
        raise ValueError(f'Multiplication/division of {type(self)} and {type(other)} is not supported')

    def __sub__(self, other):
        if isinstance(other, int | float):
            other = -other
            return self.__add__(other)
        elif isinstance(other, Variable) and self.name == other.name:
            other.coefficient = -other.coefficient
            return self.__add__(other)

    def __truediv__(self, other):
        if isinstance(other, int | float):
            other = Fraction(1, other)
            return self.__mul__(other)
        elif isinstance(other, Variable):
            other.coefficient = 1 / other.coefficient
            return self.__mul__(other)

    def __le__(self, other):
        return Constraint(self, '<=', other)

    def __eq__(self, other):
        return Constraint(self, '==', other)

    def __ge__(self, other):
        return Constraint(self, '>=', other)

    def __neg__(self):
        new_instance = self.copy()
        new_instance.coefficient = -new_instance.coefficient
        return new_instance


class ArtificialVariable(Variable):

    def __init__(self, coefficient, name, index, *args, **kwargs):
        super().__init__(coefficient, name, index)
        self.coefficient = -Symbol('M')


from constraint import Constraint
