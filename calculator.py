#!/usr/bin/env python3
"""
Finance Factors CLI

Usage examples (run the script and type commands at the prompt):
  A_P(2.5%, 10)
  F_A(7%, 12)
  P_F(5, 3)          # You can omit the %; numbers are treated as percent by default.
  A_G(4%, 8)
  P_G(4, 8)

Commands:
  - F_P  : F given P = (1+i)^n
  - P_F  : P given F = (1+i)^-n
  - P_A  : P given A = (1 - (1+i)^-n)/i
  - A_P  : A given P = i(1+i)^n / ((1+i)^n - 1)
  - F_A  : F given A = ((1+i)^n - 1)/i
  - A_F  : A given F = i / ((1+i)^n - 1)
  - A_G  : A given arithmetic gradient G = (1/i) - n/((1+i)^n - 1)
           (gradient defined as: 0, G, 2G, ..., (n-1)G at periods 1..n)
  - P_G  : P given arithmetic gradient G = (A_G) * (P_A)
           (computed via A_G * P_A for numerical stability)

Notes:
  - Enter interest as a percentage (e.g., '2.5%' or '2.5').
  - i=0 is handled using the correct limit formulas.
  - Type 'help' to reprint this message, or 'quit' / 'exit' to leave.
"""
import re
import math
import sys
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # fallback if colorama is not installed
    class Dummy:
        RESET_ALL = ''
        RED = ''
        GREEN = ''
        YELLOW = ''
        CYAN = ''
        MAGENTA = ''
        BLUE = ''
        WHITE = ''
    Fore = Style = Dummy()

HELP = __doc__

# ------- Core factor formulas -------

def _pow1p(i, n):
    # Stable power for (1+i)^n
    return (1.0 + i) ** n

def F_P(i, n):
    return _pow1p(i, n)

def P_F(i, n):
    return 1.0 / _pow1p(i, n)

def P_A(i, n):
    if i == 0.0:
        return float(n)
    return (1.0 - _pow1p(i, -n)) / i

def A_P(i, n):
    if i == 0.0:
        return 1.0 / n if n != 0 else float('inf')
    x = _pow1p(i, n)
    return i * x / (x - 1.0)

def F_A(i, n):
    if i == 0.0:
        return float(n)
    return (_pow1p(i, n) - 1.0) / i

def A_F(i, n):
    if i == 0.0:
        return 1.0 / n if n != 0 else float('inf')
    return i / (_pow1p(i, n) - 1.0)

def A_G(i, n):
    if i == 0.0:
        # limit as i -> 0 for arithmetic gradient with 0, G, 2G, ..., (n-1)G
        return (n - 1.0) / 2.0
    return (1.0 / i) - (n / (_pow1p(i, n) - 1.0))

def P_G(i, n):
    # Use relation P/G = (A/G) * (P/A)
    return A_G(i, n) * P_A(i, n)

FACTOR_FUNCS = {
    'F_P': F_P,
    'P_F': P_F,
    'P_A': P_A,
    'A_P': A_P,
    'F_A': F_A,
    'A_F': A_F,
    'A_G': A_G,
    'P_G': P_G,
}

FACTOR_ALIASES = {k.lower(): k for k in FACTOR_FUNCS}

CALL_RE = re.compile(r"""
    ^\s*
    (?P<factor>[A-Za-z]+_[A-Za-z]+)   # e.g., A_P
    \s*\(\s*
    (?P<i>[-+]?\d+(\.\d+)?)(\s*%)?    # interest as percent, optional %
    \s*,\s*
    (?P<n>\d+)\s*
    \)\s*$
""", re.VERBOSE)

def parse_line(line):
    m = CALL_RE.match(line)
    if not m:
        raise ValueError("Could not parse. Expected like: A_P(2.5%, 10)")
    factor = m.group('factor').strip()
    i_percent = float(m.group('i'))
    # Interpret numbers as percentages by default (2.5 -> 2.5%)
    i = i_percent / 100.0
    n = int(m.group('n'))
    key = FACTOR_ALIASES.get(factor.lower())
    if key is None:
        raise ValueError(f"Unknown factor '{factor}'. Try one of: {', '.join(FACTOR_FUNCS.keys())}")
    return key, i, n

def evaluate(expr):
    name, i, n = parse_line(expr)
    val = FACTOR_FUNCS[name](i, n)
    return name, i, n, val

