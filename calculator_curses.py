import sys
try:
    import curses
    from curses import textpad
except Exception:
    print("Curses not available. On Windows, install 'windows-curses' with: pip install windows-curses")
    sys.exit(1)
import re
import math

HELP = """
Finance Factors CLI

Commands:
  - F_P  : F given P = (1+i)^n
  - P_F  : P given F = (1+i)^-n
  - P_A  : P given A = (1 - (1+i)^-n)/i
  - A_P  : A given P = i(1+i)^n / ((1+i)^n - 1)
  - F_A  : F given A = ((1+i)^n - 1)/i
  - A_F  : A given F = i / ((1+i)^n - 1)
  - A_G  : A given arithmetic gradient G = (1/i) - n/((1+i)^n - 1)
  - P_G  : P given arithmetic gradient G = (A_G) * (P_A)

Other:
  - case, endcase, cls, help, quit
"""

# ------- Core factor formulas -------
def _pow1p(i, n):
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
        return (n - 1.0) / 2.0
    return (1.0 / i) - (n / (_pow1p(i, n) - 1.0))

def P_G(i, n):
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
    (?P<factor>[A-Za-z]+_[A-Za-z]+)
    \s*\(\s*
    (?P<i>[-+]?\d+(\.\d+)?)(\s*%)?
    \s*,\s*
    (?P<n>\d+)\s*
    \)\s*$
