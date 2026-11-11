"""tx05_constants.py - the AST-derivable truth for the TX-05C chain fixture.

`grade_v5.derive_truth` reads this file with `ast` and takes each symbol's assigned
value, so the fixture's documented `expected` strings are cross-checked against source
rather than trusted.  The values mirror the bodies the fixture delivers: the base
constant and the override the caller rebinds.
"""

SYM_01 = 4011
SYM_01_OVERRIDE = 4017

SYM_02 = 4021
SYM_02_OVERRIDE = 4027

SYM_03 = 4031
SYM_03_OVERRIDE = 4037

SYM_04 = 4041
SYM_04_OVERRIDE = 4047

SYM_05 = 4051
SYM_05_OVERRIDE = 4057

SYM_06 = 4061
SYM_06_OVERRIDE = 4067
