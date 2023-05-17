from fractions import Fraction
from typing import List

from sympy import Symbol

from util import variable_re


class Expression:

    def __init__(self, *args):
        super().__init__()
        values = [*args]
        for x in range(len(values)):
            if not isinstance(values[x], Variable):
                raise TypeError(f'Expected {type(Variable)} for variable, got {type(values[x])}')
        self.variables: List[Variable] = values

    @classmethod
    def from_string(cls, string: str):
        return cls(*(Variable.from_string(x) for x in variable_re.findall(string)))

    def __add__(self, other):
        if isinstance(other, Variable):
            new_instance = Expression(*(self.variables + [other]))
            self.variables.append(other)
            self.variables.sort(key=lambda x: x.index)
            return self
        elif isinstance(other, Expression):
            new_instance = Expression(*(self.variables + other.variables))
            return new_instance
        raise ValueError(f'Addition of {type(self)} and {type(other)} is not supported')

    def __sub__(self, other):
        if isinstance(other, Variable):
            other.coefficient = -other.coefficient
            return self.__add__(other)
        elif isinstance(other, Expression):
            for v in other.variables:
                v.coefficient = -v.coefficient
            return self.__add__(other)

    def __le__(self, other):
        return Constraint(self, '<=', other)

    def __eq__(self, other):
        return Constraint(self, '=', other)

    def __ge__(self, other):
        return Constraint(self, '>=', other)

    def __str__(self):
        a: int = 1
        return ' + '.join([str(v) for v in self.variables])

    def __repr__(self):
        return self.__str__()

    def get_coefficient(self, variable: 'Variable') -> int | float | Fraction | Symbol | None:
        for v in self.variables:
            if v.name == variable.name and v.index == variable.index:
                return v.coefficient
        return None

    def set_coefficient(self, variable: 'Variable', value: int | float | Fraction | Symbol):
        for v in self.variables:
            if v.name == variable.name and v.index == variable.index:
                v.coefficient = value
                return

from variable import Variable
from constraint import Constraint
