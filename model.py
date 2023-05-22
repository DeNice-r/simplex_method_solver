import copy
from typing import Dict, List
from math import isclose
from artificial_coefficient import ArtificialCoefficient
from constraint import Constraint
from expression import Expression
from util import variable_re, sign_re, Sign, LpType, Status, get_fractional_part
from variable import Variable
from fractions import Fraction


class Model:
    def __init__(
            self,
            lptype: LpType,
            target: Expression,
            constraints: List[Constraint],
            variable_constraints: List[Constraint],
            positive_integer_variables: List[Variable]
    ) -> None:
        super().__init__()
        self.lptype: LpType = lptype
        self.initial_target: Expression = copy.deepcopy(target)
        self.target: Expression = target
        self.initial_constraints: List[Constraint] = copy.deepcopy(constraints)
        self.constraints: List[Constraint] = constraints
        self.variable_constraints: List[Constraint] = variable_constraints
        self.positive_integer_variables: List[Variable] = positive_integer_variables
        self.__highest_variable_index: int = max([x.index for x in self.target.variables])
        self.__basis: Dict[int, Variable] = {}
        self.__gomory_variables: List[Variable] = []
        self.json: dict = {'tables': []}
        self.gomory_state = False

    @classmethod
    def from_string(cls, string: str):
        input_lines = string.replace(' ', '').split('\n')

        lptype = LpType(input_lines[0][:3].lower())
        target = Expression.from_string(input_lines[0])

        constraints = []
        variable_constraints = []
        positive_integer_variables = []

        for x in input_lines[1:-1]:
            constraints.append(Constraint.from_string(x))

        conditions_str = input_lines[-1][3:]
        if 'and' in conditions_str:
            variable_constraints_str, positive_integer_variables_str = conditions_str.split('and')
        elif 'non-negativeintegers' in conditions_str:
            variable_constraints_str = ''
            positive_integer_variables_str = conditions_str
        else:
            variable_constraints_str = conditions_str
            positive_integer_variables_str = ''

        if variable_constraints_str:
            sign = sign_re.search(variable_constraints_str).group()
            left_str, right_str = sign_re.split(variable_constraints_str)
            left_values: List[str] = variable_re.findall(left_str)
            for value in left_values:
                variable_constraints.append(Constraint.from_string(f'{value}{sign}{right_str}'))

        if positive_integer_variables_str:
            for variable_str in variable_re.findall(positive_integer_variables_str.replace('non-negativeintegers', '')):
                positive_integer_variables.append(Variable.from_string(variable_str))

        return cls(lptype, target, constraints, variable_constraints, positive_integer_variables)

    def __add_missing_variables(self) -> None:
        for constraint in self.constraints:
            for variable in self.target.variables:
                if constraint.left.get_coefficient(variable) is None:
                    constraint.left += Variable(0, variable.name, variable.index)

    def __introduce_variable(self, coefficients: List[int | float | Fraction | ArtificialCoefficient], name: str, constraint_index: int) -> None:
        index = self.__highest_variable_index + 1
        variables = Variable.create_many(coefficients, name, index)
        constraint = self.constraints[constraint_index]
        self.constraints[constraint_index] = Constraint(constraint.left + variables[0], '=', constraint.right)
        self.variable_constraints.append(variables[1] >= 0.)
        self.target += variables[2]
        self.__highest_variable_index += 1

    def __convert_constraints_to_equations(self) -> None:
        for index, constraint in enumerate(self.constraints):
            if constraint.sign == Sign.LE:
                coefficient = 1
            elif constraint.sign == Sign.GE:
                coefficient = -1
            else:
                continue
            self.__introduce_variable([coefficient, 1, 0], self.target.variables[0].name, index)

    def __search_for_basis(self) -> None:
        for index, constraint in enumerate(self.constraints):
            if index in self.__basis:
                continue
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

            target_coefficient = ArtificialCoefficient(-1) if self.lptype is LpType.MAX else ArtificialCoefficient(1)
            self.__introduce_variable([1, 1, target_coefficient], var_name, index)

    def __to_canonical_form(self) -> None:
        # Convert all constraints to equations
        self.__convert_constraints_to_equations()
        # Try to find basis for each constraint
        self.__search_for_basis()
        # If we don't have basis for each constraint, we need to add artificial variables, where appropriate
        self.__add_artificial_basis()
        self.__search_for_basis()
        # Add variables to constraints with 0 coefficient where they are missing
        self.__add_missing_variables()

    def __get_sums(self) -> List[int | float | Fraction]:
        sums = []
        for variables in self.target.variables:
            sums.append(0)
            for index, constraint in enumerate(self.constraints):
                sums[-1] += constraint.left.get_coefficient(variables) * self.target.get_coefficient(self.__basis[index])
        return sums

    def __get_deltas(self) -> List[int | float | Fraction | ArtificialCoefficient]:
        deltas = []
        for variables in self.target.variables:
            s = 0
            for index, constraint in enumerate(self.constraints):
                s += constraint.left.get_coefficient(variables) * self.target.get_coefficient(self.__basis[index])
            deltas.append(s - variables.coefficient)
        sums = self.__get_sums()
        return [sums[x] - self.target.variables[x].coefficient for x in range(len(sums))]

    def __get_x_values(self) -> Dict[str, int | float | Fraction]:
        x_values = {}
        for variable in self.initial_target.variables:
            x_values[variable.coefless()] = 0
            for index in self.__basis:
                if self.__basis[index].coefless() == variable.coefless():
                    x_values[variable.coefless()] = self.constraints[index].right
                    break
        return x_values

    def __get_integer_status(self) -> Status:
        if not self.positive_integer_variables:
            return Status.OPTIMAL
        values = self.__get_x_values()
        for variable in self.positive_integer_variables:
            value = values[variable.coefless()]
            if not (value >= 0 and isclose(value, int(value))):
                return Status.UNSOLVED
        return Status.OPTIMAL

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

    def get_status(self) -> Status:
        deltas = self.__get_deltas()
        if all([(x >= 0 if self.lptype is LpType.MAX else x <= 0) for x in deltas]):
            return Status.OPTIMAL if self.__is_solution_viable() else Status.INFEASIBLE

        return Status.UNSOLVED

    def __choose_column(self) -> int:
        deltas = self.__get_deltas()
        return deltas.index(min(deltas) if self.lptype is LpType.MAX else max(deltas))

    def __get_ratio(self, row_index: int, column_index: int) -> int | float | Fraction | None:
        xB = self.constraints[row_index].right
        xr = self.constraints[row_index].left.get_coefficient(self.target.variables[column_index])
        if xr == 0:
            return None

        ratio = xB / xr
        if ratio <= 0:
            return None
        return ratio

    def __choose_row(self, column_index: int) -> int:
        mn, mn_index = None, None
        for index in range(0, len(self.constraints)):
            ratio = self.__get_ratio(index, column_index)
            if ratio is not None and (mn is None or ratio < mn):
                mn, mn_index = ratio, index

        return mn_index

    def __get_pivot(self, row_index: int, column_index: int) -> int | float | Fraction:
        return self.constraints[row_index].left.get_coefficient(self.target.variables[column_index])

    def __recalculate_solution(self, row_index: int, column_index: int) -> None:
        pivot = self.__get_pivot(row_index, column_index)
        self.constraints[row_index] /= pivot
        for index, constraint in enumerate(self.constraints):
            if index == row_index:
                continue
            self.constraints[index] -= self.constraints[row_index] * constraint.left.get_coefficient(
                self.target.variables[column_index])

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

    def __improve_solution(self) -> None:
        column_index = self.__choose_column()
        row_index = self.__choose_row(column_index)
        self.__recalculate_solution(row_index, column_index)

    def __get_function_value(self) -> int | float | Fraction | ArtificialCoefficient:
        s = 0
        for index in self.__basis:
            s += self.target.get_coefficient(self.__basis[index]) * self.constraints[index].right
        return s

    def __get_gomory_deltas(self) -> List[int | float | Fraction | None]:
        deltas = self.__get_deltas()
        gomory_applicable_row = None
        for index, constraint in enumerate(self.constraints):
            if constraint.right <= 0 and (gomory_applicable_row is None or self.constraints[gomory_applicable_row].right > constraint.right):
                if constraint.right == 0 and self.__basis[index].coefless() in [x.coefless() for x in self.__gomory_variables]:
                    continue

                gomory_applicable_row = index
        if not gomory_applicable_row:
            return [None for _ in deltas]
        for index, variable in enumerate(self.constraints[gomory_applicable_row].left.variables):
            if variable.coefficient < 0:
                deltas[index] /= variable.coefficient
            else:
                deltas[index] = None
        return deltas

    def __gomory_choose_column(self) -> int:
        deltas = self.__get_gomory_deltas()

        extr, extr_index = None, None

        if self.lptype is LpType.MAX:  # TODO: check if it's correct (suggested by copilot)
            for index, delta in enumerate(deltas):
                if delta is not None and (extr is None or delta > extr):
                    extr = delta
                    extr_index = index
        else:
            for index, delta in enumerate(deltas):
                if delta is not None and (extr is None or delta < extr):
                    extr = delta
                    extr_index = index

        return extr_index

    def __gomory_choose_row(self, column: int = None) -> int:
        mn_index = None
        for index in self.__basis:
            if self.constraints[index].right <= 0 and (mn_index is None or self.constraints[index].right < self.constraints[mn_index].right):
                mn_index = index

        return mn_index

    def __gomory_cut(self) -> None:
        cut_row = None
        for index, variable in self.__basis.items():
            if variable.coefless() not in [x.coefless() for x in self.initial_target.variables] or get_fractional_part(self.constraints[index].right) == 1:
                continue
            if (cut_row is None or get_fractional_part(self.constraints[cut_row].right) <  # variable.coefless() in [x.coefless() for x in self.positive_integer_variables] and \
                     get_fractional_part(self.constraints[index].right)):
                cut_row = index

        self.constraints.append(Constraint(Expression(), Sign.EQ, -get_fractional_part(self.constraints[cut_row].right)))
        for variable in self.constraints[cut_row].left.variables:
            if variable.coefless() == self.__basis[cut_row].coefless():
                # Add new variable
                self.__introduce_variable([get_fractional_part(variable.coefficient), 1, 0], variable.name,
                                          len(self.constraints) - 1)
                self.__gomory_variables.append(self.target.variables[-1])
                continue
            self.constraints[-1].left.variables.append(Variable(-get_fractional_part(variable.coefficient), variable.name, variable.index))

        self.__search_for_basis()
        self.__add_missing_variables()

        self.__add_table_to_json()

        self.__choose_column = self.__gomory_choose_column
        self.__choose_row = self.__gomory_choose_row

        row_index = self.__choose_row()
        column_index = self.__choose_column()
        self.__recalculate_solution(row_index, column_index)

    def solve(self) -> None:
        # Convert existing model to canonical form
        self.__to_canonical_form()
        self.json['tables'] = []
        self.json['tables'].append(self.get_current_table())
        # Improve solution until we reach optimal solution
        while self.get_status() is Status.UNSOLVED:
            self.__improve_solution()
            self.__add_table_to_json()


        while self.get_status() is Status.OPTIMAL and self.__get_integer_status() is Status.UNSOLVED:
            self.gomory_state = True
            self.__gomory_cut()
            self.__add_table_to_json()

            while any([x is not None for x in self.__get_gomory_deltas()]):
                self.__improve_solution()
                self.__add_table_to_json()

        self.__finalize_json()

    def __add_table_to_json(self) -> None:
        self.json['tables'].append(self.get_current_table())

    def get_current_table(self) -> Dict[str, List[int | float | Fraction | None] | None | int | float | Fraction]:
        column = self.__choose_column()
        row = column and self.__choose_row(column)
        pivot = column and row and self.__get_pivot(row, column)
        r = {
            'target': [variable.coefficient for variable in self.target.variables],
            'constraints': [],
            'basis': [constraint.right for constraint in self.constraints],
            'variables': [variable.coefless() for variable in self.target.variables],
            'basis_variables': [variable.coefless() for variable in self.__basis.values()],
            'sums': self.__get_sums(),
            'deltas': self.__get_deltas(),
            'gomory_deltas': [x if x else '---' for x in self.__get_gomory_deltas()] if self.gomory_state else None,
            'function_value': self.__get_function_value(),
            'column': column,
            'row': row,
            'pivot': pivot,
        }

        # Too complicated to be done in one line
        for constraint in self.constraints:
            r['constraints'].append([])
            r['constraints'][-1].append(constraint.right)
            for variable in constraint.left.variables:
                r['constraints'][-1].append(constraint.left.get_coefficient(variable))
        return r

    def __finalize_json(self) -> None:
        self.json['status'] = self.get_status()
        self.json['integer_status'] = self.__get_integer_status()
        self.json['x_values'] = self.__get_x_values()
        self.json['function_value'] = self.__get_function_value()

    def print_json(self) -> None:
        for table in self.json['tables']:
            for row in table:
                print(f'{row}: {table[row]}')
            print('-' * 80)

        for key in list(self.json.keys())[1:]:
            print(f'{key}: {self.json[key]}')

    def __str__(self) -> str:
        return '\n'.join(
            [f'F(x) = {self.target} -> {self.lptype}'] + [str(x) for x in self.constraints] + ['']) + ' | '.join(
            [str(x) for x in self.__get_deltas()]) + '\n\n'

    def __repr__(self) -> str:
        return self.__str__()
