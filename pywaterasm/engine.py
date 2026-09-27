"""pywaterasm engine: parse .inwt model definition files and generate
standalone ASM simulation scripts (.py), single-tank or multi-tank A2O.

Usage:
    python -m pywaterasm.engine input/ASM1.inwt -o generated_model/asm1_tank.py

.inwt format (INI-like), 8 parts plus an optional [TimeSeries] block:
    [META]           model metadata (name, source, units)
    [COMPONENTS]     4-column pipe table, header comment row first:
                     #note# name in code | name in chemical | unit | phase
                     S_I  | "Soluble inert organic matter" | mg COD/L | soluble
    [PARAMS]         4-column pipe table like [Components]:
                     #note# name in code | name in chemical | unit | value
                     mu_H | "Maximum heterotrophic growth rate" | 1/d | 4.0
    [PROCESSES]      4-column pipe table like [Components]:
                     #note# name in code | name in chemical | reactants | products
                     P1 | "Aerobic hydrolysis" | X_S | S_F, S_I
    [STOICHIOMETRY]  rows: "P1 | S_S = -1 / Y_H"   (Petersen matrix, non-zero)
    [RATES]          2-column pipe table; rate Rk belongs to process Pk and
                     may reference earlier rates:
                     #note# name in code | rate expression
                     R1 | mu_H * monod(S_S, K_S) * ... * X_BH
    [TANK]/[BOUNDARY:name]/[INITIAL]/[SOLVER]
                     single CSTR + aeration boundary and time integration.
                     Boundary values: number, 'series:<column>' or
                     'expr:<expression over series columns and params>';
                     [INITIAL]: explicit values or 'mode = steady' (warm
                     start from the mean-influent steady state).
    [TIMESERIES]     optional multi-column time table: a
                     '#note# time | name1 | ...' header row (optional
                     ':linear' per column, default ':step'), followed by
                     '|'-separated numeric rows, time strictly increasing
    [MAPPING]        3-column pipe table covering EVERY component and parameter:
                     #note# name in code | name in chemical | name in regular expression
                     S_I | "Soluble inert organic matter" | S_sub_I
                     the regular-expression name uses the symbol_sub_<sub>_sep_<sub>
                     style (e.g. S_O2 -> S_sub_O_sub_2) for report generation.
Rate expressions may use helpers monod(S,K), inh(S,K) and reference any
component or parameter by name; a rate may reference an earlier rate (R8 uses R7, written R8 | ... * R7 * ...).
"""
from __future__ import annotations

import argparse
import configparser
import re
from pathlib import Path

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_HELPERS = {"monod", "inh"}


class AsmError(Exception):
    """Raised when the .inwt file violates the format rules."""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def _extract_table(text: str, section: str, ncols: int = 4) -> tuple[list[list[str]], str]:
    """Parse a section written as a 4-column pipe table (a | b | c | d).

    The header row and any other comment/blank lines are ignored. Returns
    (rows, remaining text with the entry lines removed, still parseable by
    configparser).
    """
    lines = text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if ln.strip().lower() == f"[{section.lower()}]"), None
    )
    if start is None:
        raise AsmError(f"missing [{section.capitalize()}] section")
    rows: list[list[str]] = []
    comments: list[str] = []
    j = start + 1
    while j < len(lines) and not lines[j].strip().startswith("["):
        s = lines[j].strip()
        if s and not s.startswith("#note#"):
            parts = [x.strip() for x in lines[j].split("|")]
            if len(parts) != ncols or not parts[0]:
                raise AsmError(
                    f"[{section.capitalize()}] expected {ncols} '|'-separated fields, got {s!r}"
                )
            rows.append(parts)
        else:
            comments.append(lines[j])
        j += 1
    kept = lines[: start + 1] + comments + lines[j:]
    return rows, "\n".join(kept) + "\n"


def _extract_components(text: str) -> tuple[dict, str]:
    """[Components]: code | "name in chemical" | unit | phase -> {code: {...}}."""
    rows, rest = _extract_table(text, "components")
    comps: dict[str, dict] = {}
    for code, name, unit, phase in rows:
        if code in comps:
            raise AsmError(f"[Components] duplicate code {code!r}")
        comps[code] = {"name": name.strip('"'), "unit": unit, "phase": phase}
    return comps, rest


def _extract_params(text: str) -> tuple[dict, str]:
    """[Params]: code | "name in chemical" | unit | value -> {code: float}."""
    rows, rest = _extract_table(text, "params")
    params: dict[str, float] = {}
    for code, name, unit, value in rows:
        if code in params:
            raise AsmError(f"[Params] duplicate code {code!r}")
        try:
            params[code] = float(value)
        except ValueError:
            raise AsmError(f"[Params] {code}: value must be numeric, got {value!r}") from None
    return params, rest


def _extract_processes(text: str, comps: dict) -> tuple[dict, str]:
    """[Processes]: code | "name in chemical" | reactants | products -> {code: {...}}."""
    rows, rest = _extract_table(text, "processes")
    procs: dict[str, dict] = {}
    for code, name, reactants, products in rows:
        if code in procs:
            raise AsmError(f"[Processes] duplicate code {code!r}")
        split = lambda s: [x.strip() for x in s.split(",") if x.strip()]
        reac, prod = split(reactants), split(products)
        unknown = [c for c in reac + prod if c not in comps]
        if unknown:
            raise AsmError(f"[Processes] {code}: unknown components {unknown}")
        procs[code] = {
            "name": name.strip('"'),
            "reactants": reac,
            "products": prod,
            "components": reac + prod,
        }
    return procs, rest


def _extract_rates(text: str) -> tuple[dict, str]:
    """[Rates]: Rk | expression -> {Rk: expression} (2-column pipe table)."""
    rows, rest = _extract_table(text, "rates", ncols=2)
    rates: dict[str, str] = {}
    for code, expr in rows:
        if code in rates:
            raise AsmError(f"[Rates] duplicate code {code!r}")
        rates[code] = expr
    return rates, rest


def _extract_mapping(text: str) -> tuple[dict, str]:
    """[Mapping]: code | "meaning" | regex-name -> {code: {...}} (3-column pipe table).

    The section is optional; a missing [Mapping] yields an empty dict.
    """
    if not re.search(r"(?im)^\s*\[mapping\]\s*$", text):
        return {}, text
    rows, rest = _extract_table(text, "mapping", ncols=3)
    mapping: dict[str, dict] = {}
    for code, meaning, regex_name in rows:
        if code in mapping:
            raise AsmError(f"[Mapping] duplicate code {code!r}")
        mapping[code] = {"meaning": meaning.strip('"'), "latex": regex_name}
    return mapping, rest


def _extract_timeseries(text: str) -> tuple[dict | None, str]:
    """[TimeSeries]: optional multi-column time table.

    A '#note# time | name1 | name2 ...' header row declares the columns
    (optional ':linear' suffix per column, default ':step'); the following
    rows are '|'-separated numbers with time in the first column, strictly
    increasing. Returns ({"time": [...], "cols": {name: {"values": [...],
    "interp": kind}}} or None when the section is absent, remaining text).
    """
    if not re.search(r"(?im)^\s*\[timeseries\]\s*$", text):
        return None, text
    lines = text.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip().lower() == "[timeseries]")
    cols: list[tuple[str, str]] | None = None
    rows: list[list[float]] = []
    kept: list[str] = []
    j = start + 1
    while j < len(lines) and not lines[j].strip().startswith("["):
        s = lines[j].strip()
        if not s:
            kept.append(lines[j])
            j += 1
            continue
        if s.startswith("#note#"):
            body = s[len("#note#"):].strip()
            parts = [x.strip() for x in body.split("|")]
            if cols is None and len(parts) >= 2 and all(
                re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(:linear|:step)?", p) for p in parts
            ):
                cols = []
                for p in parts:
                    m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?::(linear|step))?", p)
                    cols.append((m.group(1), m.group(2) or "step"))
            else:
                kept.append(lines[j])
            j += 1
            continue
        parts = [x.strip() for x in lines[j].split("|")]
        try:
            rows.append([float(x) for x in parts])
        except ValueError:
            raise AsmError(
                f"[TimeSeries] expected numeric '|'-separated row, got {lines[j].rstrip()!r}"
            ) from None
        j += 1
    if cols is None:
        raise AsmError("[TimeSeries] missing column header row: '#note# time | name1 | ...'")
    if len(rows) < 2:
        raise AsmError("[TimeSeries] need at least 2 data rows")
    if any(len(r) != len(cols) for r in rows):
        raise AsmError(f"[TimeSeries] every row must have {len(cols)} columns")
    if cols[0][0].lower() != "time":
        raise AsmError("[TimeSeries] first column must be named 'time'")
    t_values = [r[0] for r in rows]
    if any(b <= a for a, b in zip(t_values, t_values[1:])):
        raise AsmError("[TimeSeries] time column must be strictly increasing")
    col_dict = {
        name: {"values": [r[i] for r in rows], "interp": kind}
        for i, (name, kind) in enumerate(cols[1:], start=1)
    }
    kept_text = lines[: start + 1] + kept + lines[j:]
    return {"time": t_values, "cols": col_dict}, "\n".join(kept_text) + "\n"


