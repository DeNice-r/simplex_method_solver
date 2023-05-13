from typing import Dict, List
from constraint import Constraint
from expression import Expression
from util import variable_re, sign_re, Sign, LpType, Status
from variable import Variable, ArtificialVariable


# TODO: Implement conversion to canonical form
class Model:
    lptype: LpType
    target: Expression
    constraints: List[Constraint]
    variable_constraints: List[Expression]
    highest_variable_index: int
    __basis: Dict[int, Variable]
    status = Status.UNSOLVED

    def __init__(
            self,
            lptype: LpType,
            target: Expression,
            constraints: List[Constraint],
            variable_constraints: List[Expression]
            ):
        super().__init__()
        self.lptype = lptype
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
            var = ArtificialVariable(1, var_name, self.highest_variable_index + 1)
            self.constraints[index] = Constraint(
                constraint.left + var,
                '=',
                constraint.right
            )
            self.__basis[index] = var
            var = ArtificialVariable(1, var_name, self.highest_variable_index + 1)
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

    def __get_delta(self):
        delta = Expression()
        for index, constraint in enumerate(self.constraints):
            delta += self.target.variables[index] * constraint.right
        return delta - self.target

    @property
    def status(self) -> Status:
        # TODO: Implement status checking
        return Status.UNSOLVED

    def solve(self):
        # Convert existing model to canonical form
        self.__to_canonical_form()

        # while self.status == Status.UNSOLVED:
        #     pass



    def __str__(self):
        return '\n'.join([f'F(x) = {self.target} -> {self.lptype}'] + [str(x) for x in self.constraints] + [''] + [str(x) for x in self.variable_constraints])

    def __repr__(self):
        return self.__str__()