def repl():
    print(Fore.CYAN + Style.BRIGHT + HELP + Style.RESET_ALL)
    import os
    user_vars = {}
    case_stack = []
    screen_stack = []  # stores (user_vars, session_history)
    session_history = []  # stores (input, output) tuples
    in_case = False
    def print_history(history):
        for inp, outp in history:
            if inp is not None:
                print(Fore.YELLOW + Style.BRIGHT + f"factor> {inp}" + Style.RESET_ALL)
            if outp is not None:
                print(outp)

    def print_intro():
        box_color = Fore.BLUE + Style.BRIGHT
        title_color = Fore.MAGENTA + Style.BRIGHT
        desc_color = Fore.CYAN + Style.BRIGHT
        border = box_color + "=" * 60 + Style.RESET_ALL
        title = title_color + "FINANCIAL CALCULATOR CLI" + Style.RESET_ALL
        desc = desc_color + "Type mathematical expressions, finance factors, or commands.\nType 'help' for instructions, 'cls' to clear, 'case' to start a scoped session." + Style.RESET_ALL
        print(border)
        print(title.center(60))
        print(desc.center(60))
        print(border)

    # Initial screen content
    os.system('cls' if os.name == 'nt' else 'clear')
    print_intro()
    while True:
        try:
            line = input(Fore.YELLOW + Style.BRIGHT + "factor> " + Style.RESET_ALL).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.lower() in {"", "quit", "exit"}:
            print(Fore.MAGENTA + "Goodbye!" + Style.RESET_ALL)
            break
        if line.lower() == "help":
            print(Fore.CYAN + Style.BRIGHT + HELP + Style.RESET_ALL)
            session_history.append((line, Fore.CYAN + Style.BRIGHT + HELP + Style.RESET_ALL))
            continue
        if line.lower() == "cls":
            os.system('cls' if os.name == 'nt' else 'clear')
            session_history = []
            continue
        if line.lower() == "case":
            # Save current variables and session history
            screen_stack.append((user_vars.copy(), session_history.copy()))
            user_vars = {}
            session_history = []
            in_case = True
            os.system('cls' if os.name == 'nt' else 'clear')
            print(Fore.MAGENTA + Style.BRIGHT + "Case started. Variables now local to this case." + Style.RESET_ALL)
            session_history.append((line, Fore.MAGENTA + Style.BRIGHT + "Case started. Variables now local to this case." + Style.RESET_ALL))
            continue
        if line.lower() == "endcase":
            if screen_stack:
                user_vars, prev_history = screen_stack.pop()
                in_case = False
                os.system('cls' if os.name == 'nt' else 'clear')
                print(Fore.MAGENTA + Style.BRIGHT + "Case ended. Previous variables restored." + Style.RESET_ALL)
                print_history(prev_history)
                session_history = prev_history
                session_history.append((line, Fore.MAGENTA + Style.BRIGHT + "Case ended. Previous variables restored." + Style.RESET_ALL))
            else:
                print(Fore.RED + Style.BRIGHT + "No case to end." + Style.RESET_ALL)
                session_history.append((line, Fore.RED + Style.BRIGHT + "No case to end." + Style.RESET_ALL))
            continue
        # Variable assignment: x = 49.5
        assign_match = re.match(r'^\s*([a-zA-Z_]\w*)\s*=\s*(.+)$', line)
        if assign_match:
            var_name = assign_match.group(1)
            var_value_expr = assign_match.group(2)
            try:
                safe_env = dict(FACTOR_FUNCS)
                safe_env.update({
                    'math': math,
                    '__builtins__': {},
                })
                # Provide custom abs (remove negative sign) since builtins are stripped
                safe_env['abs'] = lambda x: -x if x < 0 else x
                for k in dir(math):
                    if not k.startswith('_'):
                        safe_env[k] = getattr(math, k)
                safe_env.update(user_vars)
                var_value_expr = re.sub(r'(\d+(?:\.\d+)?)\s*%', lambda m: str(float(m.group(1))/100), var_value_expr)
                value = eval(var_value_expr, safe_env)
                user_vars[var_name] = value
                session_history.append((line, None))
            except Exception as e:
                err = Fore.RED + Style.BRIGHT + f"Error in assignment: {e}" + Style.RESET_ALL
                print(err)
                session_history.append((line, err))
            continue
        # Print variable value if line is a variable name
        var_print_match = re.match(r'^\s*([a-zA-Z_]\w*)\s*$', line)
        if var_print_match:
            var_name = var_print_match.group(1)
            if var_name in user_vars:
                outp = Fore.CYAN + Style.BRIGHT + f"{var_name} = {user_vars[var_name]}" + Style.RESET_ALL
                print(outp)
                session_history.append((line, outp))
            else:
                outp = Fore.RED + Style.BRIGHT + f"Variable '{var_name}' not found in current scope." + Style.RESET_ALL
                print(outp)
                session_history.append((line, outp))
            continue
        try:
            safe_env = dict(FACTOR_FUNCS)
            safe_env.update({
                'math': math,
                '__builtins__': {},
            })
            # Provide custom abs function (remove negative sign)
            safe_env['abs'] = lambda x: -x if x < 0 else x
            for k in dir(math):
                if not k.startswith('_'):
                    safe_env[k] = getattr(math, k)
            safe_env.update(user_vars)
            expr = re.sub(r'(\d+(?:\.\d+)?)\s*%', lambda m: str(float(m.group(1))/100), line)
            result = eval(expr, safe_env)
            outp = Fore.GREEN + Style.BRIGHT + f"Result: {result}" + Style.RESET_ALL
            print(outp)
            session_history.append((line, outp))
        except Exception as e:
            outp = Fore.RED + Style.BRIGHT + f"Error: {e}" + Style.RESET_ALL
            print(outp)
            session_history.append((line, outp))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # allow quick one-off evaluation via CLI args
        expr = " ".join(sys.argv[1:])
        try:
            name, i, n, val = evaluate(expr)
            print(f"{name} @ i={i*100:.6g}%, n={n}  ->  {val:.12f}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        repl()