def _classify_value(raw: str, series_names: set, params: dict, where: str) -> dict:
    """Classify a boundary/tank value: number | 'series:<col>' | 'expr:<...>' | '-'.

    An optional '~ <number>' suffix declares a constant fallback, used for the
    steady phase when the model has no [TimeSeries] (or as the declared mean)."""
    s = raw.strip()
    fb = None
    if "~" in s:
        s, fb_raw = s.split("~", 1)
        s = s.strip()
        try:
            fb = float(fb_raw)
        except ValueError:
            raise AsmError(
                f"{where}: fallback after '~' must be a number, got {fb_raw.strip()!r}"
            ) from None
    if s == "-":
        # dash: bind the same-named [TimeSeries] column if it exists,
        # otherwise use a built-in steady estimate (resolved per flow key)
        item = {"kind": "dash"}
        if fb is not None:
            item["fallback"] = fb
        return item
    if s.lower().startswith("series:"):
        name = s.split(":", 1)[1].strip()
        if name not in series_names:
            if fb is not None:
                # no [TimeSeries]: the '~' fallback makes this a plain constant
                return {"kind": "const", "value": fb}
            raise AsmError(f"{where}: unknown series column {name!r} (define it in [TimeSeries])")
        item = {"kind": "series", "name": name}
        if fb is not None:
            item["fallback"] = fb
        return item
    if s.lower().startswith("expr:"):
        expr = s.split(":", 1)[1].strip()
        allowed = set(series_names) | set(params)
        idents = set(_IDENT.findall(expr))
        unknown = [t for t in idents if t not in allowed and not t[0].isdigit()]
        if unknown and fb is None:
            raise AsmError(f"{where}: unknown identifier(s) {unknown} in expression {expr!r}")
        # with a '~' fallback, unknown identifiers are tolerated (fallback covers
        # the no-[TimeSeries] case; they must resolve once a series defines them)
        env = {t: 1.0 for t in idents}
        try:
            float(eval(expr, {"__builtins__": {}}, env))
        except ZeroDivisionError:
            pass  # 1.0 substitution can hit guards; ok
        except Exception as e:  # noqa: BLE001
            raise AsmError(f"{where}: expression error: {e} in {expr!r}")
        item = {"kind": "expr", "expr": expr}
        if fb is not None:
            item["fallback"] = fb
        return item
    try:
        item = {"kind": "const", "value": float(s)}
    except ValueError:
        raise AsmError(
            f"{where}: value must be a number, 'series:<column>' or "
            f"'expr:<expression>', got {raw!r}"
        ) from None
    if fb is not None:
        item["fallback"] = fb
    return item


def _const_of(item: dict, where: str) -> float:
    """Return the numeric value of a constant item; raise otherwise."""
    if item["kind"] != "const":
        raise AsmError(f"{where}: expected a constant number, got {item['kind']}")
    return item["value"]


def parse_asm(path: str | Path) -> dict:
    cp = configparser.ConfigParser(
        interpolation=None,
        comment_prefixes=("#note#",),
        inline_comment_prefixes=("#note#",),
    )
    cp.optionxform = str  # preserve case of component/parameter names
    ts, text = _extract_timeseries(Path(path).read_text(encoding="utf-8"))
    comps, text = _extract_components(text)
    params, text = _extract_params(text)
    procs, text = _extract_processes(text, comps)
    rates, text = _extract_rates(text)
    mapping, text = _extract_mapping(text)
    cp.read_string(text)
    secs = {s.lower(): s for s in cp.sections()}

    def sect(name: str):
        """case-insensitive section lookup"""
        return secs.get(name.lower())

    model: dict = {"meta": dict(cp[sect("META")]) if sect("META") else {}}

    model["components"] = comps  # parsed from the 4-column pipe table

    model["processes"] = procs  # parsed from the 4-column pipe table

    model["params"] = params  # parsed from the 4-column pipe table

    # stoichiometry: key "R1 | S_S", value expression over params
    stoich: dict[str, dict[str, str]] = {p: {} for p in procs}
    for key, expr in cp[sect("STOICHIOMETRY")].items():
        if "|" not in key:
            raise AsmError(f"[STOICHIOMETRY] {key}: expected 'R | comp = expr'")
        rid, comp = [s.strip() for s in key.split("|", 1)]
        if rid not in procs:
            raise AsmError(f"[STOICHIOMETRY] {key}: unknown process {rid!r}")
        if comp not in comps:
            raise AsmError(f"[STOICHIOMETRY] {key}: unknown component {comp!r}")
        if comp in stoich[rid]:
            raise AsmError(f"[STOICHIOMETRY] duplicate entry {key}")
        stoich[rid][comp] = expr
    model["stoich"] = stoich

    model["rates"] = rates  # parsed from the 2-column pipe table
    series_names = set(ts["cols"]) if ts else set()
    if sect("TANK"):
        model["tank"] = {
            k: _classify_value(v, series_names, params, f"[TANK] {k}")
            for k, v in cp[sect("TANK")].items()
        }
    else:
        model["tank"] = {}
    model["solver"] = dict(cp[sect("SOLVER")]) if sect("SOLVER") else {}

    bounds = {}
    for sec in cp.sections():
        if sec.lower().startswith("boundary:"):
            name = sec.split(":", 1)[1]
            items = {}
            for k, v in cp[sec].items():
                if k.lower() in ("from", "to"):
                    items[k] = {"kind": "ref", "ref": v.strip()}
                else:
                    items[k] = _classify_value(v, series_names, params, f"[{sec}] {k}")
            bounds[name] = items
    model["boundaries"] = bounds

    tanks = {}
    for sec in cp.sections():
        if sec.lower().startswith("tank:"):
            name = sec.split(":", 1)[1]
            props = {}
            for k, v in cp[sec].items():
                if k.lower() in ("v", "kla", "s_o_sat", "q"):
                    props[k] = _classify_value(v, series_names, params, f"[{sec}] {k}")
                else:
                    if k not in params:
                        raise AsmError(
                            f"[{sec}] {k}: unknown parameter override (not in [Params])"
                        )
                    props[k] = {"kind": "override", "value": float(v)}
            tanks[name] = props
    model["tanks"] = tanks

    init_tanks = {}
    for sec in cp.sections():
        if sec.lower().startswith("initial:"):
            init_tanks[sec.split(":", 1)[1]] = {
                k: float(v) for k, v in cp[sec].items()
            }
    model["initial_tanks"] = init_tanks
    model["timeseries"] = ts

    if sect("INITIAL"):
        raw_init = dict(cp[sect("INITIAL")])
        mode = raw_init.pop("mode", "explicit").strip()
        if mode not in ("explicit", "steady"):
            raise AsmError(f"[INITIAL] mode must be 'explicit' or 'steady', got {mode!r}")
        try:
            init_vals = {k: float(v) for k, v in raw_init.items()}
        except ValueError:
            raise AsmError("[INITIAL] values must be numeric; use 'mode = steady' for a warm start") from None
        model["initial"] = {"mode": mode, "values": init_vals}
    else:
        model["initial"] = {"mode": "explicit", "values": {}}

    model["mapping"] = mapping  # parsed from the 3-column pipe table
    return model


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(model: dict) -> None:
    comps, procs, params = model["components"], model["processes"], model["params"]

    for rid in procs:
        if "R" + rid[1:] not in model["rates"]:
            raise AsmError(f"[RATES] missing rate R{rid[1:]} for process {rid}")
        if not model["stoich"][rid]:
            raise AsmError(f"[STOICHIOMETRY] no entries for process {rid}")

    allowed = set(comps) | set(params) | _HELPERS | set(model["rates"])
    for rk, expr in model["rates"].items():
        if "P" + rk[1:] not in procs:
            raise AsmError(f"[RATES] {rk}: no matching process P{rk[1:]} in [PROCESSES]")
        for tok in _IDENT.findall(expr):
            if tok not in allowed and not tok[0].isdigit():
                raise AsmError(f"[RATES] {rid}: unknown identifier {tok!r} in {expr!r}")
        # numeric sanity check with all symbols = 1.0
        env = {t: 1.0 for t in _IDENT.findall(expr)}
        try:
            float(eval(expr, {"__builtins__": {}}, {**env, "monod": lambda a, b: 0.5, "inh": lambda a, b: 0.5}))
        except ZeroDivisionError:
            pass  # 1.0 substitution can hit guards like (X_S + eps); ok
        except Exception as e:  # noqa: BLE001
            raise AsmError(f"[RATES] {rid}: expression error: {e} in {expr!r}")

    for rid, coeffs in model["stoich"].items():
        for comp, expr in coeffs.items():
            for tok in _IDENT.findall(expr):
                if tok not in params:
                    raise AsmError(f"[STOICHIOMETRY] {key_of(rid, comp)}: unknown parameter {tok!r}")
            try:
                float(eval(expr, {"__builtins__": {}}, dict(params)))
            except Exception as e:  # noqa: BLE001
                raise AsmError(f"[STOICHIOMETRY] {key_of(rid, comp)}: {e} in {expr!r}")

    if (model.get("tanks") or model.get("tank")) and not model["boundaries"]:
        raise AsmError("[Tank] models require at least one [BOUNDARY:name] section")

    ts = model.get("timeseries")
    if model.get("tanks"):
        _validate_multitank(model, has_ts=ts is not None)
    elif ts is None:
        for bname, bnd in model["boundaries"].items():
            for c, item in bnd.items():
                if item["kind"] != "const":
                    raise AsmError(
                        f"[BOUNDARY:{bname}] {c}: {item['kind']} values require a [TimeSeries] section"
                    )
        for k, item in model["tank"].items():
            if item["kind"] != "const":
                raise AsmError(f"[TANK] {k}: {item['kind']} values require a [TimeSeries] section")
    else:
        for k, item in model["tank"].items():
            if item["kind"] != "const" and k.lower() != "q":
                raise AsmError(f"[TANK] {k}: only Q may reference a series")
    for c in model["initial"]["values"]:
        if c not in comps:
            raise AsmError(f"[INITIAL] unknown component {c!r}")

    mapping = model.get("mapping") or {}
    if mapping:
        known = set(comps) | set(params)
        extra = sorted(k for k in mapping if k not in known)
        missing = sorted(k for k in known if k not in mapping)
        if extra:
            raise AsmError(f"[MAPPING] entries that are not components/params: {extra}")
        if missing:
            raise AsmError(f"[MAPPING] missing entries for: {missing}")


