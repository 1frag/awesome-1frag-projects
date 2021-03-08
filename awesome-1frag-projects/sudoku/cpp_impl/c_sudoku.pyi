from typing import List, AnyStr, Optional

Item = Optional[AnyStr]  # "1", "2", "3", ..., "9" or None
FieldType = List[List[Item]]  # Matrix of Item

def check(field: FieldType) -> bool:
    """ Checks if there is an error in the Sudoku field """

def solve(field: FieldType) -> Optional[FieldType]:
    """ Solves Sudoku via Backtracking, returning a
    filled-in field or None if there is no solution """
