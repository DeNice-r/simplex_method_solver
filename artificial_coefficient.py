from fractions import Fraction


class ArtificialCoefficient:
    def __init__(self, multiplier: int | float | Fraction = 1, constant: int | float | Fraction = 0):
        self.multiplier: Fraction = multiplier
        self.constant: Fraction = constant

    def __add__(self, other):
        if isinstance(other, int | float | Fraction):
            return ArtificialCoefficient(self.multiplier, self.constant + other)
        elif isinstance(other, ArtificialCoefficient):
            return ArtificialCoefficient(self.multiplier + other.multiplier, self.constant + other.constant)
        return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        if isinstance(other, int | float | Fraction):
            return ArtificialCoefficient(self.multiplier * other, self.constant * other)
        elif isinstance(other, ArtificialCoefficient):
            return ArtificialCoefficient(self.multiplier * other.multiplier, self.constant * other.constant)
        return NotImplemented

    def __rmul__(self, other):
        return self.__mul__(other)

    def __sub__(self, other):
        if isinstance(other, int | float | Fraction):
            return ArtificialCoefficient(self.multiplier, self.constant - other)
        elif isinstance(other, ArtificialCoefficient):
            return ArtificialCoefficient(self.multiplier - other.multiplier, self.constant - other.constant)
        return NotImplemented

    def __rsub__(self, other):
        return (-self).__add__(other)

    def __truediv__(self, other):
        if isinstance(other, int | float | Fraction):
            return ArtificialCoefficient(self.multiplier / other, self.constant / other)
        elif isinstance(other, ArtificialCoefficient):
            return ArtificialCoefficient(self.multiplier / other.multiplier, self.constant / other.constant)
        return NotImplemented

    def __rtruediv__(self, other):
        return (1/self).__mul__(other)

    def __neg__(self):
        return ArtificialCoefficient(-self.multiplier, -self.constant)

    def __eq__(self, other):
        if isinstance(other, int | float | Fraction):
            return self.multiplier == 0 and self.constant == other
        elif isinstance(other, ArtificialCoefficient):
            return self.multiplier == other.multiplier and self.constant == other.constant
        return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if self.__eq__(other):
            return False
        if isinstance(other, int | float | Fraction):
            if self.multiplier == 0:
                return self.constant < other
            return self.multiplier < 0
        elif isinstance(other, ArtificialCoefficient):
            if self.multiplier == other.multiplier:
                return self.constant < other.constant
            return self.multiplier < other.multiplier
        return NotImplemented

    def __gt__(self, other):
        return not self.__lt__(other) and not self.__eq__(other)

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __str__(self) -> str:
        if self.multiplier == 0 and self.constant == 0:
            return '0'
        m_part = f'{"-" if self.multiplier < 0 else ""}{abs(self.multiplier) if abs(self.multiplier) != 1 else ""}M'
        if self.constant == 0:
            return m_part
        elif self.multiplier == 0:
            return f'{self.constant}'
        else:
            return f'{m_part} {"-" if self.constant < 0 else "+"} {abs(self.constant)}'

    def __repr__(self) -> str:
        return self.__str__()