def key_of(rid: str, comp: str) -> str:
    return f"{rid} | {comp}"


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------
def generate_py(model: dict, asm_name: str) -> str:
    if model.get("timeseries"):
        return _generate_py_dynamic(model, asm_name)
    return _generate_py_steady(model, asm_name)


def _generate_py_steady(model: dict, asm_name: str) -> str:
    comps = model["components"]
    procs = model["processes"]
    params = model["params"]
    stoich = model["stoich"]
    rates = model["rates"]
    tank = model["tank"]
    solver = model["solver"]
    bound = model["boundaries"]
    initial = model["initial"]
    mapping = model.get("mapping") or {}

    tV = _const_of(tank["V"], "[TANK] V")
    tQ = _const_of(tank["Q"], "[TANK] Q")
    tKLA = _const_of(tank["kLa"], "[TANK] kLa")
    tOSAT = _const_of(tank["S_O_sat"], "[TANK] S_O_sat")
    comp_list = list(comps)
    inf = bound[list(bound)[0]]  # single-tank: first boundary is the influent
    y0 = {
        c: _const_of(inf.get(c, {"kind": "const", "value": 0.0}),
                     f"[BOUNDARY:{list(bound)[0]}] {c}")
        for c in comp_list
    }
    for c, v in initial["values"].items():
        y0[c] = v

    # numeric Petersen matrix (params substituted at generation time)
    nu_rows = []
    for rid in procs:
        row = [0.0] * len(comp_list)
        for comp, expr in stoich[rid].items():
            row[comp_list.index(comp)] = float(eval(expr, {"__builtins__": {}}, dict(params)))
        nu_rows.append(row)

    p_lines = "\n".join(f"{k} = {v!r}" for k, v in params.items())
    unpack = ", ".join(comp_list)
    rate_lines = []
    for rid in procs:  # process order matches NU rows; a rate may use an earlier R
        rk = "R" + rid[1:]
        rate_lines.append(f"    {rk} = {rates[rk]}")
    ret = ", ".join("R" + rid[1:] for rid in procs)
    nu_text = ",\n    ".join("[" + ", ".join(f"{v:.6g}" for v in row) + "]" for row in nu_rows)
    y0_text = ", ".join(f"{y0[c]:.6g}" for c in comp_list)
    inf_text = ", ".join(
        f"{_const_of(inf.get(c, {'kind': 'const', 'value': 0.0}), f'[BOUNDARY:{list(bound)[0]}] {c}'):.6g}" for c in comp_list
    )

    # oxygen component: ASM1 uses S_O, ASM2d/modified ASM2d use S_O2
    o2_name = "S_O2" if "S_O2" in comps else "S_O"

    units_dict_text = "{" + ", ".join(repr(c) + ": " + repr(comps[c]["unit"]) for c in comp_list) + "}"
    if mapping:
        map_keys = [c for c in comp_list] + [k for k in params if k not in comps]
        map_keys = [k for k in map_keys if k in mapping]
        meaning_text = "{" + ", ".join(f"{k!r}: {mapping[k]['meaning']!r}" for k in map_keys) + "}"
        latex_text = "{" + ", ".join(f"{k!r}: {mapping[k]['latex']!r}" for k in map_keys) + "}"
        mapping_text = f"MEANING = {meaning_text}\nLATEX = {latex_text}"
    else:
        mapping_text = ""
    meta = model["meta"]
    NL = chr(10)
    return f'''"""Auto-generated by pywaterasm from {asm_name}. Do not edit by hand.

Model : {{meta.get("name", asm_name)}} ({{meta.get("source", "n/a")}})
Tank  : single CSTR, V={{tank["V"]:g}} m3, Q={{tank["Q"]:g}} m3/d,
        kLa={{tank["kLa"]:g}} 1/d, S_O,sat={{tank["S_O_sat"]:g}} mg/L
Run   : python {Path(asm_name).stem.lower()}_tank.py
"""
import numpy as np
from scipy.integrate import solve_ivp

# --- components (order of the state vector) --------------------------------
COMPONENTS = {comp_list!r}
UNITS = {units_dict_text}
{mapping_text}

# --- parameters ({meta.get("source", "defaults")}) ---------------------------
{p_lines}

# --- Petersen matrix: rows = processes {list(procs)}, cols = components -----
NU = np.array([
    {nu_text},
])

# --- single-tank boundary ----------------------------------------------------
V = {tV!r}          # m3
Q = {tQ!r}          # m3/d
KLA = {tKLA!r}      # 1/d
S_O_SAT = {tOSAT!r}  # mg/L
C_IN = np.array([{inf_text}])   # influent, mg/L


def monod(S, K):
    return S / (K + S)


def inh(S, K):
    return K / (K + S)


def rates(C):
    {unpack} = C
{NL.join(rate_lines)}
    return np.array([{ret}])


def rhs(t, C):
    C = np.maximum(C, 0.0)  # clip negatives to keep Monod terms stable
    rho = rates(C)
    dC = Q / V * (C_IN - C) + NU.T @ rho
    dC[COMPONENTS.index({o2_name!r})] += KLA * (S_O_SAT - C[COMPONENTS.index({o2_name!r})])
    return dC


def main():
    t_end = {float(solver.get("t_end", 30))!r}     # d
    dt = {float(solver.get("dt", 0.5))!r}          # d
    tol = {float(solver.get("steady_tol", 1e-3))!r}
    y0 = np.array([{y0_text}])
    sol = solve_ivp(rhs, (0.0, t_end), y0, method={solver.get("method", "LSODA")!r},
                    t_eval=np.arange(0.0, t_end + 1e-9, dt))
    assert sol.success, sol.message
    C_ss = sol.y[:, -1]
    resid = np.abs(rhs(sol.t[-1], C_ss))
    print(f"integration: {{sol.message}}  ({{len(sol.t)}} points to t={{t_end}} d)")
    print(f"steady-state check: max|dC/dt| = {{resid.max():.3e}} mg/L/d "
          f"(tol={{tol:g}}) -> {{'OK' if resid.max() < tol else 'NOT CONVERGED'}}")
    print()
    print(f"{{'component':<8}} {{'effluent':>12}} {{'influent':>12}}  unit")
    for j, c in enumerate(COMPONENTS):
        print(f"{{c:<8}} {{C_ss[j]:>12.3f}} {{C_IN[j]:>12.3f}}  {{UNITS[c]}}")
    cod_eff = sum(C_ss[j] for j, c in enumerate(COMPONENTS) if c.endswith(("S", "I", "BH", "BA", "P")))
    print()
    print(f"effluent total COD ~ {{cod_eff:.1f}} mg/L "
          f"(removal {{100*(1 - cod_eff / max(C_IN.sum(), 1e-9)):5.1f}} % of total input mass)")
    return sol, C_ss


if __name__ == "__main__":
    main()
'''


