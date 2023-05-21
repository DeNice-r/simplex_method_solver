from typing import List

from util import dismantled_variable_re
from fractions import Fraction
from copy import deepcopy
from artificial_coefficient import ArtificialCoefficient


class Variable:
    def __init__(self, coefficient, name, index):
        super().__init__()
        if isinstance(coefficient, int | float):
            self.coefficient: Fraction | ArtificialCoefficient = Fraction.from_float(coefficient)
        elif isinstance(coefficient, Fraction | ArtificialCoefficient):
            self.coefficient: Fraction | ArtificialCoefficient = coefficient
        self.name: str = name
        self.index: int = index

    @classmethod
    def from_string(cls, string: str):
        coefficient_str, name, index = dismantled_variable_re.match(string).groups()
        if coefficient_str in ['+', '-']:
            coefficient_str = coefficient_str + '1'
        return cls(Fraction(coefficient_str or 1), name, int(index))

    @classmethod
    def create_many(cls, coefficients: List[int | float | Fraction], name: str, index: int):
        return [cls(coefficient, name, index) for coefficient in coefficients]

    def evaluate(self, values: dict[str, int | float | Fraction]):
        if self.coefless() in values:
            return self.coefficient * values[self.coefless()]
        return 0

    def __str__(self):
        return f'{self.coefficient}{self.name}{self.index}'

    def __repr__(self):
        return self.__str__()

    def coefless(self):
        return f'{self.name}{self.index}'

    def __add__(self, other):
        from expression import Expression
        if isinstance(other, int | float):
            new_instance = deepcopy(self)
            new_instance.coefficient += other
            return new_instance
        elif isinstance(other, Variable):
            if self.name == other.name:
                new_instance = deepcopy(self)
                new_instance.coefficient += other.coefficient
                return new_instance
            else:
                return Expression(self, other)

    def __mul__(self, other):
        new_instance = deepcopy(self)
        if isinstance(other, int | float):
            new_instance.coefficient *= other
            return new_instance
        elif isinstance(other, Variable):
            if self.name == other.name:
                new_instance = deepcopy(self)
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

    # def __eq__(self, other):
    #     return Constraint(self, '=', other)

    def __ge__(self, other):
        return Constraint(self, '>=', other)

    def __neg__(self):
        new_instance = deepcopy(self)
        new_instance.coefficient = -new_instance.coefficient
        return new_instance


from constraint import Constraint
