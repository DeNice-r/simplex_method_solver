from typing import List
from util import variable_re


class Expression:
    variables: List['Variable']

    def __init__(self, *args):
        super().__init__()
        values = [*args]
        for x in range(len(values)):
            if not isinstance(values[x], Variable):
                raise TypeError(f'Expected {type(Variable)} for variable, got {type(values[x])}')
        self.variables = values

    @classmethod
    def from_string(cls, string: str):
        return cls(*(Variable.from_string(x) for x in variable_re.findall(string)))

    def __add__(self, other):
        if isinstance(other, Variable):
            self.variables.append(other)
            return self
        elif isinstance(other, Expression):
            self.variables.extend(other.variables)
            return self

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


from variable import Variable
from constraint import Constraint