TEMPLATE_DYNAMIC = r'''"""Auto-generated by pywaterasm from @ASM@. Do not edit by hand.

Model : @NAME@ (@SOURCE@)
Tank  : single CSTR, V=@V@ m3, dynamic boundary, kLa=@KLA_V@ 1/d,
        S_O,sat=@OSAT@ mg/L
Run   : python @STEM@_tank.py  (writes @STEM@_dyn.csv)
"""
import csv
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

# --- components (order of the state vector) --------------------------------
COMPONENTS = @COMPS@
UNITS = @UNITS@
@MAPPING@

# --- parameters --------------------------------------------------------------
@PARAMS@

# --- Petersen matrix: rows = processes @PROCS@, cols = components -----------
NU = np.array([
@NU@
])

# --- time series (embedded from [TimeSeries]) --------------------------------
@TS@
T_END = @T_END@
DT = @DT@


def _lin(T, V, t):
    return float(np.interp(t, T, V))


def _step(T, V, t):
    i = int(np.clip(np.searchsorted(T, t, side="right") - 1, 0, len(T) - 1))
    return float(V[i])


def _mk(T, V, kind):
    if kind == "linear":
        return lambda t: _lin(T, V, t)
    return lambda t: _step(T, V, t)


@SERFUNCS@

# --- boundary ----------------------------------------------------------------
V = @V@              # m3
S_O_SAT = @OSAT@    # mg/L
@QRUN@
@KLARUN@


def monod(S, K):
    return S / (K + S)


def inh(S, K):
    return K / (K + S)


def rates(C):
    @UNPACK@ = C
@RATES@
    return np.array([@RET@])


@CIN@

C_MEAN = np.array([@CMEAN@])  # time-mean influent (warm start and reporting)
Q_MEAN = @QMEAN@
KLA_MEAN = @KMEAN@
IO2 = COMPONENTS.index(@O2@)


def rhs_dyn(t, C):
    C = np.maximum(C, 0.0)  # clip negatives to keep Monod terms stable
    rho = rates(C)
    dC = q_in(t) / V * (c_in(t) - C) + NU.T @ rho
    dC[IO2] += kla(t) * (S_O_SAT - C[IO2])
    return dC


def rhs_ss(t, C):
    C = np.maximum(C, 0.0)
    rho = rates(C)
    dC = Q_MEAN / V * (C_MEAN - C) + NU.T @ rho
    dC[IO2] += KLA_MEAN * (S_O_SAT - C[IO2])
    return dC


def main():
    y0 = np.array([@Y0@])
@WARM@
    sol = solve_ivp(rhs_dyn, (0.0, T_END), y0, method=@METHOD@,
                    t_eval=np.arange(0.0, T_END + 1e-9, DT))
    assert sol.success, sol.message
    eff = sol.y
    print(f"dynamic run: {sol.message}  ({len(sol.t)} points to t={T_END} d)")
    print()
    print(f"{'component':<8} {'influent(mean)':>14} {'effluent mean':>13} {'min':>9} {'max':>9}  unit")
    for j, c in enumerate(COMPONENTS):
        print(f"{c:<8} {C_MEAN[j]:>14.3f} {eff[j].mean():>13.3f} "
              f"{eff[j].min():>9.3f} {eff[j].max():>9.3f}  {UNITS[c]}")
    cod_idx = [j for j, c in enumerate(COMPONENTS) if c.endswith(@SUF@)]
    cod_in = sum(C_MEAN[j] for j in cod_idx)
    cod_eff = sum(eff[j].mean() for j in cod_idx)
    print()
    print(f"mean total COD: influent {cod_in:.1f} -> effluent {cod_eff:.1f} mg/L "
          f"(removal {100 * (1 - cod_eff / max(cod_in, 1e-9)):5.1f} %)")
    out_csv = Path(__file__).with_name(@CSV@)
    with out_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t", "Q_in"] + ["in_" + c for c in COMPONENTS] + list(COMPONENTS))
        for k, t in enumerate(sol.t):
            w.writerow([f"{t:.4f}", f"{q_in(t):.4f}"] +
                       [f"{v:.4f}" for v in c_in(t)] +
                       [f"{v:.4f}" for v in eff[:, k]])
    print(f"wrote {out_csv.name}: t, Q_in, influent and effluent concentrations")


if __name__ == "__main__":
    main()'''


def _generate_py_dynamic(model: dict, asm_name: str) -> str:
    """Generate a dynamic-run script with a time-varying boundary from [TimeSeries]."""
    comps = model["components"]
    procs = model["processes"]
    params = model["params"]
    stoich = model["stoich"]
    rates = model["rates"]
    tank = model["tank"]
    solver = model["solver"]
    bound = model["boundaries"]
    initial = model["initial"]
    ts = model["timeseries"]
    mapping = model.get("mapping") or {}
    meta = model["meta"]

    comp_list = list(comps)
    bname = list(bound)[0]
    inf = bound[bname]
    missing = [c for c in comp_list if c not in inf]
    if missing:
        raise AsmError(f"[BOUNDARY:{bname}] dynamic run needs every component; missing: {missing}")

    series_cols = ts["cols"]
    t_values = ts["time"]

    def series_mean(name: str) -> float:
        vals = series_cols[name]["values"]
        return sum(vals) / len(vals)

    def item_runtime(item: dict) -> str:
        """Generated-code snippet evaluating the boundary item at time t."""
        if item["kind"] == "const":
            return repr(item["value"])
        if item["kind"] == "series":
            return f"ser_{item['name']}(t)"

        def repl(m):
            tok = m.group(0)
            return f"ser_{tok}(t)" if tok in series_cols else tok

        return _IDENT.sub(repl, item["expr"])

    def item_mean(item: dict) -> float:
        """Time-mean of the item (constants as-is, series averaged, expr evaluated)."""
        if item["kind"] == "const":
            return item["value"]
        if item["kind"] == "series":
            return series_mean(item["name"])
        env = {n: series_mean(n) for n in series_cols}
        env.update(params)
        return float(eval(item["expr"], {"__builtins__": {}}, env))

    V = _const_of(tank["V"], "[TANK] V")
    s_osat = _const_of(tank["S_O_sat"], "[TANK] S_O_sat")
    kla_item = tank.get("kLa") or {"kind": "const", "value": 0.0}
    q_item = tank["Q"]
    q_mean = item_mean(q_item)
    kla_mean = item_mean(kla_item)

    # numeric Petersen matrix (params substituted at generation time)
    nu_rows = []
    for rid in procs:
        row = [0.0] * len(comp_list)
        for comp, expr in stoich[rid].items():
            row[comp_list.index(comp)] = float(eval(expr, {"__builtins__": {}}, dict(params)))
        nu_rows.append(row)

    o2_name = "S_O2" if "S_O2" in comps else "S_O"
    io2 = comp_list.index(o2_name)

    t_end = float(solver.get("t_end", t_values[-1]))
    dt = float(solver.get("dt", 0.25))
    ss_days = float(solver.get("ss_days", 400))
    method = repr(solver.get("method", "LSODA"))
    tol = float(solver.get("steady_tol", 1e-3))

    p_lines = "\n".join(f"{k} = {v!r}" for k, v in params.items())
    unpack = ", ".join(comp_list)
    rate_lines = [f"    R{rid[1:]} = {rates['R' + rid[1:]]}" for rid in procs]
    ret = ", ".join("R" + rid[1:] for rid in procs)
    nu_text = ",\n    ".join("[" + ", ".join(f"{v:.6g}" for v in row) + "]" for row in nu_rows)

    def fmt_arr(vals) -> str:
        return "np.array([" + ", ".join(f"{v:.6g}" for v in vals) + "])"

    ts_text = "\n".join(
        [f"TS_T = {fmt_arr(t_values)}"]
        + [f"TS_{n} = {fmt_arr(c['values'])}" for n, c in series_cols.items()]
    )
    ser_text = "\n".join(
        f"ser_{n} = _mk(TS_T, TS_{n}, {c['interp']!r})" for n, c in series_cols.items()
    )
    cin_text = "\n".join(f"        {item_runtime(inf[c])},  # {c}" for c in comp_list)
    cmean_text = ", ".join(f"{item_mean(inf[c]):.6g}" for c in comp_list)

    y0 = {c: item_mean(inf[c]) for c in comp_list}
    for c, v in initial["values"].items():
        y0[c] = v
    y0_text = ", ".join(f"{y0[c]:.6g}" for c in comp_list)

    q_run = (
        f"q_in = lambda t: ser_{q_item['name']}(t)"
        if q_item["kind"] == "series"
        else f"q_in = lambda t: {q_item['value']!r}"
    )
    kla_run = (
        f"kla = lambda t: ser_{kla_item['name']}(t)"
        if kla_item["kind"] == "series"
        else f"kla = lambda t: {kla_item['value']!r}"
    )

    units_dict_text = "{" + ", ".join(repr(c) + ": " + repr(comps[c]["unit"]) for c in comp_list) + "}"
    if mapping:
        map_keys = [c for c in comp_list] + [k for k in params if k not in comps]
        map_keys = [k for k in map_keys if k in mapping]
        meaning_text = "{" + ", ".join(f"{k!r}: {mapping[k]['meaning']!r}" for k in map_keys) + "}"
        latex_text = "{" + ", ".join(f"{k!r}: {mapping[k]['latex']!r}" for k in map_keys) + "}"
        mapping_text = f"MEANING = {meaning_text}\nLATEX = {latex_text}"
    else:
        mapping_text = ""

    if initial["mode"] == "steady":
        warm = (
            f"    sol_ss = solve_ivp(rhs_ss, (0.0, {ss_days!r}), y0, method={method},\n"
            f"                         t_eval=[{ss_days!r}])\n"
            "    assert sol_ss.success, sol_ss.message\n"
            "    y0 = sol_ss.y[:, -1]\n"
            f"    ss_resid = float(np.abs(rhs_ss({ss_days!r}, y0)).max())\n"
            '    print(f"warm start (mode = steady): max|dC/dt| = {ss_resid:.3e} mg/L/d")\n'
        )
    else:
        warm = ""

    stem = Path(asm_name).stem.lower()
    template = TEMPLATE_DYNAMIC
    return (
        template
        .replace("@ASM@", asm_name)
        .replace("@NAME@", str(meta.get("name", stem)))
        .replace("@SOURCE@", str(meta.get("source", "n/a")))
        .replace("@V@", repr(V))
        .replace("@KLA_V@", f"{kla_mean:g}")
        .replace("@OSAT@", repr(s_osat))
        .replace("@STEM@", stem)
        .replace("@COMPS@", repr(comp_list))
        .replace("@UNITS@", units_dict_text)
        .replace("@MAPPING@", mapping_text)
        .replace("@PARAMS@", p_lines)
        .replace("@PROCS@", str(list(procs)))
        .replace("@NU@", nu_text)
        .replace("@TS@", ts_text)
        .replace("@T_END@", repr(t_end))
        .replace("@DT@", repr(dt))
        .replace("@SERFUNCS@", ser_text)
        .replace("@QRUN@", q_run)
        .replace("@KLARUN@", kla_run)
        .replace("@UNPACK@", unpack)
        .replace("@RATES@", "\n".join(rate_lines))
        .replace("@RET@", ret)
        .replace("@CIN@", "def c_in(t):\n    return np.array([\n" + cin_text + "\n    ])")
        .replace("@CMEAN@", cmean_text)
        .replace("@QMEAN@", repr(q_mean))
        .replace("@KMEAN@", repr(kla_mean))
        .replace("@O2@", repr(o2_name))
        .replace("@Y0@", y0_text)
        .replace("@WARM@", warm.rstrip("\n"))
        .replace("@METHOD@", method)
        .replace("@SUF@", repr(("S", "I", "BH", "BA", "P")))
        .replace("@CSV@", repr(f"{stem}_dyn.csv"))
    )




