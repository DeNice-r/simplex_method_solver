import math
import re
from enum import Enum
from fractions import Fraction


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

    def flipped(self):
        if self is self.LE:
            return Sign.GE
        elif self is self.GE:
            return Sign.LE
        return self.EQ

    def __str__(self) -> str:
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

    def __str__(self) -> str:
        return self.value


def get_fractional_part(number: int | float | Fraction) -> int | float | Fraction:
    if number < 0:
        return number + math.ceil(abs(number))
    elif number == 1:
        return 1
    return number - int(number)