""", re.VERBOSE)

def evaluate(expr, user_vars):
    safe_env = dict(FACTOR_FUNCS)
    safe_env.update({'math': math, '__builtins__': {}})
    for k in dir(math):
        if not k.startswith('_'):
            safe_env[k] = getattr(math, k)
    safe_env.update(user_vars)
    expr = re.sub(r'(\d+(?:\.\d+)?)\s*%', lambda m: str(float(m.group(1))/100), expr)
    return eval(expr, safe_env)

def curses_repl(stdscr):
    # Colors
    curses.curs_set(1)
    try:
        curses.start_color()
        curses.use_default_colors()
    except Exception:
        pass
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_BLUE, -1)
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)
    curses.init_pair(6, curses.COLOR_GREEN, -1)
    curses.init_pair(7, curses.COLOR_RED, -1)

    maxy, maxx = stdscr.getmaxyx()
    sidebar_w = 30
    header_h = 3
    input_box_h = 3
    footer_h = 1

    user_vars = {}
    case_stack = []  # (vars, history)
    session_history = []  # (input, output, is_error)
    history_scroll = 0

    prompt = "factor> "

    def draw_header():
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(0, 0, " " * maxx)
        stdscr.attroff(curses.color_pair(2))
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(1, 0, " FINANCIAL CALCULATOR CLI ".center(maxx))
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(2, 0, " Expressions, finance factors, variables, and cases ".center(maxx))
        stdscr.attroff(curses.color_pair(4))

    def draw_sidebar():
        help_lines = [
            "Commands:",
            "  help      Show help/info",
            "  cls       Clear history",
            "  case      Start scoped session",
            "  endcase   End scoped session",
            "  quit      Exit calculator",
            "",
            "Finance Factors:",
            "  F_P, P_F, P_A, A_P",
            "  F_A, A_F, A_G, P_G",
            "",
            "Shortcuts:",
            "  x = 10    Assign variable",
            "  x         Print variable",
            "  A_P(5%, 10) * 100",
        ]
        for i, line in enumerate(help_lines):
            attr = curses.color_pair(4) | (curses.A_BOLD if line.endswith(":") else 0)
            stdscr.attron(attr)
            y = header_h + 1 + i
            if y < maxy - footer_h:
                stdscr.addstr(y, 1, line[:sidebar_w-2].ljust(sidebar_w-2))
            stdscr.attroff(attr)
        # Variables title
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        y = min(maxy - footer_h - 5, header_h + len(help_lines) + 2)
        stdscr.addstr(y, 1, "Variables:")
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        var_lines = [f"  {k} = {v}" for k, v in user_vars.items()]
        for i, line in enumerate(var_lines[:max(0, maxy - y - footer_h - 2)]):
            stdscr.attron(curses.color_pair(4))
            stdscr.addstr(y + 1 + i, 1, line[:sidebar_w-2].ljust(sidebar_w-2))
            stdscr.attroff(curses.color_pair(4))

    def draw_history():
        nonlocal history_scroll
        hist_y = header_h
        hist_x = sidebar_w
        hist_h = maxy - header_h - input_box_h - footer_h
        hist_w = maxx - sidebar_w
        # Render history lines
        rendered = []
        for inp, outp, is_err in session_history:
            rendered.append((prompt + inp if inp is not None else "", False))
            if outp:
                rendered.append(("  " + str(outp), is_err))
        total_lines = len(rendered)
        # Clamp scroll
        max_scroll = max(0, total_lines - hist_h)
        history_scroll = max(0, min(history_scroll, max_scroll))
        start = history_scroll
        view = rendered[start:start+hist_h]
        # Clear area
        for i in range(hist_h):
            stdscr.move(hist_y + i, hist_x)
            stdscr.clrtoeol()
        # Draw
        for i, (line, is_err) in enumerate(view):
            color = curses.color_pair(6)
            if is_err:
                color = curses.color_pair(7)
            elif line.startswith(prompt):
                color = curses.color_pair(5)
            stdscr.attron(color)
            stdscr.addstr(hist_y + i, hist_x + 1, line[:hist_w-2])
            stdscr.attroff(color)

    def draw_input_box():
        inp_y = maxy - input_box_h - footer_h
        inp_x = sidebar_w
        inp_w = maxx - sidebar_w
        # Box
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(inp_y, inp_x, "+" + "-"*(inp_w-2) + "+")
        stdscr.addstr(inp_y+2, inp_x, "+" + "-"*(inp_w-2) + "+")
        stdscr.addstr(inp_y+1, inp_x, "|")
        stdscr.addstr(inp_y+1, inp_x+inp_w-1, "|")
        stdscr.attroff(curses.color_pair(2))
        stdscr.attron(curses.color_pair(5))
        stdscr.addstr(inp_y+1, inp_x+1, prompt)
        stdscr.attroff(curses.color_pair(5))
        # Inner edit window
        edit_x = inp_x + 1 + len(prompt)
        edit_w = max(1, inp_w - 2 - len(prompt))
        edit_win = curses.newwin(1, edit_w, inp_y+1, edit_x)
        return edit_win

    def draw_status(text="Ready"):
        mode = "CASE" if case_stack else "NORMAL"
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(maxy-1, 0, (f" {text} | Mode: {mode} ").ljust(maxx))
        stdscr.attroff(curses.color_pair(2))

    def accept_and_eval(command: str):
        cmd = command.strip()
        if cmd == "":
            # Append blank line to history to mimic cmd-style new line
            session_history.append(("", None, False))
            return
        # Built-ins
        if cmd.lower() in {"quit", "exit"}:
            raise SystemExit
        if cmd.lower() == "help":
            session_history.append((cmd, HELP, False))
            return
        if cmd.lower() == "cls":
            session_history.clear()
            return
        if cmd.lower() == "case":
            case_stack.append((user_vars.copy(), session_history.copy()))
            user_vars.clear()
            session_history.clear()
            return
        if cmd.lower() == "endcase":
            if case_stack:
                old_vars, old_hist = case_stack.pop()
                user_vars.clear()
                user_vars.update(old_vars)
                session_history = old_hist
            else:
                session_history.append((cmd, "No case to end.", True))
            return
        # Assignment
        m = re.match(r'^\s*([a-zA-Z_]\w*)\s*=\s*(.+)$', cmd)
        if m:
            name = m.group(1)
            rhs = m.group(2)
            try:
                val = evaluate(rhs, user_vars)
                user_vars[name] = val
                session_history.append((cmd, None, False))
            except Exception as e:
                session_history.append((cmd, f"Error in assignment: {e}", True))
            return
        # Variable echo
        m = re.match(r'^\s*([a-zA-Z_]\w*)\s*$', cmd)
        if m:
            name = m.group(1)
            if name in user_vars:
                session_history.append((cmd, f"{name} = {user_vars[name]}", False))
            else:
                session_history.append((cmd, f"Variable '{name}' not found in current scope.", True))
            return
        # Expression
        try:
            result = evaluate(cmd, user_vars)
            session_history.append((cmd, f"Result: {result}", False))
        except Exception as e:
            session_history.append((cmd, f"Error: {e}", True))

    stdscr.nodelay(False)
    while True:
        stdscr.erase()
        maxy, maxx = stdscr.getmaxyx()
        draw_header()
        draw_sidebar()
        draw_history()
        draw_status()
        stdscr.refresh()
        # Draw input and edit
        edit_win = draw_input_box()
        tb = textpad.Textbox(edit_win, insert_mode=True)
        def validator(ch):
            # Submit on Enter
            if ch in (10, 13):
                return 7  # Ctrl-G ends editing
            return ch
        try:
            s = tb.edit(validator)
        except Exception:
            s = ""
        cmd = s.strip()
        try:
            accept_and_eval(cmd)
        except SystemExit:
            break

if __name__ == "__main__":
    curses.wrapper(curses_repl)
