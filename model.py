import copy
from typing import Dict, List
import sympy
from constraint import Constraint
from expression import Expression
from util import variable_re, sign_re, Sign, LpType, Status
from variable import Variable, ArtificialVariable
from fractions import Fraction


# TODO: Implement conversion to canonical form
class Model:
    lptype: LpType
    target: Expression
    constraints: List[Constraint]
    variable_constraints: List[Expression]
    highest_variable_index: int
    __basis: Dict[int, Variable]
    deltas: List[Fraction]

    def __init__(
            self,
            lptype: LpType,
            target: Expression,
            constraints: List[Constraint],
            variable_constraints: List[Expression]
            ):
        super().__init__()
        self.lptype = lptype
        self.initial_target = copy.deepcopy(target)
        self.target = target
        self.constraints = constraints
        self.variable_constraints = variable_constraints
        self.highest_variable_index = max([x.index for x in self.target.variables])
        self.__basis = {}

    @classmethod
    def from_string(cls, string: str):
        input_lines = string.replace(' ', '').split('\n')

        lptype = LpType(input_lines[0][:3].lower())
        target = Expression.from_string(input_lines[0])

        constraints = []
        variable_constraints = []

        for x in input_lines[1:]:
            if ',' in x:
                sign = sign_re.search(x).group()
                left_str, right_str = sign_re.split(input_lines[-1])
                left_values: List[str] = variable_re.findall(left_str)
                for value in left_values:
                    variable_constraints.append(Constraint.from_string(f'{value}{sign}{right_str}'))
            else:
                constraints.append(Constraint.from_string(x))

        return cls(lptype, target, constraints, variable_constraints)

    def __add_missing_variables(self):
        for constraint in self.constraints:
            for variable in self.target.variables:
                if constraint.left.get_coefficient(variable) is None:
                    constraint.left += Variable(0, variable.name, variable.index)

    def __convert_constraints_to_equations(self):
        for index, constraint in enumerate(self.constraints):
            if constraint.sign == Sign.EQ:
                continue
            elif constraint.sign == Sign.LE:
                coefficient = 1
            elif constraint.sign == Sign.GE:
                coefficient = -1
            var = Variable(coefficient, self.target.variables[0].name, self.highest_variable_index + 1)
            self.constraints[index] = Constraint(
                constraint.left + var,
                '=',
                constraint.right
            )
            var = Variable(1, self.target.variables[0].name, self.highest_variable_index + 1)
            self.variable_constraints.append(var >= 0.)
            var = Variable(0, self.target.variables[0].name, self.highest_variable_index + 1)
            self.target += var
            self.highest_variable_index += 1

    def __search_for_basis(self):
        for index, constraint in enumerate(self.constraints):
            for variable in constraint.left.variables:
                if variable.coefficient != 1:
                    continue
                basis_criteria = True
                for constraint2 in self.constraints:
                    if constraint is constraint2:
                        continue
                    for variable2 in constraint2.left.variables:
                        if variable.name == variable2.name and variable.index == variable2.index and variable2.coefficient != 0:
                            basis_criteria = False
                            break
                    if not basis_criteria:
                        break
                if basis_criteria:
                    self.__basis[index] = variable
                    break

    def __add_artificial_basis(self):
        if len(self.__basis) == len(self.constraints):
            return

        var_name = self.target.variables[0].name
        for index, constraint in enumerate(self.constraints):
            if index in self.__basis:
                continue
            var = Variable(1, var_name, self.highest_variable_index + 1)
            self.constraints[index] = Constraint(
                constraint.left + var,
                '=',
                constraint.right
            )
            self.__basis[index] = var
            var = Variable(1, var_name, self.highest_variable_index + 1)
            self.variable_constraints.append(var >= 0.)
            var = ArtificialVariable(-1, var_name, self.highest_variable_index + 1)
            self.target += var
            self.highest_variable_index += 1

    def __to_canonical_form(self):
        # Convert all constraints to equations
        self.__convert_constraints_to_equations()
        # Try to find basis for each constraint
        self.__search_for_basis()
        # If we don't have basis for each constraint, we need to add artificial variables, where appropriate
        self.__add_artificial_basis()
        # Add variables to constraints with 0 coefficient where they are missing
        self.__add_missing_variables()

    def __update_delta(self) -> None:
        self.deltas = []
        M = sympy.Symbol('M')
        for var in self.target.variables:
            s = 0
            for index, constraint in enumerate(self.constraints):
                s += constraint.left.get_coefficient(var) * self.target.get_coefficient(self.__basis[index])
            delta = (s - var.coefficient)
            if not isinstance(delta, int | float | Fraction):
                delta = delta.subs(M, 10**12)
            self.deltas.append(delta)

    @property
    def status(self) -> Status:
        self.__update_delta()
        if all([x >= 0 for x in self.deltas]):
            return Status.OPTIMAL

        return Status.UNSOLVED

    def __choose_column(self) -> int:
        return self.deltas.index(min(self.deltas))

    def __get_ratio(self, row_index: int, column_index: int) -> Fraction | str:
        xB = self.constraints[row_index].right
        xr = self.constraints[row_index].left.get_coefficient(self.target.variables[column_index])
        if xr == 0:
            return '---'

        return xB / xr

    def __choose_row(self, column_index: int) -> int:
        mn, mn_index = self.__get_ratio(0, column_index), 0
        for index in range(1, len(self.constraints)):
            ratio = self.__get_ratio(index, column_index)
            if ratio != '---' and ratio < mn:
                mn, mn_index = ratio, index

        return mn_index

    def __get_pivot(self, row_index: int, column_index: int) -> Fraction:
        return self.constraints[row_index].left.get_coefficient(self.target.variables[column_index])

    def __improve_solution(self):
        column_index = self.__choose_column()
        row_index = self.__choose_row(column_index)
        pivot = self.__get_pivot(row_index, column_index)
        self.__basis[row_index] = self.target.variables[column_index]
        self.constraints[row_index] /= pivot
        for index, constraint in enumerate(self.constraints):
            if index == row_index:
                continue
            self.constraints[index] -= self.constraints[row_index] * constraint.left.get_coefficient(self.target.variables[column_index])

    def __get_function_value(self) -> str:
        s = 0
        for index in self.__basis:
            s += self.target.get_coefficient(self.__basis[index]) * self.constraints[index].right
        return s

    def solve(self):
        # Convert existing model to canonical form
        self.__to_canonical_form()

        # print(self)

        while self.status == Status.UNSOLVED:
            self.__improve_solution()

        for variable in self.initial_target.variables:
            found = False
            for index, basis in enumerate(self.__basis.values()):
                if variable.coefless() == basis.coefless():
                    print(f'{variable.coefless()} = {self.constraints[index].right}')
                    found = True
                    break
            if not found:
                print(f'{variable.coefless()} = 0')

        print(f'F(x) = {self.__get_function_value()}')

    def __str__(self):
        return '\n'.join([f'F(x) = {self.target} -> {self.lptype}'] + [str(x) for x in self.constraints] + [''] + [str(x) for x in self.variable_constraints])

    def __repr__(self):
        return self.__str__()
