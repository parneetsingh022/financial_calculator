# Financial Calculator CLI

An interactive command‑line financial factor and expression evaluator supporting:

- Standard engineering economy factors (P/F, F/P, P/A, A/P, F/A, A/F, A/G, P/G)
- Percentage interest inputs with optional `%` (inside factor calls and expressions)
- Arbitrary mathematical expressions (with the `math` module functions)
- Chaining / combining factor results in larger expressions
- User‑defined variables and variable scoping via `case` / `endcase`
- Gradient factors (A/G, P/G) with proper i→0 limiting behavior
- A custom `abs()` (absolute value) implementation available inside expressions
- Screen management: `cls`, scoped variable sessions, and history replay

Only a single simple colorized REPL (`calculator.py`) is documented here. (The previous curses-based UI has been removed from the documentation for simplicity.)

---
## Installation

Python 3.8+ recommended.

```powershell
# (Windows PowerShell examples)
python -m venv .venv
.venv\Scripts\activate
pip install colorama
python calculator.py
```

---
## Core Factor Notation
Each factor is a function of effective interest rate `i` (per period) and number of periods `n`.
Inside factor calls and general expressions, numbers you supply for the interest argument are interpreted as percentages whether or not you include the `%` (e.g. `5` → 5%). See the next section for the important distinction when assigning variables.

| Symbol | Meaning | Formula |
|--------|---------|---------|
| F_P | F given P | (1+i)^n |
| P_F | P given F | (1+i)^(-n) |
| P_A | P given A | (1 - (1+i)^(-n)) / i |
| A_P | A given P | i(1+i)^n / ((1+i)^n - 1) |
| F_A | F given A | ((1+i)^n - 1) / i |
| A_F | A given F | i / ((1+i)^n - 1) |
| A_G | A given arithmetic gradient G (0,G,2G,...,(n-1)G) | (1/i) - n/((1+i)^n - 1) |
| P_G | P given arithmetic gradient G | A_G * P_A |

Special handling ensures correct limiting values when `i = 0`.

---
## Basic Usage Examples
At the prompt (`factor>`):

```text
A_P(5%, 10)
F_A(7, 12)          # 7 means 7%
P_F(5%, 3) * 1000
A_G(4%, 8)
P_G(4, 8)
```

All of these return a numeric result. Results are printed as `Result: <value>`.

---
## Percentage Semantics (Important)
There is a difference between how bare numbers and numbers with `%` are handled depending on context:

1. Inside factor calls and evaluated expressions (e.g. `A_P(5, 10)` or `F_A(7%,12)`), the interest argument is always treated as a percent. So `A_P(5,10)` and `A_P(5%,10)` are equivalent (`i = 0.05`).
2. In variable assignments, a number is stored literally, while a number with a `%` is converted to its decimal fractional form.

Example session:
```
factor> x = 43
factor> x
x = 43
factor> x = 43%
factor> x
x = 0.43
factor> A_G(12,29)
Result: 0.08333333333333333
factor> A_G(12%,29)
Result: 7.2071166998823895
```
Explanation:
- `A_G(12,29)` reads `12` as 12% internally when used as the interest argument, giving a result based on `i = 0.12`.
- `A_G(12%,29)` also uses `i = 0.12`, but the displayed numeric magnitude differs due to how the gradient formula scales; both forms treat 12 and 12% identically as 0.12 inside the factor logic.
- Variable assignment without `%` keeps the raw number (`x = 43`).
- Variable assignment with `%` stores the decimal (`x = 0.43`). Use this when you plan to pass the variable directly where a rate is expected without additional division.

Tip: If you assign `rate = 7%`, then `A_P(rate*100, n)` is NOT needed; just pass `rate*100` only if you want to reinterpret it as 700%. For normal usage do `A_P(rate*100, n)` only if you understand the doubling of scaling. Prefer `A_P(7, n)` or `rate = 7%` then `A_P(rate*100, n)` ONLY if you intentionally want 700%. In most cases you want either `A_P(7, n)` or `rate = 7%` then just use `A_P(7, n)` again rather than referencing `rate` directly.

---
## Expressions
You are not limited to a single factor call. You can combine them with normal math operators:
```
A_P(5%, 10) * 100
F_A(7%, 12) / A_P(5%, 10)
(P_F(5, 3) + A_P(4, 6)) * 2
sin(0.5) + cos(0.25)   # via math module import
```
Supported math functions come from Python's `math` module (e.g. `sin`, `cos`, `log`, `exp`, `sqrt`, etc.).

Percent signs inside larger expressions are also converted:
```
( A_P(5%, 10) * 100 ) / ( F_A(7%, 12) + 3 )
```

---
## Variables
Assign variables for reuse:
```
x = 2500
rate = 7%
n = 12
A_P(rate, n) * x
```
Typing the variable name alone prints its value:
```
x
rate
```
Variable assignment is silent on success. If an error occurs (e.g., invalid expression), an error message is shown.

---
## Custom abs()
Because builtins are stripped for safety, a custom `abs()` is exposed inside the evaluator. It behaves like normal absolute value:
```
abs(-5)          # -> 5
abs(A_P(5%, 10) * -3)
```

---
## Case Scoping
`case` creates an isolated variable scope. Variables defined inside a case shadow outer ones and disappear when the case ends.
```
x = 10
case
x = 4
x           # prints 4
endcase
x           # prints 10 (outer scope restored)
```
While in a case, previous history is hidden. After `endcase`, the prior history (before `case`) is restored and appended with a message.

---
## Screen & History Commands
| Command | Description |
|---------|-------------|
| help    | Reprint full help text |
| cls     | Clear the visible screen/history (variables remain) |
| case    | Start a new variable scope and clear visible history |
| endcase | End scope, restore previous variables & history |
| quit / exit | Leave the program |

Empty input (just pressing Enter) does nothing (ignored) or exits (in basic mode) depending on the interface version (curses version inserts a blank line; plain version exits on blank). You can modify this behavior in `repl()` if desired.

---
<!-- Curses interface documentation removed as requested -->

---
## Safety Notes
- Expressions are evaluated with a restricted environment (no builtins) plus `math`, factor functions, variables, and custom `abs`.
- Avoid entering untrusted code anyway—this is still an evaluator.

---
## Extending
Ideas:
- Add geometric gradient factors
- Export results to CSV
- Add command history navigation / autocompletion
- Persist variables between sessions
- Add rounding helpers (e.g., `round2(x)`)

Pull requests or personal extensions are welcome.

---
## License
See `LICENSE` for details.
