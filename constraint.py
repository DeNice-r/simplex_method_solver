from util import sign_re, Sign


class Constraint:
    left: int | float
    sign: Sign
    right: int | float

    def __init__(
            self, left: int | float,
            sign: Sign | str,
            right: int | float
            ):
        super().__init__()
        if isinstance(sign, str):
            sign = Sign(sign)
        elif not isinstance(sign, Sign):
            raise TypeError(f'Expected {type(Sign)} or {type(str)} for sign argument, got {type(sign)}')
        self.left = left
        self.sign = sign
        self.right = right

    @classmethod
    def from_string(cls, string: str):
        sign = Sign(sign_re.search(string).group())
        left_str, right_str = sign_re.split(string)
        return cls(
            Expression.from_string(left_str),
            sign,
            float(right_str)
        )

    def __str__(self):
        return f'{self.left} {self.sign} {self.right}'

    def __repr__(self):
        return self.__str__()


from expression import Expression
from variable import Variable