# ---------------------------------------------------------------------------
# Multi-tank A2O generation: 5 module files (a1..a5)
# ---------------------------------------------------------------------------

MULTI_FILENAMES = (
    "a1influent2anaerobic.py",
    "a2anaerobic.py",
    "a3anoxic.py",
    "a4oxic.py",
    "a5oxic2effluent.py",
)


def _validate_multitank(model: dict, has_ts: bool) -> None:
    """Structural checks for the multi-tank A2O layout."""
    comps = model["components"]
    tanks = model["tanks"]
    bounds = model["boundaries"]
    tank_names = set(tanks) | {"clarifier"}

    for name, props in tanks.items():
        if "V" not in props:
            raise AsmError(f"[Tank:{name}] missing V")
        for k, item in props.items():
            if item["kind"] in ("series", "expr") and not has_ts and "fallback" not in item:
                raise AsmError(
                    f"[Tank:{name}] {k}: dynamic value needs a '~ <const>' fallback "
                    "(no [TimeSeries])"
                )

    for bname, bnd in bounds.items():
        for k, item in bnd.items():
            if item["kind"] == "ref":
                if item["ref"] not in tank_names:
                    raise AsmError(f"[BOUNDARY:{bname}] {k}: unknown tank {item['ref']!r}")
            elif item["kind"] in ("series", "expr") and not has_ts and "fallback" not in item:
                raise AsmError(
                    f"[BOUNDARY:{bname}] {k}: dynamic value needs a '~ <const>' fallback "
                    "(no [TimeSeries])"
                )

    need = {"influent", "effluent", "internal_recycle", "ras_recycle", "aeration"}
    missing_b = sorted(need - set(bounds))
    if missing_b:
        raise AsmError(f"multi-tank model missing boundary sections: {missing_b}")

    inf = bounds["influent"]
    miss = [c for c in comps if c not in inf]
    if miss:
        raise AsmError(
            f"[BOUNDARY:influent] must define all {len(comps)} components; missing: {miss}"
        )

    init_tanks = model.get("initial_tanks") or {}
    for name in tanks:
        if name not in init_tanks:
            raise AsmError(f"missing [Initial:{name}] section")
        miss = [c for c in comps if c not in init_tanks[name]]
        if miss:
            raise AsmError(f"[Initial:{name}] missing components: {miss}")


# Steady-state design estimates (PLANT totals) for 'Q_x = -' when the series is absent.
# They equal the old per-group '~' fallbacks x 4 (n_groups = 4 design point).
_DASH_EST = {
    "Q_in": 800.0, "Q_eff": 800.0,
    "Q_ana": 800.0, "Q_anox": 2800.0, "Q_aer": 2800.0,
    "Q_ir": 1600.0, "Q_r": 400.0, "Q_air": 2000.0,
    "Q_carbon": 0.12, "Q_chem": 0.08,
}


def _resolve_flow(item: dict, col: str, n_groups: int, series_cols: dict,
                  params: dict, where: str) -> dict:
    """Resolve 'Q_x = -': plant-total series column -> per-group item
    (runtime expr '<col> / n_groups>'); no series -> steady estimate const."""
    if item.get("kind") != "dash":
        return item
    if col in series_cols:
        return {"kind": "expr", "expr": f"{col} / {n_groups}"}
    est = item.get("fallback", _DASH_EST.get(col))
    if est is None:
        raise AsmError(
            f"{where}: 'Q = -' needs series column {col!r} or a declared '~ <num>' fallback"
        )
    return {"kind": "const", "value": est / n_groups}


def _const_of_item(item: dict, series_cols: dict, params: dict) -> float:
    """Steady-phase constant: declared '~' fallback wins, else time-mean."""
    if item["kind"] == "const":
        return item["value"]
    if "fallback" in item:
        return item["fallback"]
    if item["kind"] == "series":
        vals = series_cols[item["name"]]["values"]
        return sum(vals) / len(vals)
    env = {
        n: _const_of_item({"kind": "series", "name": n}, series_cols, params)
        for n in series_cols
    }
    env.update(params)
    return float(eval(item["expr"], {"__builtins__": {}}, env))


def _runtime_of_item(item: dict, series_cols: dict) -> str:
    """Generated-code snippet evaluating the item at time t."""
    if item["kind"] == "const":
        return repr(item["value"])
    if item["kind"] == "series":
        return f"ser_{item['name']}(t)"

    def repl(m):
        tok = m.group(0)
        return f"ser_{tok}(t)" if tok in series_cols else tok

    return _IDENT.sub(repl, item["expr"])


def _shared_block(model: dict) -> dict:
    """Code fragments shared by every generated module file."""
    comps = model["components"]
    procs = model["processes"]
    stoich = model["stoich"]
    rates = model["rates"]
    comp_list = list(comps)
    nu_rows = []
    for rid in procs:
        row = [0.0] * len(comp_list)
        for comp, expr in stoich[rid].items():
            row[comp_list.index(comp)] = float(
                eval(expr, {"__builtins__": {}}, dict(model["params"]))
            )
        nu_rows.append(row)
    return {
        "comp_list": comp_list,
        "comps_repr": repr(comp_list),
        "units": "{" + ", ".join(repr(c) + ": " + repr(comps[c]["unit"]) for c in comp_list) + "}",
        "nu": ",\n    ".join(
            "[" + ", ".join(f"{v:.6g}" for v in row) + "]" for row in nu_rows
        ),
        "unpack": ", ".join(comp_list),
        "rates": "\n".join(
            f"    R{rid[1:]} = {rates['R' + rid[1:]]}" for rid in procs
        ),
        "ret": ", ".join("R" + rid[1:] for rid in procs),
        "partic_idx": [
            j
            for j, c in enumerate(comp_list)
            if comps[c]["phase"].lower().startswith("part")
        ],
        "cod_idx": [j for j, c in enumerate(comp_list) if "COD" in comps[c]["unit"]],
    }


def _params_text(model: dict, tank_name: str | None) -> str:
    """Parameter constants, with per-tank overrides merged (generation time)."""
    params = dict(model["params"])
    if tank_name:
        for k, item in model["tanks"].get(tank_name, {}).items():
            if item.get("kind") == "override":
                params[k] = item["value"]
    return "\n".join(f"{k} = {v!r}" for k, v in params.items())


def _module_core(model: dict, sh: dict, tank_name: str | None) -> str:
    return f"""import numpy as np
from scipy.integrate import solve_ivp

COMPONENTS = {sh["comps_repr"]}
UNITS = {sh["units"]}
NU = np.array([
    {sh["nu"]},
])

{_params_text(model, tank_name)}


def monod(S, K):
    return S / (K + S)


def inh(S, K):
    return K / (K + S)


def rates(C):
    {sh["unpack"]} = C
{sh["rates"]}
    return np.array([{sh["ret"]}])
"""


def _fmt_arr(vals) -> str:
    return "np.array([" + ", ".join(f"{v:.6g}" for v in vals) + "])"


