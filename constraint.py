import copy
from fractions import Fraction
from util import sign_re, Sign


class Constraint:
    def __init__(
            self, left,
            sign: Sign | str,
            right: int | float | Fraction
            ):
        super().__init__()
        if isinstance(sign, str):
            sign = Sign(sign)
        elif not isinstance(sign, Sign):
            raise TypeError(f'Expected {type(Sign)} or {type(str)} for sign argument, got {type(sign)}')
        self.left: int | float | Fraction | Variable | Expression = left
        self.sign: Sign = sign
        if isinstance(right, int | float):
            self.right: Fraction = Fraction.from_float(right)
        else:
            self.right: Fraction = right

    @classmethod
    def from_string(cls, string: str):
        sign = Sign(sign_re.search(string).group())
        left_str, right_str = sign_re.split(string)
        return cls(
            Expression.from_string(left_str),
            sign,
            float(right_str)
        )

    def is_satisfied_by(self, values: dict[str, int | float | Fraction]) -> bool:
        return self.sign.compare(self.left.evaluate(values), self.right)

    def __add__(self, other: int | float | Fraction):
        new_instance = copy.deepcopy(self)
        if isinstance(other, int | float | Fraction):
            for x in new_instance.left.variables:
                x.coefficient += other
            new_instance.right += other
        elif isinstance(other, Constraint):
            for x in range(len(other.left.variables)):
                new_instance.left.variables[x].coefficient += other.left.variables[x].coefficient
            new_instance.right += other.right
        return new_instance

    def __sub__(self, other: int | float | Fraction):
        return self.__add__(-other)

    def __mul__(self, other: int | float | Fraction):
        new_instance = copy.deepcopy(self)
        for x in new_instance.left.variables:
            x.coefficient *= other
        new_instance.right *= other
        if other < 0:
            new_instance.sign = new_instance.sign.flipped()
        return new_instance

    def __truediv__(self, other: int | float | Fraction):
        return self.__mul__(Fraction(1, other))

    def __neg__(self):
        return self.__mul__(-1)

    def __str__(self) -> str:
        return f'{self.left} {self.sign} {self.right}'

    def __repr__(self) -> str:
        return self.__str__()


from expression import Expression
from variable import Variable
