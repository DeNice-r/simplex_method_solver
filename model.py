import copy
from typing import Dict, List
import sympy

from artificial_coefficient import ArtificialCoefficient
from constraint import Constraint
from expression import Expression
from util import variable_re, sign_re, Sign, LpType, Status
from variable import Variable
from fractions import Fraction


class Model:
    def __init__(
            self,
            lptype: LpType,
            target: Expression,
            constraints: List[Constraint],
            variable_constraints: List[Constraint]
            ) -> None:
        super().__init__()
        self.lptype: LpType = lptype
        self.initial_target: Expression = copy.deepcopy(target)
        self.target: Expression = target
        self.initial_constraints: List[Constraint] = copy.deepcopy(constraints)
        self.constraints: List[Constraint] = constraints
        self.variable_constraints: List[Constraint] = variable_constraints
        self.highest_variable_index: int = max([x.index for x in self.target.variables])
        self.__basis: Dict[int, Variable] = {}
        self.__deltas: List[Fraction] = []

    @classmethod
    def from_string(cls, string: str) -> 'Model':
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

    def __add_missing_variables(self) -> None:
        for constraint in self.constraints:
            for variable in self.target.variables:
                if constraint.left.get_coefficient(variable) is None:
                    constraint.left += Variable(0, variable.name, variable.index)

    def __convert_constraints_to_equations(self) -> None:
        for index, constraint in enumerate(self.constraints):
            if constraint.sign == Sign.LE: coefficient = 1
            elif constraint.sign == Sign.GE: coefficient = -1
            else: continue
            variable = Variable(coefficient, self.target.variables[0].name, self.highest_variable_index + 1)
            self.constraints[index] = Constraint(
                constraint.left + variable,
                '=',
                constraint.right
            )
            variable = Variable(1, self.target.variables[0].name, self.highest_variable_index + 1)
            self.variable_constraints.append(variable >= 0.)
            variable = Variable(0, self.target.variables[0].name, self.highest_variable_index + 1)
            self.target += variable
            self.highest_variable_index += 1

    def __search_for_basis(self) -> None:
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

    def __add_artificial_basis(self) -> None:
        if len(self.__basis) == len(self.constraints):
            return

        var_name = self.target.variables[0].name
        for index, constraint in enumerate(self.constraints):
            if index in self.__basis:
                continue
            variable = Variable(1, var_name, self.highest_variable_index + 1)
            self.constraints[index] = Constraint(
                constraint.left + variable,
                '=',
                constraint.right
            )
            variable = Variable(1, var_name, self.highest_variable_index + 1)
            self.variable_constraints.append(variable >= 0.)
            variable = Variable(ArtificialCoefficient(-1) if self.lptype is LpType.MAX else ArtificialCoefficient(1),
                           var_name,
                           self.highest_variable_index + 1)
            self.target += variable
            self.__basis[index] = variable
            self.highest_variable_index += 1

    def __to_canonical_form(self) -> None:
        # Convert all constraints to equations
        self.__convert_constraints_to_equations()
        # Try to find basis for each constraint
        self.__search_for_basis()
        # If we don't have basis for each constraint, we need to add artificial variables, where appropriate
        self.__add_artificial_basis()
        # Add variables to constraints with 0 coefficient where they are missing
        self.__add_missing_variables()

    def __update_delta(self) -> None:
        self.__deltas = []
        for variables in self.target.variables:
            s = 0
            for index, constraint in enumerate(self.constraints):
                s += constraint.left.get_coefficient(variables) * self.target.get_coefficient(self.__basis[index])
            self.__deltas.append(s - variables.coefficient)

    def __get_x_values(self) -> Dict[str, int | float | Fraction]:
        x_values = {}
        for variable in self.initial_target.variables:
            x_values[variable.coefless()] = 0
            for index in self.__basis:
                if self.__basis[index].coefless() == variable.coefless():
                    x_values[variable.coefless()] = self.constraints[index].right
                    break
        return x_values

    def __is_solution_viable(self) -> bool:
        viable = True
        values = self.__get_x_values()
        for constraint in self.initial_constraints:
            s = 0
            for variable in constraint.left.variables:
                for basis_index in self.__basis:
                    if self.__basis[basis_index].coefless() == variable.coefless():
                        s += variable.coefficient * self.constraints[basis_index].right
                        break
            viable = viable and constraint.is_satisfied_by(values)
            if not viable:
                break
        if viable:
            for constraint in self.variable_constraints:
                viable = viable and constraint.is_satisfied_by(values)
                if not viable:
                    break

        return viable

    def status(self) -> Status:
        self.__update_delta()
        if all([(x >= 0 if self.lptype is LpType.MAX else x <= 0) for x in self.__deltas]):
            return Status.OPTIMAL if self.__is_solution_viable() else Status.INFEASIBLE

        return Status.UNSOLVED

    def __choose_column(self) -> int:
        return self.__deltas.index(min(self.__deltas) if self.lptype is LpType.MAX else max(self.__deltas))

    def __get_ratio(self, row_index: int, column_index: int) -> Fraction | None:
        xB = self.constraints[row_index].right
        xr = self.constraints[row_index].left.get_coefficient(self.target.variables[column_index])
        if xr == 0:
            return None

        ratio = xB / xr
        if ratio <= 0:
            return None
        return ratio

    def __choose_row(self, column_index: int) -> int:
        mn, mn_index = None, 0
        for index in range(0, len(self.constraints)):
            ratio = self.__get_ratio(index, column_index)
            if ratio is not None and (mn is None or ratio < mn):
                mn, mn_index = ratio, index

        return mn_index

    def __get_pivot(self, row_index: int, column_index: int) -> Fraction:
        return self.constraints[row_index].left.get_coefficient(self.target.variables[column_index])

    def __improve_solution(self) -> None:
        column_index = self.__choose_column()
        row_index = self.__choose_row(column_index)
        pivot = self.__get_pivot(row_index, column_index)
        # print(f'Entering column: {column_index}\nLeaving row: {row_index}\nPivot: {pivot}')
        self.constraints[row_index] /= pivot
        for index, constraint in enumerate(self.constraints):
            if index == row_index:
                continue
            self.constraints[index] -= self.constraints[row_index] * constraint.left.get_coefficient(self.target.variables[column_index])

        old_basis = self.__basis[row_index]
        self.__basis[row_index] = self.target.variables[column_index]
        if isinstance(old_basis.coefficient, ArtificialCoefficient):
            leaving_index = old_basis.index
            for index, variable in enumerate(self.target.variables):
                if variable.index == leaving_index:
                    self.target.variables.pop(index)
                    break
            for constraint in self.constraints:
                for index, variable in enumerate(constraint.left.variables):
                    if variable.index == leaving_index:
                        constraint.left.variables.pop(index)
                        break

    def __get_function_value(self) -> str:
        s = 0
        for index in self.__basis:
            s += self.target.get_coefficient(self.__basis[index]) * self.constraints[index].right
        return s

    def solve(self) -> None:
        # Convert existing model to canonical form
        self.__to_canonical_form()

        # Improve solution until we reach optimal solution
        # print(self)
        while self.status() == Status.UNSOLVED:
            # print(self)
            self.__improve_solution()
        # print(self)

        # Print solution (to be removed)
        values = self.__get_x_values()
        for variable in values:
            print(f'{variable} = {values[variable]}')
        print(f'F(x) = {self.__get_function_value()}')
        print(f'Status: {self.status()}')

    def __str__(self) -> str:
        return '\n'.join([f'F(x) = {self.target} -> {self.lptype}'] + [str(x) for x in self.constraints] + ['']) + ' | '.join([str(x) for x in self.__deltas]) + '\n\n'
        # [str(x) for x in self.variable_constraints])

    def __repr__(self) -> str:
        return self.__str__()