def generate_class(model: dict, asm_name: str) -> str:
    """Generate an instantiable kinetics package from a model-definition-only
    .inwt (sections 0-5, 8: no [Tank], no [Boundary]). The class exposes only
    the biochemical reaction term r(C) [mg/L/d]; the reactor balance (CSTR /
    PFR / SBR / ...), boundary conversion, initial values, mass conservation
    and calibration live on the caller side
    (see input/边界初值质量守恒说明.md)."""
    meta = model["meta"]
    mname = meta.get("name", Path(asm_name).stem)
    source = meta.get("source", "n/a")
    comps = model["components"]
    comp_list = list(comps)
    params = model["params"]
    sh = _shared_block(model)
    pname = set(params)
    io2 = comp_list.index("S_O2") if "S_O2" in comps else -1
    cls = re.sub(r"\W|^(?=\d)", "_", mname)

    def rp(m):
        tok = m.group(0)
        return f"p[{tok!r}]" if tok in pname else tok

    rates_text = "\n".join(
        f"        R{rid[1:]} = {_IDENT.sub(rp, model['rates']['R' + rid[1:]])}"
        for rid in model["processes"]
    )
    ret = ", ".join("R" + rid[1:] for rid in model["processes"])
    params_dict = "{" + ", ".join(f"{k!r}: {v!r}" for k, v in params.items()) + "}"
    return f'''"""Auto-generated by pywaterasm from {asm_name}. Do not edit by hand.

Model : {mname} ({source})
Usage : kinetics package only. Instance.r(C) returns the biochemical source
        term [mg/L/d]; build the reactor balance (CSTR/PFR/SBR), boundary
        conversion, initial values and calibration on the caller side -- see
        input/边界初值质量守恒说明.md.
"""

import numpy as np


def monod(S, K):
    return S / (K + S)


def inh(S, K):
    return K / (K + S)


class {cls}:
    """{mname} biokinetic package: process rates + Petersen stoichiometry.

    Deliberately reactor-agnostic: no tank volume, flows, aeration or
    external dosing here. The caller composes r(C) into whatever reactor
    balance applies (CSTR: dC/dt = Q/V (C_in - C) + r(C) + ...).
    Stoichiometric parameters are baked into NU; change them in the .inwt
    [Params] and regenerate."""

    COMPONENTS = {sh["comps_repr"]}
    UNITS = {sh["units"]}
    PROCESSES = {list(model["processes"])!r}
    PARAMS = {params_dict}
    N_C = {len(comp_list)}
    N_R = {len(model["processes"])}
    NU = np.array([
        {sh["nu"]},
    ])
    PARTICULATE = {sh["partic_idx"]!r}
    COD_IDX = {sh["cod_idx"]!r}
    IO2 = {io2}  # index of S_O2 (-1 if the model has none)

    def __init__(self, params=None):
        """params: kinetic parameter overrides (stoichiometric ones are
        baked into NU and can only be changed in the .inwt)."""
        self.p = dict(self.PARAMS)
        if params:
            self.p.update(params)

    def rates(self, C):
        """Process rates rho [1/d], one per entry in PROCESSES."""
        C = np.maximum(np.asarray(C, float), 0.0)
        p = self.p
        {sh["unpack"]} = C
{rates_text}
        return np.array([{ret}])

    def r(self, C):
        """Biochemical source term dC/dt = NU.T @ rho [mg/L/d]."""
        return self.NU.T @ self.rates(C)

    def cod(self, C):
        """Total COD of a state vector [mg/L]."""
        return float(sum(np.asarray(C)[j] for j in self.COD_IDX))
'''


