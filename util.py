import re
from enum import Enum

variable_re = re.compile(r'([-|+]?\d*[A-ZА-ЯІЇЄЙҐ]+\d+)', re.UNICODE | re.IGNORECASE)
dismantled_variable_re = re.compile(r'([-|+]?\d*)([A-ZА-ЯІЇЄЙҐ]+)(\d+)', re.UNICODE | re.IGNORECASE)
sign_re = re.compile(r'<=|<|=|>=|>', re.UNICODE)


class Sign(Enum):
    LE = '<='
    EQ = '='
    GE = '>='

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
    UNBOUNDED = 'unbounded'
    INFEASIBLE = 'infeasible'
    UNDEFINED = 'undefined'

    def __str__(self):
        return self.value
