import re
from enum import Enum

variable_re = re.compile(r'([-|+]?\d*[/\\]*\d*[A-ZА-ЯІЇЄЙҐ]+\d+)', re.UNICODE | re.IGNORECASE)
dismantled_variable_re = re.compile(r'([-|+]?\d*[/\\]*\d*)([A-ZА-ЯІЇЄЙҐ]+)(\d+)', re.UNICODE | re.IGNORECASE)
sign_re = re.compile(r'<=|<|=|>=|>', re.UNICODE)


class Sign(Enum):
    LE = '<='
    EQ = '='
    GE = '>='

    def compare(self, left, right):
        if self is Sign.LE:
            return left <= right
        elif self is Sign.EQ:
            return left == right
        elif self is Sign.GE:
            return left >= right
        else:
            raise ValueError(f'Unknown sign {self}')

    def __str__(self):
        return self.value


class LpType(Enum):
    MIN = 'min'
    MAX = 'max'

    def __str__(self):
        return self.value


class Status(Enum):
    UNSOLVED = 'unsolved'
    OPTIMAL = 'optimal'
    INFEASIBLE = 'infeasible'
    UNDEFINED = 'undefined'

    def __str__(self):
        return self.value