def generate_multi(model: dict, asm_name: str) -> dict:
    """Generate the 5 coupled module files for the multi-tank A2O model."""
    meta = model["meta"]
    mname = meta.get("name", Path(asm_name).stem)
    source = meta.get("source", "n/a")
    comps = model["components"]
    comp_list = list(comps)
    tanks = model["tanks"]
    bounds = model["boundaries"]
    ts = model.get("timeseries")
    solver = model["solver"]
    series_cols = ts["cols"] if ts else {}
    sh = _shared_block(model)

    method = repr(solver.get("method", "LSODA"))
    dt = float(solver.get("dt", 0.25))
    ss_days = float(solver.get("ss_days", 400))
    tol = float(solver.get("steady_tol", 1e-3))
    rtol = float(solver.get("rtol", 1e-6))
    atol = float(solver.get("atol", 1e-9))
    ng_item = bounds.get("influent", {}).get("n_groups")
    if ng_item is not None:
        n_groups = int(_const_of_item(ng_item, series_cols, model["params"]))
    else:
        n_groups = model["params"].get("n_groups", 1)
    ng_eff = bounds.get("effluent", {}).get("n_groups")
    if ng_eff is not None and int(_const_of_item(ng_eff, series_cols, model["params"])) != n_groups:
        raise AsmError("[BOUNDARY:effluent] n_groups disagrees with [BOUNDARY:influent]")

    def header(fname: str, role: str) -> str:
        return (
            f'"""Auto-generated by pywaterasm from {asm_name}. Do not edit by hand.\n\n'
            f"Module : {fname} -- {role}\n"
            f"Model  : {mname} ({source})\n"
            f'Run    : python {fname}  (standalone self-test; coupled entry is a1influent2anaerobic.py)\n"""'
        )

    inf = bounds["influent"]
    cin_const = [_const_of_item(inf[c], series_cols, model["params"]) for c in comp_list]
    cin_const_text = _fmt_arr(cin_const)
    y0 = {
        name: [model["initial_tanks"][name][c] for c in comp_list]
        for name in tanks
    }

    V = {
        name: _const_of_item(props["V"], series_cols, model["params"])
        for name, props in tanks.items()
    }
    s_osat = 8.0
    if "S_O_sat" in tanks.get("aerobic", {}):
        s_osat = _const_of_item(tanks["aerobic"]["S_O_sat"], series_cols, model["params"])

    P = model["params"]
    # 'Q_x = -' binds the plant-total series column Q_x; per-group = /n_groups;
    # with no [TimeSeries] the built-in steady design estimate (_DASH_EST) is used.
    q_in = bounds["influent"].get("Q_in", {"kind": "dash"})
    q_ana = _resolve_flow(q_in, "Q_in", n_groups, series_cols, P, "[Boundary:influent] Q_in")
    q_ir = _resolve_flow(bounds["internal_recycle"]["Q_ir"], "Q_ir", n_groups,
                         series_cols, P, "[Boundary:internal_recycle] Q_ir")
    q_r = _resolve_flow(bounds["ras_recycle"]["Q_r"], "Q_r", n_groups,
                        series_cols, P, "[Boundary:ras_recycle] Q_r")
    q_air = _resolve_flow(bounds["aeration"]["Q_air"], "Q_air", n_groups,
                          series_cols, P, "[Boundary:aeration] Q_air")
    q_carbon = _resolve_flow(bounds["carbon_dose"]["Q_carbon"], "Q_carbon", n_groups,
                             series_cols, P, "[Boundary:carbon_dose] Q_carbon")
    s_dose = _const_of_item(bounds["carbon_dose"]["S_dose"], series_cols, P)
    f_pass = _const_of_item(bounds["ras_recycle"]["f_pass"], series_cols, P)
    q_eff_item = bounds["effluent"]["Q_eff"]
    if q_eff_item.get("kind") == "dash":  # plant total, NOT divided by n_groups
        if "Q_eff" in series_cols:
            q_eff_item = {"kind": "series", "name": "Q_eff"}
        else:
            q_eff_item = {"kind": "const", "value": q_eff_item.get("fallback", _DASH_EST["Q_eff"])}
    q_eff_const = _const_of_item(q_eff_item, series_cols, P)

    # declared tank through-flows: 'Q = -' -> plant-total series / n_groups;
    # a constant is a per-group design value (anaerobic Q is documentation only,
    # its through-flow is derived at runtime as Q_in/n_groups + Q_r/n_groups)
    TANK_FLOW_COL = {"anaerobic": "Q_ana", "anoxic": "Q_anox", "aerobic": "Q_aer"}
    tank_flow = {}
    for tname, props in tanks.items():
        if "Q" not in props:
            continue
        it = props["Q"]
        if it.get("kind") == "dash":
            col = TANK_FLOW_COL.get(tname, f"Q_{tname}")
            tank_flow[tname] = _resolve_flow(it, col, n_groups, series_cols, P,
                                             f"[Tank:{tname}] Q")
        else:
            tank_flow[tname] = it

    flow_consts = {
        "Q_ana": _const_of_item(q_ana, series_cols, P),
        "Q_ir": _const_of_item(q_ir, series_cols, P),
        "Q_r": _const_of_item(q_r, series_cols, P),
        "Q_air": _const_of_item(q_air, series_cols, P),
        "Q_carbon": _const_of_item(q_carbon, series_cols, P),
    }
    thru_fb = {"kind": "const",
               "value": flow_consts["Q_ana"] + flow_consts["Q_r"] + flow_consts["Q_ir"]}
    q_anox_item = tank_flow.get("anoxic", thru_fb)
    q_aer_item = tank_flow.get("aerobic", thru_fb)
    flow_consts["Q_anox"] = _const_of_item(q_anox_item, series_cols, P)
    flow_consts["Q_aer"] = _const_of_item(q_aer_item, series_cols, P)
    kla_item = tanks.get("aerobic", {}).get("kLa", {"kind": "const", "value": 0.0})
    kla_const = _const_of_item(kla_item, series_cols, P)

    partic = sh["partic_idx"]
    cod = sh["cod_idx"]

    # ================= a2 anaerobic ======================================
    core2 = _module_core(model, sh, "anaerobic")
    code_a2 = (
        header("a2anaerobic.py", f"anaerobic tank CSTR, V = {V['anaerobic']:g} m3 per group")
        + "\n" + core2
        + f"""
V_ANA = {V['anaerobic']!r}   # m3 per group


def rhs_anaerobic(C, t, Q_in, C_in):
    C = np.maximum(C, 0.0)  # clip negatives to keep Monod terms stable
    return Q_in / V_ANA * (C_in - C) + NU.T @ rates(C)


Y0_SELF = {_fmt_arr(y0['anaerobic'])}
C_INF_CONST = {cin_const_text}


def main():
    Q = {flow_consts['Q_ana']!r} + {flow_consts['Q_r']!r}  # influent + RAS
    sol = solve_ivp(lambda t, C: rhs_anaerobic(C, t, Q, C_INF_CONST),
                    (0.0, {ss_days!r}), Y0_SELF, method={method}, t_eval=[{ss_days!r}],
                    rtol={rtol!r}, atol={atol!r})
    assert sol.success, sol.message
    Css = np.maximum(sol.y[:, -1], 0.0)
    resid = np.abs(rhs_anaerobic(Css, {ss_days!r}, Q, C_INF_CONST)).max()
    print(f"a2anaerobic standalone steady: max|dC/dt| = {{resid:.3e}} mg/L/d "
          f"(tol={tol:g}) -> {{'OK' if resid < {tol!r} else 'NOT CONVERGED'}}")
    for j, c in enumerate(COMPONENTS):
        print(f"  {{c:<8}} {{Css[j]:>10.3f}}  {{UNITS[c]}}")


if __name__ == "__main__":
    main()
"""
    )

    # ================= a3 anoxic =========================================
    core3 = _module_core(model, sh, "anoxic")
    code_a3 = (
        header("a3anoxic.py", f"anoxic tank CSTR, V = {V['anoxic']:g} m3 per group, internal recycle + carbon dose")
        + "\n" + core3
        + f"""
V_ANOX = {V['anoxic']!r}   # m3 per group
S_DOSE = {s_dose!r}        # mg COD/L of carbon solution
IDX_S_A = COMPONENTS.index("S_A")


def rhs_anoxic(C, t, Q_ana_in, C_ana, Q_ir, C_aer, Q_carbon, Q_out):
    C = np.maximum(C, 0.0)
    dC = (Q_ana_in * C_ana + Q_ir * C_aer - Q_out * C) / V_ANOX + NU.T @ rates(C)
    dC[IDX_S_A] += Q_carbon * S_DOSE / V_ANOX  # external carbon as S_A
    return dC


Y0_SELF = {_fmt_arr(y0['anoxic'])}
C_INF_CONST = {cin_const_text}


def main():
    Q_ana_in = {flow_consts['Q_ana']!r} + {flow_consts['Q_r']!r}
    Q_ir = {flow_consts['Q_ir']!r}
    Q_carbon = {flow_consts['Q_carbon']!r}
    Q_out = {flow_consts['Q_anox']!r}
    sol = solve_ivp(lambda t, C: rhs_anoxic(C, t, Q_ana_in, C_INF_CONST, Q_ir,
                                            C_INF_CONST, Q_carbon, Q_out),
                    (0.0, {ss_days!r}), Y0_SELF, method={method}, t_eval=[{ss_days!r}],
                    rtol={rtol!r}, atol={atol!r})
    assert sol.success, sol.message
    Css = np.maximum(sol.y[:, -1], 0.0)
    resid = np.abs(rhs_anoxic(Css, {ss_days!r}, Q_ana_in, C_INF_CONST, Q_ir,
                              C_INF_CONST, Q_carbon, Q_out)).max()
    print(f"a3anoxic standalone steady: max|dC/dt| = {{resid:.3e}} mg/L/d "
          f"(tol={tol:g}) -> {{'OK' if resid < {tol!r} else 'NOT CONVERGED'}}")
    for j, c in enumerate(COMPONENTS):
        print(f"  {{c:<8}} {{Css[j]:>10.3f}}  {{UNITS[c]}}")


if __name__ == "__main__":
    main()
"""
    )

    # ================= a4 oxic ===========================================
    core4 = _module_core(model, sh, "aerobic")
    o2 = "S_O2" if "S_O2" in comps else "S_O"
    code_a4 = (
        header("a4oxic.py", f"aerobic (oxic) tank CSTR, V = {V['aerobic']:g} m3 per group, aeration")
        + "\n" + core4
        + f"""
V_AER = {V['aerobic']!r}   # m3 per group
S_O_SAT = {s_osat!r}       # mg/L
IO2 = COMPONENTS.index({o2!r})


def rhs_aerobic(C, t, Q_anox, C_anox, kla, Q_out):
    C = np.maximum(C, 0.0)
    dC = (Q_anox * C_anox - Q_out * C) / V_AER + NU.T @ rates(C)
    dC[IO2] += kla * (S_O_SAT - C[IO2])
    return dC


Y0_SELF = {_fmt_arr(y0['aerobic'])}
C_INF_CONST = {cin_const_text}


def main():
    Q_anox = {flow_consts['Q_anox']!r}
    Q_out = {flow_consts['Q_aer']!r}
    sol = solve_ivp(lambda t, C: rhs_aerobic(C, t, Q_anox, C_INF_CONST, {kla_const!r}, Q_out),
                    (0.0, {ss_days!r}), Y0_SELF, method={method}, t_eval=[{ss_days!r}],
                    rtol={rtol!r}, atol={atol!r})
    assert sol.success, sol.message
    Css = np.maximum(sol.y[:, -1], 0.0)
    resid = np.abs(rhs_aerobic(Css, {ss_days!r}, Q_anox, C_INF_CONST, {kla_const!r}, Q_out)).max()
    print(f"a4oxic standalone steady: max|dC/dt| = {{resid:.3e}} mg/L/d "
          f"(tol={tol:g}) -> {{'OK' if resid < {tol!r} else 'NOT CONVERGED'}}")
    for j, c in enumerate(COMPONENTS):
        print(f"  {{c:<8}} {{Css[j]:>10.3f}}  {{UNITS[c]}}")


if __name__ == "__main__":
    main()
"""
    )

    # ================= a5 oxic -> effluent ===============================
    core5 = _module_core(model, sh, None)
    code_a5 = (
        header("a5oxic2effluent.py", "static clarifier: aerobic outlet -> effluent + RAS")
        + "\n" + core5
        + f"""
F_PASS = {f_pass!r}    # particulate fraction passing to effluent
PARTIC_IDX = {partic!r}
COD_IDX = {cod!r}
KLA_SELF = {kla_const!r}
C_INF_CONST = {cin_const_text}


def clarifier(C_aer, Q_clar, Q_eff, Q_r):
    # static clarifier, mass-conserving split:
    #   soluble: both outlets get C_aer
    #   particulate: effluent gets F_PASS x C_aer; RAS takes the solids flux balance
    Ca = np.maximum(C_aer, 0.0)
    C_eff = Ca.copy()
    C_ras = Ca.copy()
    C_eff[PARTIC_IDX] *= F_PASS
    C_ras[PARTIC_IDX] = np.maximum(
        (Q_clar * Ca[PARTIC_IDX] - Q_eff * C_eff[PARTIC_IDX]) / max(Q_r, 1e-9), 0.0
    )
    return C_eff, C_ras


def total_cod(C):
    return float(sum(C[j] for j in COD_IDX))


Y0_SELF = {_fmt_arr(y0['aerobic'])}


def main():
    import a4oxic as m_aer
    Q_ana = {flow_consts['Q_ana']!r}; Q_r = {flow_consts['Q_r']!r}; Q_ir = {flow_consts['Q_ir']!r}
    Q_anox = {flow_consts['Q_anox']!r}; Q_aer = {flow_consts['Q_aer']!r}
    sol = solve_ivp(lambda t, C: m_aer.rhs_aerobic(C, t, Q_anox, C_INF_CONST, KLA_SELF, Q_aer),
                    (0.0, {ss_days!r}), Y0_SELF, method={method}, t_eval=[{ss_days!r}],
                    rtol={rtol!r}, atol={atol!r})
    assert sol.success, sol.message
    Car = np.maximum(sol.y[:, -1], 0.0)
    Q_clar = Q_aer - Q_ir
    Q_eff = Q_clar - Q_r
    C_eff, C_ras = clarifier(Car, Q_clar, Q_eff, Q_r)
    print("a5oxic2effluent standalone: clarifier split of steady aerobic outlet")
    print(f"  total COD  aer {{total_cod(Car):8.2f}} -> eff {{total_cod(C_eff):8.2f}} mg/L")
    print(f"  S_NH4        aer {{Car[COMPONENTS.index('S_NH4')]:8.2f}} "
          f"-> eff {{C_eff[COMPONENTS.index('S_NH4')]:8.2f}} mg/L")


if __name__ == "__main__":
    main()
"""
    )

    # ================= a1 influent -> anaerobic (driver) ===============
    ts_text = ""
    ser_text = ""
    if ts:
        ts_text = "\n".join(
            [f"TS_T = {_fmt_arr(ts['time'])}"]
            + [f"TS_{n} = {_fmt_arr(c['values'])}" for n, c in series_cols.items()]
        )
        ser_text = "\n".join(
            f"ser_{n} = _mk(TS_T, TS_{n}, {c['interp']!r})" for n, c in series_cols.items()
        )
        dynamic = "True"
        t_end = ts["time"][-1]
    else:
        dynamic = "False"
        t_end = ss_days

    def rt(item):
        return _runtime_of_item(item, series_cols)

    cin_dyn_rows = "\n".join(f"        {rt(inf[c])},  # {c}" for c in comp_list)
    y0_all = ", ".join(f"{v:.6g}" for vals in y0.values() for v in vals)

    code_a1 = (
        header("a1influent2anaerobic.py", "influent conversion + RAS mixing; coupled driver (main entry)")
        + "\n" + _module_core(model, sh, None)
        + f"""
N_C = len(COMPONENTS)
SS_DAYS = {ss_days!r}
DT = {dt!r}
T_END = {t_end!r}
DYNAMIC = {dynamic}
N_GROUPS = {n_groups!r}
TOL = {tol!r}

# --- time series (embedded from [TimeSeries]; absent in steady-only builds) --
{ts_text}


def _lin(T, V, t):
    return float(np.interp(t, T, V))


def _step(T, V, t):
    i = int(np.clip(np.searchsorted(T, t, side="right") - 1, 0, len(T) - 1))
    return float(V[i])


def _mk(T, V, kind):
    if kind == "linear":
        return lambda t: _lin(T, V, t)
    return lambda t: _step(T, V, t)


{ser_text}

# --- influent: 18-component conversion (expr/series; constants if no series) -
def c_influent(t):
    return np.array([
{cin_dyn_rows}
    ])


C_INF_CONST = {cin_const_text}
Q_EFF_CONST = {q_eff_const!r}   # plant total effluent flow from [Boundary:effluent]
Y0 = np.array([{y0_all}])  # [anaerobic | anoxic | aerobic] initial values


def q_ana(t):
    return {rt(q_ana)}


def q_ir(t):
    return {rt(q_ir)}


def q_r(t):
    return {rt(q_r)}


def q_air(t):
    return {rt(q_air)}


def q_carbon(t):
    return {rt(q_carbon)}


def q_anox(t):
    return {rt(q_anox_item)}


def q_aer(t):
    return {rt(q_aer_item)}


def kla(t):
    return {rt(kla_item)}


CONST = {{  # steady-phase constants (fallbacks / time means)
    "Q_ana": {flow_consts['Q_ana']!r}, "Q_ir": {flow_consts['Q_ir']!r},
    "Q_r": {flow_consts['Q_r']!r}, "Q_air": {flow_consts['Q_air']!r},
    "Q_carbon": {flow_consts['Q_carbon']!r}, "Q_anox": {flow_consts['Q_anox']!r},
    "Q_aer": {flow_consts['Q_aer']!r}, "kla": {kla_const!r},
}}


def coupled_rhs(tt, x, dyn):
    import a2anaerobic as m_ana
    import a3anoxic as m_anx
    import a4oxic as m_aer
    import a5oxic2effluent as m_eff

    Can, Cax, Car = x[:N_C], x[N_C:2 * N_C], x[2 * N_C:]
    if dyn:
        Q_ana = q_ana(tt); Q_ir = q_ir(tt); Q_r = q_r(tt); Q_carbon = q_carbon(tt)
        Q_anox = q_anox(tt); Q_aer = q_aer(tt)
        C_inf = c_influent(tt); kla_t = kla(tt)
    else:
        Q_ana = CONST["Q_ana"]; Q_ir = CONST["Q_ir"]; Q_r = CONST["Q_r"]
        Q_carbon = CONST["Q_carbon"]; Q_anox = CONST["Q_anox"]; Q_aer = CONST["Q_aer"]
        C_inf = C_INF_CONST; kla_t = CONST["kla"]
    Q_mix = Q_ana + Q_r
    Q_clar = Q_aer - Q_ir
    Q_eff = Q_clar - Q_r
    C_eff, C_ras = m_eff.clarifier(Car, Q_clar, Q_eff, Q_r)
    C_mix = (Q_ana * C_inf + Q_r * C_ras) / Q_mix
    d1 = m_ana.rhs_anaerobic(Can, tt, Q_mix, C_mix)
    d2 = m_anx.rhs_anoxic(Cax, tt, Q_mix, Can, Q_ir, Car, Q_carbon, Q_anox)
    d3 = m_aer.rhs_aerobic(Car, tt, Q_anox, Cax, kla_t, Q_aer)
    return np.concatenate([d1, d2, d3])


def report(sol, dyn):
    import a5oxic2effluent as m_eff
    N = N_C
    labels = ["anaerobic", "anoxic", "aerobic"]
    print()
    for k, lab in enumerate(labels):
        seg = sol.y[k * N:(k + 1) * N]
        print(f"--- {{lab}} tank ---")
        for j, c in enumerate(COMPONENTS):
            val = seg[j, -24:].mean() if dyn else seg[j, -1]
            print(f"  {{c:<8}} {{val:>10.3f}}  (min {{seg[j].min():9.3f}}, max {{seg[j].max():9.3f}})  {{UNITS[c]}}")
        print()
    Car = np.maximum(sol.y[2 * N:3 * N], 0.0)
    def _clar_flows(tt):
        if dyn:
            Q_aer = q_aer(tt); Q_ir = q_ir(tt); Q_r = q_r(tt)
        else:
            Q_aer = CONST["Q_aer"]; Q_ir = CONST["Q_ir"]; Q_r = CONST["Q_r"]
        Q_clar = Q_aer - Q_ir
        return Q_clar, Q_clar - Q_r, Q_r
    C_eff = np.array([m_eff.clarifier(Car[:, k], *_clar_flows(sol.t[k]))[0] for k in range(Car.shape[1])]).T
    Q_tot = Q_EFF_CONST  # plant total effluent flow from [Boundary:effluent]
    cod_in = m_eff.total_cod(C_INF_CONST) * Q_tot / 1000.0
    cod_eff = m_eff.total_cod(C_eff[:, -24:].mean(axis=1) if dyn else C_eff[:, -1]) * Q_tot / 1000.0
    nh4_j = COMPONENTS.index("S_NH4")
    print(f"plant total COD load: influent {{cod_in:8.1f}} -> effluent {{cod_eff:8.1f}} g/d "
          f"(removal {{100 * (1 - cod_eff / max(cod_in, 1e-9)):5.1f}} %)")
    print(f"plant effluent S_NH4 mean: {{float(C_eff[nh4_j].mean()):.3f}} mg/L")
    return C_eff


def main():
    import csv
    from pathlib import Path
    y0 = Y0.copy()
    print(f"[a1] steady warm-up {{SS_DAYS}} d (constant mean/fallback boundary) ...")
    sol_ss = solve_ivp(lambda t, x: coupled_rhs(t, x, False), (0.0, SS_DAYS), y0,
                       method={method}, t_eval=[SS_DAYS], rtol={rtol!r}, atol={atol!r})
    assert sol_ss.success, sol_ss.message
    y_ss = np.maximum(sol_ss.y[:, -1], 0.0)
    resid = float(np.abs(coupled_rhs(SS_DAYS, y_ss, False)).max())
    print(f"[a1] warm start: max|dC/dt| = {{resid:.3e}} mg/L/d (tol={{TOL:g}}) "
          f"-> {{'OK' if resid < TOL else 'NOT CONVERGED'}}")
    if not DYNAMIC:
        report(sol_ss, False)
        print("[a1] no [TimeSeries]: steady-only run finished.")
        return sol_ss, y_ss
    sol = solve_ivp(lambda t, x: coupled_rhs(t, x, True), (0.0, T_END), y_ss,
                    method={method}, t_eval=np.arange(0.0, T_END + 1e-9, DT),
                    rtol={rtol!r}, atol={atol!r})
    assert sol.success, sol.message
    print(f"[a1] dynamic run: {{sol.message}} ({{len(sol.t)}} points to {{T_END}} d)")
    C_eff = report(sol, True)
    out_csv = Path(__file__).with_name("a2o_dynamic.csv")
    with out_csv.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t", "Q_ana", "Q_ir", "Q_r", "Q_anox", "Q_aer"] +
                   [f"{{lab}}_{{c}}" for lab in ["ana", "anx", "aer"] for c in COMPONENTS] +
                   [f"eff_{{c}}" for c in COMPONENTS])
        for k, t in enumerate(sol.t):
            w.writerow([f"{{t:.4f}}", f"{{q_ana(t):.4f}}", f"{{q_ir(t):.4f}}",
                        f"{{q_r(t):.4f}}", f"{{q_anox(t):.4f}}", f"{{q_aer(t):.4f}}"] +
                       [f"{{v:.4f}}" for v in sol.y[:, k]] +
                       [f"{{v:.4f}}" for v in C_eff[:, k]])
    print(f"[a1] wrote {{out_csv.name}}")
    return sol, C_eff


if __name__ == "__main__":
    main()
"""
    )

    return {
        "a1influent2anaerobic.py": code_a1,
        "a2anaerobic.py": code_a2,
        "a3anoxic.py": code_a3,
        "a4oxic.py": code_a4,
        "a5oxic2effluent.py": code_a5,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="pywaterasm: .inwt -> standalone .py (single-tank or multi-tank A2O)")
    ap.add_argument("asm", help="path to the .inwt model definition file")
    ap.add_argument("-o", "--out", help="output .py path (default: generated_model/<stem>_tank.py)")
    args = ap.parse_args(argv)

    asm_path = Path(args.asm)
    model = parse_asm(asm_path)
    validate(model)

    n_r = len(model["rates"])
    n_c = len(model["components"])
    print(f"[pywaterasm] parsed  {asm_path}  ({n_c} components, {n_r} processes)")
    if model.get("tanks"):
        outdir = (Path(args.out) if args.out
                  else asm_path.parent.parent / "generated_model" / asm_path.stem)
        if outdir.suffix == ".py":
            outdir = outdir.parent
        outdir.mkdir(parents=True, exist_ok=True)
        files = generate_multi(model, asm_path.name)
        for fn in MULTI_FILENAMES:
            (outdir / fn).write_text(files[fn], encoding="utf-8")
        print(f"[pywaterasm] wrote   {outdir} / " + ", ".join(MULTI_FILENAMES))
    elif model.get("tank"):
        out = Path(args.out) if args.out else asm_path.parent.parent / "generated_model" / f"{asm_path.stem.lower()}_tank.py"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(generate_py(model, asm_path.name), encoding="utf-8")
        print(f"[pywaterasm] wrote   {out}")
    else:
        out = Path(args.out) if args.out else asm_path.parent.parent / "generated_model" / f"{asm_path.stem}.py"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(generate_class(model, asm_path.name), encoding="utf-8")
        print(f"[pywaterasm] wrote   {out}  (instantiable class)")


if __name__ == "__main__":
    main()
