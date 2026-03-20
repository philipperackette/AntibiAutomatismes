"""
Générateurs d'exercices pour le système Antibi.
v4 — Double mode corrigé (complet/succinct), corrections pédagogiques, corrigés détaillés, bug Distributivite5e corrigé,
     nouveaux générateurs (Intervalles/Valeur absolue, Fonctions de référence).
"""

import re
import random
import math
import datetime
import json
import os
import statistics
from abc import ABC, abstractmethod
from sympy import (
    Symbol, symbols, expand, factor, simplify, latex, sqrt, Rational,
    solve_univariate_inequality, Lt, Gt, Le, Ge, Interval, oo, S, nsimplify,
    pi, cos, sin, tan, Integer, Union, Abs, Mul, Add, Pow, UnevaluatedExpr,
    gcd as sympy_gcd
)
from sympy.geometry import Point, Line, Circle, intersection

x = Symbol('x')

REGISTRY = {}

def register(cls):
    REGISTRY[cls.id] = cls
    return cls

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers LaTeX
# ═══════════════════════════════════════════════════════════════════════════════

def pt(name):
    return f"\\ensuremath{{\\mathrm{{{name}}}}}"

def ptp(name):
    return f"\\ensuremath{{\\mathrm{{{name}}}^\\prime}}"

def pt_fig(name):
    return name

def vect(a, b):
    return f"\\overrightarrow{{{pt(a)}{pt(b)}}}"

def vect_u(name):
    return f"\\vec{{{name}}}"

def interval_from_solution(sol, ineq=None):
    if sol is S.EmptySet:
        return "\\emptyset"
    if sol == S.Reals or sol == Interval(-oo, oo):
        return "\\mathbb{R}"
    parts = []
    intervals = list(sol.args) if isinstance(sol, Union) else [sol]
    for intv in intervals:
        if isinstance(intv, Interval):
            a, b = intv.start, intv.end
            lo = intv.left_open
            ro = intv.right_open
            lb = "\\left]" if (a == -oo or lo) else "\\left["
            rb = "\\right[" if (b == oo or ro) else "\\right]"
            a_s = "-\\infty" if a == -oo else latex(a).replace('\\frac','\\dfrac')
            b_s = "+\\infty" if b == oo else latex(b).replace('\\frac','\\dfrac')
            parts.append(f"{lb} {a_s} \\,;\\, {b_s} {rb}")
        else:
            parts.append(latex(intv).replace('\\frac','\\dfrac'))
    return " \\cup ".join(parts)

def _plain(s: str) -> str:
    """Convert a LaTeX expression to readable plain text for QR codes."""
    s = str(s)
    # Fractions
    for _ in range(5):
        s2 = re.sub(r'\\d?frac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', s)
        if s2 == s: break
        s = s2
    # Racines
    s = re.sub(r'\\sqrt\{([^{}]*)\}', r'sqrt(\1)', s)
    # Délimiteurs \left / \right
    s = s.replace('\\left[', '[').replace('\\right]', ']')
    s = s.replace('\\left]', ']').replace('\\right[', '[')
    s = s.replace('\\left(', '(').replace('\\right)', ')')
    s = s.replace('\\left\\{', '{').replace('\\right\\}', '}')
    # Accolades échappées (ensembles solution : \{8\} → {8})
    s = s.replace('\\{', '{').replace('\\}', '}')
    # Infini
    s = s.replace('-\\infty', '-inf').replace('+\\infty', '+inf').replace('\\infty', 'inf')
    # Divers symboles
    s = s.replace('\\cup', ' U ').replace('\\,;\\,', ';').replace('\\;', ' ')
    s = s.replace('\\mathbb{R}', 'R').replace('\\emptyset', 'vide')
    s = s.replace('\\times', 'x').replace('\\cdot', '.')
    # Supprimer les commandes LaTeX restantes (\mot)
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    # Supprimer les backslashes résiduels (ex: \{ non traités, \8, etc.)
    s = s.replace('\\', '')
    # Nettoyer accolades et espaces
    s = s.replace('{', '').replace('}', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s



def _build_succinct_corrige(solutions):
    """Corrigé succinct : réponses seules en enumerate."""
    c = "\\begin{enumerate}\n"
    for s in solutions:
        c += f"\\item ${s}$\n"
    c += "\\end{enumerate}\n"
    return c


def _build_succinct_numbered(solutions):
    """Corrigé succinct numéroté pour exercices hors enumerate."""
    c = ""
    for i, s in enumerate(solutions, 1):
        c += f"\\textbf{{{i}.}} ${s}$\\par\\smallskip\n"
    return c


def _fmt_poly2(a2, a1, a0, var='x'):
    """Formate ax²+bx+c en LaTeX propre."""
    parts = []
    if a2 != 0:
        if a2 == 1: parts.append(f'{var}^2')
        elif a2 == -1: parts.append(f'-{var}^2')
        else: parts.append(f'{a2}{var}^2')
    if a1 != 0:
        if not parts:
            if a1 == 1: parts.append(var)
            elif a1 == -1: parts.append(f'-{var}')
            else: parts.append(f'{a1}{var}')
        else:
            if a1 == 1: parts.append(f' + {var}')
            elif a1 == -1: parts.append(f' - {var}')
            elif a1 > 0: parts.append(f' + {a1}{var}')
            else: parts.append(f' - {abs(a1)}{var}')
    if a0 != 0:
        if not parts:
            parts.append(str(a0))
        else:
            if a0 > 0: parts.append(f' + {a0}')
            else: parts.append(f' - {abs(a0)}')
    return ''.join(parts) if parts else '0'

def is_perfect_square(n):
    if n < 0: return False
    r = int(math.isqrt(n))
    return r * r == n

def _fmt_binomial_latex(a, b, var='x'):
    """Formate ax+b en LaTeX propre."""
    parts = []
    if a == 1: parts.append(var)
    elif a == -1: parts.append(f'-{var}')
    elif a != 0: parts.append(f'{a}{var}')
    if b > 0:
        parts.append(f' + {b}')
    elif b < 0:
        parts.append(f' - {abs(b)}')
    return ''.join(parts) if parts else '0'

def _fmt_coeff(c, var='x', first=False):
    """Formate un monôme c*var."""
    if c == 0: return ''
    sign = '+' if c > 0 else '-'
    ac = abs(c)
    if var:
        body = var if ac == 1 else f"{ac}{var}"
    else:
        body = str(ac)
    if first:
        return f"-{body}" if c < 0 else body
    return f" {sign} {body}"

# ═══════════════════════════════════════════════════════════════════════════════
# Modèle de difficulté cognitive (inspiré Training2ndeNum.py)
# ═══════════════════════════════════════════════════════════════════════════════

def _multiplication_weight(a, b):
    """Coût cognitif d'une multiplication a × b."""
    a, b = abs(int(a)), abs(int(b))
    if a > b: a, b = b, a
    if a <= 1: return 0.2
    if a == 2: return 0.4 if b <= 12 else 0.8
    if a == 5 or a == 10: return 0.3 if b <= 20 else 0.6
    if a <= 4 and b <= 12: return 0.7
    if a <= 9 and b <= 9: return 1.0 + 0.2 * max(0, min(a, b) - 5)
    if a <= 12 and b <= 12: return 1.5
    return 1.5 + 0.3 * (len(str(a)) + len(str(b)) - 2)

def _addition_weight(a, b):
    """Coût cognitif d'une addition/soustraction."""
    a, b = abs(int(a)), abs(int(b))
    if a <= 10 and b <= 10: return 0.3
    if a <= 20 and b <= 20: return 0.5
    return 0.5 + 0.2 * max(0, len(str(max(a, b))) - 1)

def _sign_cost(has_negative):
    return 0.5 if has_negative else 0.0

def _fraction_cost(num, den):
    from math import gcd
    g = gcd(abs(int(num)), abs(int(den)))
    cost = 0.8
    if g > 1 and g != abs(int(den)): cost += 0.4
    if abs(int(den)) > 10: cost += 0.3
    if int(num) < 0 or int(den) < 0: cost += 0.3
    return cost

def _sqrt_simplification_cost(n):
    """Coût de simplification de √n."""
    n = abs(int(n))
    if n <= 1: return 0.0
    if is_perfect_square(n): return 0.5
    cost = 0.0
    temp = n
    for p in [2, 3, 5, 7, 11, 13]:
        count = 0
        while temp % p == 0:
            temp //= p; count += 1
        if count >= 2: cost += 0.8
        if count >= 1: cost += 0.3
    if temp > 1: cost += 1.0
    return max(cost, 0.5)

# ═══════════════════════════════════════════════════════════════════════════════
# Base class
# ═══════════════════════════════════════════════════════════════════════════════

class ExerciseGenerator(ABC):
    id = ""; name = ""; niveau = ""; category = ""; description = ""
    has_figure = False; qr_in_corrige = False
    difficulty_config: dict = {}

    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':5,'min':1,'max':20}]

    def _resolve_difficulty(self, config: dict) -> dict:
        diff = config.get('difficulte')
        if not diff or diff == 'Mixte': return dict(config)
        presets = self.__class__.difficulty_config.get(diff, {})
        if not presets: return dict(config)
        result = dict(presets)
        result.update(config)
        return result

    @abstractmethod
    def generate(self, config: dict) -> dict:
        pass

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  5e                                                                          ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

@register
class RelatifsSomme5e(ExerciseGenerator):
    id="relatifs_somme_5e"; name="Sommes de relatifs"; niveau="5e"
    category="Nombres et calculs"; description="Additions et soustractions de nombres relatifs"
    difficulty_config = {
        'Facile':    {'nb_questions': 5, 'nb_termes': 2, 'valeur_max': 10, 'avec_soustractions': 'Additions seules'},
        'Moyen':     {'nb_questions': 8, 'nb_termes': 3, 'valeur_max': 20, 'avec_soustractions': 'Mélange'},
        'Difficile': {'nb_questions': 10, 'nb_termes': 4, 'valeur_max': 30, 'avec_soustractions': 'Soustractions seules'},
    }
    @staticmethod
    def get_config():
        return [
            {'key':'nb_questions','label':'Nombre de questions','type':'int','default':8,'min':2,'max':15},
            {'key':'nb_termes','label':'Termes par calcul','type':'int','default':3,'min':2,'max':6},
            {'key':'valeur_max','label':'Valeur absolue max','type':'int','default':20,'min':5,'max':50},
            {'key':'avec_soustractions','label':'Soustractions','type':'choice','default':'Mélange',
             'choices':['Additions seules','Soustractions seules','Mélange']},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',8); nb_t=config.get('nb_termes',3); vmax=config.get('valeur_max',20)
        mode_soustr = config.get('avec_soustractions', 'Mélange')
        enonces, solutions = [], []; total_diff = 0.0
        for q in range(n):
            termes = [random.randint(-vmax, vmax) for _ in range(nb_t)]
            while all(t >= 0 for t in termes):
                termes = [random.randint(-vmax, vmax) for _ in range(nb_t)]
            use_sub = (mode_soustr == 'Soustractions seules') or (mode_soustr == 'Mélange' and q >= n // 2)
            if mode_soustr == 'Additions seules': use_sub = False
            parts = []; total = 0; q_diff = 0.0
            for i, t in enumerate(termes):
                if i == 0:
                    parts.append(f"({t:+d})" if t != 0 else "(0)"); total += t
                    q_diff += _sign_cost(t < 0)
                elif use_sub and random.random() < 0.5:
                    neg_t = -t; parts.append(f" - ({neg_t:+d})"); total += t
                    q_diff += 1.2 + _sign_cost(neg_t < 0) + _addition_weight(abs(total-t), abs(t))
                else:
                    parts.append(f" + ({t:+d})"); total += t
                    q_diff += 0.3 + _sign_cost(t < 0) + _addition_weight(abs(total-t), abs(t))
            enonces.append(''.join(parts)); solutions.append(str(total)); total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Calculer les expressions suivantes.\n\\begin{enumerate}\n"
        for e in enonces: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for i,s in enumerate(solutions): corrige += f"\\item ${enonces[i]} = {s}$\n"
        corrige += "\\end{enumerate}\n"
        corrige_succinct = _build_succinct_corrige(solutions)
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':corrige_succinct,'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in solutions]}


@register
class PrioritesOperatoires5e(ExerciseGenerator):
    id="priorites_5e"; name="Priorités opératoires"; niveau="5e"
    category="Nombres et calculs"; description="Enchaînements d'opérations avec parenthèses"
    difficulty_config = {
        'Facile':    {'nb_questions': 4, 'avec_parentheses': 'Non'},
        'Moyen':     {'nb_questions': 6, 'avec_parentheses': 'Mélange'},
        'Difficile': {'nb_questions': 8, 'avec_parentheses': 'Oui'},
    }
    @staticmethod
    def get_config():
        return [
            {'key':'nb_questions','label':'Nombre de questions','type':'int','default':6,'min':2,'max':12},
            {'key':'avec_parentheses','label':'Avec parenthèses','type':'choice','default':'Oui','choices':['Oui','Non','Mélange']},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',6); parens=config.get('avec_parentheses','Oui')
        enonces, solutions, corriges = [], [], []; total_diff = 0.0
        for i in range(n):
            use_p = (parens=='Oui') or (parens=='Mélange' and i >= n//2)
            templates = [self._p1, self._p2] if use_p else [self._np1, self._np2]
            es, ed, q_diff, steps = random.choice(templates)()
            r = eval(es)
            if isinstance(r,float) and r==int(r): r=int(r)
            enonces.append(ed); solutions.append(str(r)); total_diff += q_diff
            corriges.append("$" + ed + "$\n\n" + "\n\n".join(steps) + f"\n\n$= {r}$")
        enonce = "\\noindent\\textbf{Exercice} -- Calculer en respectant les priorités opératoires.\n\\begin{enumerate}\n"
        for e in enonces: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for c in corriges: corrige += f"\\item {c}\n"
        corrige += "\\end{enumerate}\n"
        corrige_succinct = _build_succinct_corrige(solutions)
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':corrige_succinct,'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in solutions]}

    def _np1(self):
        a,b,c = random.randint(2,12),random.randint(2,9),random.randint(1,20)
        op = random.choice(['+','-'])
        diff = _multiplication_weight(a,b) + _addition_weight(a*b,c) + 1.0
        return f"{a}*{b}{op}{c}", f"{a} \\times {b} {op} {c}", diff, [f"$= {a*b} {op} {c}$"]
    def _np2(self):
        a,b,c,d = random.randint(1,10),random.randint(2,9),random.randint(1,10),random.randint(2,9)
        diff = _multiplication_weight(a,b) + _multiplication_weight(c,d) + _addition_weight(a*b,c*d) + 1.2
        return f"{a}*{b}+{c}*{d}", f"{a} \\times {b} + {c} \\times {d}", diff, [f"$= {a*b} + {c*d}$"]
    def _p1(self):
        a,b,c = random.randint(2,15),random.randint(1,10),random.randint(2,9)
        op = random.choice(['+','-'])
        inner = a+b if op=='+' else a-b
        diff = _addition_weight(a,b) + _multiplication_weight(inner,c) + 0.8
        return f"({a}{op}{b})*{c}", f"({a} {op} {b}) \\times {c}", diff, [f"$= {inner} \\times {c}$"]
    def _p2(self):
        a,b,c,d = random.randint(2,9),random.randint(1,10),random.randint(1,10),random.randint(2,9)
        o1,o2 = random.choice(['+','-']),random.choice(['+','-'])
        inner = b+c if o1=='+' else b-c
        diff = _addition_weight(b,c) + _multiplication_weight(a,inner) + _addition_weight(a*inner,d) + 1.0
        return f"{a}*({b}{o1}{c}){o2}{d}", f"{a} \\times ({b} {o1} {c}) {o2} {d}", diff, [f"$= {a} \\times {inner} {o2} {d}$", f"$= {a*inner} {o2} {d}$"]


# ═══════════════════════════════════════════════════════════════════════════════
# Distributivité 5e — BUG FIX : construction manuelle, pas d'auto-expand SymPy
# ═══════════════════════════════════════════════════════════════════════════════

@register
class Distributivite5e(ExerciseGenerator):
    id="distributivite_5e"; name="Distributivité simple"; niveau="5e"
    category="Nombres et calculs"; description="Développer k(a+b) et factoriser ka+kb"
    difficulty_config = {
        'Facile':    {'nb_developper': 3, 'nb_factoriser': 0},
        'Moyen':     {'nb_developper': 4, 'nb_factoriser': 4},
        'Difficile': {'nb_developper': 4, 'nb_factoriser': 6},
    }
    @staticmethod
    def get_config():
        return [
            {'key':'nb_developper','label':'Questions développer','type':'int','default':4,'min':0,'max':10},
            {'key':'nb_factoriser','label':'Questions factoriser','type':'int','default':4,'min':0,'max':10},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n_dev=config.get('nb_developper',4); n_fac=config.get('nb_factoriser',4)
        qr_dist=[]; enonce=""; corrige=""; total_diff=0.0
        nz = [i for i in range(-9,10) if i!=0]

        if n_dev>0:
            enonce += "\\noindent\\textbf{Exercice} -- Développer les expressions suivantes.\n\\begin{enumerate}\n"
            ci = "\\begin{enumerate}\n"
            for _ in range(n_dev):
                k,a,b = random.choice(nz),random.choice(nz),random.choice(nz)
                # ── Construction MANUELLE (pas de SymPy pour l'énoncé) ──
                inner = _fmt_binomial_latex(a, b)
                if k == 1: enonce_str = f"({inner})"
                elif k == -1: enonce_str = f"-({inner})"
                else: enonce_str = f"{k}({inner})"
                # Développer manuellement
                ka, kb = k*a, k*b
                dev_str = _fmt_binomial_latex(ka, kb)
                enonce += f"\\item ${enonce_str}$\n"
                # Corrigé avec étapes
                ci += f"\\item ${enonce_str} = {dev_str}$\n"
                qr_dist.append(dev_str)
                # Difficulté cognitive
                q_diff = 1.0 + _multiplication_weight(k,a) + _multiplication_weight(k,b)
                q_diff += _sign_cost(k<0) + _sign_cost(a<0) + _sign_cost(b<0)
                if k<0 and a<0: q_diff += 0.8
                if k<0 and b<0: q_diff += 0.8
                total_diff += q_diff
            enonce += "\\end{enumerate}\n"; ci += "\\end{enumerate}\n"; corrige += ci

        if n_fac>0:
            enonce += "\\noindent\\textbf{Exercice} -- Factoriser les expressions suivantes.\n\\begin{enumerate}\n"
            ci = "\\begin{enumerate}\n"
            for _ in range(n_fac):
                k=random.randint(2,9)
                a=random.choice([i for i in nz if abs(i)>=2])
                b=random.choice([i for i in nz if abs(i)>=2])
                ka, kb = k*a, k*b
                dev_str = _fmt_binomial_latex(ka, kb)
                inner = _fmt_binomial_latex(a, b)
                fac_str = f"{k}({inner})"
                enonce += f"\\item ${dev_str}$\n"
                ci += f"\\item ${dev_str} = {fac_str}$\n"
                qr_dist.append(fac_str)
                q_diff = 1.5 + 0.5*(1 if abs(ka)>12 else 0) + 0.5*(1 if abs(kb)>12 else 0)
                q_diff += _sign_cost(ka<0) + _sign_cost(kb<0)
                total_diff += q_diff
            enonce += "\\end{enumerate}\n"; ci += "\\end{enumerate}\n"; corrige += ci

        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':corrige,'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in qr_dist]}


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  3e                                                                          ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

@register
class Reduction3e(ExerciseGenerator):
    id="reduction_3e"; name="Réduction d'expressions"; niveau="3e"
    category="Calcul littéral"; description="Réduire ±(ax+b) ± (cx+d)"
    difficulty_config = {'Facile':{'nb_questions':3},'Moyen':{'nb_questions':5},'Difficile':{'nb_questions':8}}
    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':5,'min':2,'max':10}]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',5); et,st=[],[]; total_diff=0.0
        for _ in range(n):
            a,b = random.choice([1,-1])*random.randint(2,9), random.choice([1,-1])*random.randint(2,9)
            c,d = random.choice([1,-1])*random.randint(2,9), random.choice([1,-1])*random.randint(2,9)
            s1,s2 = random.choice([1,-1]),random.choice([1,-1])
            expr = s1*(a*x+b)+s2*(c*x+d); result = expand(expr)
            e0=str(a*x+b).replace('*',''); e1=str(c*x+d).replace('*','')
            disp = ('-' if s1==-1 else '')+'('+e0+')'+('+' if s2==1 else '-')+'('+e1+')'
            et.append(disp); st.append(str(result).replace('**','^').replace('*',''))
            q_diff = 1.0
            if s1==-1: q_diff += 1.5
            if s2==-1: q_diff += 1.5
            q_diff += _addition_weight(abs(s1*a), abs(s2*c)) + _addition_weight(abs(s1*b), abs(s2*d))
            q_diff += 0.3 * sum(1 for v in [a,b,c,d] if v<0)
            total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Réduire les expressions suivantes.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for i,s in enumerate(st): corrige += f"\\item ${et[i]} = {s}$\n"
        corrige += "\\end{enumerate}\n"
        corrige_succinct = _build_succinct_corrige(st)
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':corrige_succinct,'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


@register
class Developpement3e(ExerciseGenerator):
    id="developpement_3e"; name="Développement"; niveau="3e"
    category="Calcul littéral"; description="Développer et réduire (ax+b)(cx+d)"
    difficulty_config = {'Facile':{'nb_questions':4,'nb_simples':4},'Moyen':{'nb_questions':6,'nb_simples':2},'Difficile':{'nb_questions':8,'nb_simples':0}}
    @staticmethod
    def get_config():
        return [
            {'key':'nb_questions','label':'Nombre de questions','type':'int','default':6,'min':2,'max':10},
            {'key':'nb_simples','label':'dont simples (b=0)','type':'int','default':2,'min':0,'max':4},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',6); ns=min(config.get('nb_simples',2),n)
        et,st=[],[]; total_diff=0.0
        for i in range(n):
            a=random.choice([1,-1])*random.randint(2,9)
            b=0 if i<ns else random.choice([1,-1])*random.randint(2,9)
            c=random.choice([1,-1])*random.randint(2,9); d=random.choice([1,-1])*random.randint(2,9)
            expr=(a*x+b)*(c*x+d); result=expand(expr)
            et.append(str(expr).replace('**','^').replace('*',''))
            st.append(str(result).replace('**','^').replace('*',''))
            q_diff = 2.0 + _multiplication_weight(a,c) + _multiplication_weight(a,d)
            if b != 0:
                q_diff += _multiplication_weight(b,c) + _multiplication_weight(b,d) + _addition_weight(abs(a*d), abs(b*c)) + 1.0
            q_diff += 0.4 * sum(1 for v in [a,b,c,d] if v<0)
            total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Développer et réduire.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for i,s in enumerate(st): corrige += f"\\item ${et[i]} = {s}$\n"
        corrige += "\\end{enumerate}\n"
        corrige_succinct = _build_succinct_corrige(st)
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':corrige_succinct,'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


@register
class Equations3e(ExerciseGenerator):
    id="equations_3e"; name="Équations du 1er degré"; niveau="3e"
    category="Calcul littéral"; description="Résoudre ax+b = cx+d (niveaux progressifs)"
    difficulty_config = {'Facile':{'nb_questions':4,'niveau':'Simple (ax=b)'},'Moyen':{'nb_questions':5,'niveau':'Progressif'},'Difficile':{'nb_questions':6,'niveau':'Complet (ax+b=cx+d)'}}
    @staticmethod
    def get_config():
        return [
            {'key':'nb_questions','label':'Nombre de questions','type':'int','default':5,'min':2,'max':10},
            {'key':'niveau','label':'Difficulté','type':'choice','default':'Progressif',
             'choices':['Simple (ax=b)','Moyen (ax+b=c)','Complet (ax+b=cx+d)','Progressif']},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',5); niveau=config.get('niveau','Progressif')
        et,st,corriges=[],[],[]; total_diff=0.0
        for i in range(n):
            if niveau=='Progressif':
                lev = 'simple' if i<n//3 else ('moyen' if i<2*n//3 else 'complet')
            else:
                lev = 'simple' if niveau.startswith('Simple') else ('moyen' if niveau.startswith('Moyen') else 'complet')
            if lev=='simple':
                a=random.choice([j for j in range(-9,10) if j not in [0,1]]); bv=random.choice([j for j in range(-20,21) if j!=0])
                eq=f"{a}x = {bv}"; sol=Rational(bv,a); q_diff=1.5+_fraction_cost(bv,a)
                sol_l=latex(sol).replace('\\frac','\\dfrac')
                detail=f"${eq}$\n\n$\\Leftrightarrow x = \\dfrac{{{bv}}}{{{a}}} = {sol_l}$"
            elif lev=='moyen':
                a=random.choice([j for j in range(-9,10) if j not in [0,1]])
                bv=random.choice([1,-1])*random.randint(1,15); cv=random.choice([1,-1])*random.randint(1,15)
                eq=f"{str(a*x+bv).replace('*','')} = {cv}"; sol=Rational(cv-bv,a)
                sol_l=latex(sol).replace('\\frac','\\dfrac'); rhs=cv-bv
                detail=(f"${eq}$\n\n$\\Leftrightarrow {a}x = {cv} - ({bv}) = {rhs}$\n\n$\\Leftrightarrow x = \\dfrac{{{rhs}}}{{{a}}} = {sol_l}$")
                q_diff=3.0+_addition_weight(abs(cv),abs(bv))+_fraction_cost(rhs,a)
            else:
                while True:
                    a=random.choice([1,-1])*random.randint(2,9); bv=random.choice([1,-1])*random.randint(1,12)
                    cv=random.choice([1,-1])*random.randint(2,9); dv=random.choice([1,-1])*random.randint(1,12)
                    if a!=cv: break
                eq=f"{str(a*x+bv).replace('*','')} = {str(cv*x+dv).replace('*','')}"; sol=Rational(dv-bv,a-cv)
                sol_l=latex(sol).replace('\\frac','\\dfrac')
                cd=a-cv; cn=dv-bv
                detail=(f"${eq}$\n\n$\\Leftrightarrow {cd}x = {cn}$\n\n$\\Leftrightarrow x = \\dfrac{{{cn}}}{{{cd}}} = {sol_l}$")
                q_diff=5.0+_addition_weight(abs(a),abs(cv))+_addition_weight(abs(dv),abs(bv))+_fraction_cost(cn,cd)
                q_diff+=0.5*sum(1 for v in [a,bv,cv,dv] if v<0)
            sol_set = f"S = \\left\\{{{sol_l}\\right\\}}"
            detail += f"\n\nL'ensemble des solutions est ${sol_set}$."
            et.append(eq); st.append(sol_set); corriges.append(detail)
            total_diff += q_diff
        sol_only = [s for s in st]  # S={...} strings
        enonce = "\\noindent\\textbf{Exercice} -- Résoudre les équations suivantes.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for d in corriges: corrige += f"\\item {d}\n\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige(st),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


@register
class EquationsProduit3e(ExerciseGenerator):
    id="equations_produit_3e"; name="Équations produit"; niveau="3e"
    category="Calcul littéral"; description="Résoudre (ax+b)(cx+d) = 0"
    difficulty_config = {'Facile':{'nb_questions':3},'Moyen':{'nb_questions':4},'Difficile':{'nb_questions':6}}
    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':4,'min':2,'max':8}]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',4); et,st,corriges=[],[],[]; total_diff=0.0
        for _ in range(n):
            a=random.choice([1,-1])*random.randint(1,7); b=random.choice([1,-1])*random.randint(1,9)
            c=random.choice([1,-1])*random.randint(1,7); d=random.choice([1,-1])*random.randint(1,9)
            lhs=(a*x+b)*(c*x+d); s1=Rational(-b,a); s2=Rational(-d,c)
            et.append(f"{str(lhs).replace('**','^').replace('*','')} = 0")
            if s1 == s2:
                s1l=latex(s1).replace('\\frac','\\dfrac')
                st.append(f"S = \\left\\{{{s1l}\\right\\}}")
            else:
                ordered = sorted([s1, s2])
                o1=latex(ordered[0]).replace('\\frac','\\dfrac')
                o2=latex(ordered[1]).replace('\\frac','\\dfrac')
                st.append(f"S = \\left\\{{{o1} \\; ; \\; {o2}\\right\\}}")
            s1l=latex(s1).replace('\\frac','\\dfrac'); s2l=latex(s2).replace('\\frac','\\dfrac')
            fac1=str(a*x+b).replace('*',''); fac2=str(c*x+d).replace('*','')
            corriges.append(
                f"Un produit est nul si et seulement si l'un des facteurs est nul.\n\n"
                f"$\\bullet\\ {fac1} = 0 \\Leftrightarrow x = {s1l}$\n\n"
                f"$\\bullet\\ {fac2} = 0 \\Leftrightarrow x = {s2l}$\n\n"
                f"Donc ${st[-1]}$")
            q_diff = 2.0 + _fraction_cost(-b,a) + _fraction_cost(-d,c)
            q_diff += 0.3 * sum(1 for v in [a,b,c,d] if v<0)
            total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Résoudre les équations suivantes.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for d in corriges: corrige += f"\\item {d}\n\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige(st),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}

# ═══════════════════════════════════════════════════════════════════════════════
# Pythagore 3e — corrigé déjà détaillé, ajout difficulté cognitive
# ═══════════════════════════════════════════════════════════════════════════════

@register
class Pythagore3e(ExerciseGenerator):
    id="pythagore_3e"; name="Théorème de Pythagore"; niveau="3e"
    category="Géométrie"; description="Calculer un côté (hypoténuse OU côté), unités homogènes"
    has_figure = True
    difficulty_config = {'Facile':{'nb_questions':2},'Moyen':{'nb_questions':4},'Difficile':{'nb_questions':6}}
    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':4,'min':1,'max':8}]

    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',4)
        triplets=[(3,4,5),(5,12,13),(8,15,17),(7,24,25),(6,8,10),(9,12,15)]
        lettres=[('A','B','C'),('D','E','F'),('M','N','P'),('R','S','T'),('K','L','H'),('U','V','W')]
        enonces_tex, solutions_tex, qr_final = [], [], []
        total_diff = 0.0
        for i in range(n):
            L=lettres[i%len(lettres)]; rd=L[1]
            mode = i%4
            if mode<=1:
                trip=random.choice(triplets); k=random.randint(1,3)
                ca,cb,hyp = trip[0]*k, trip[1]*k, trip[2]*k
                if mode==0:
                    d1=f"{pt(L[0])}{pt(L[1])} = {ca}~\\text{{cm}}"
                    d2=f"{pt(L[1])}{pt(L[2])} = {cb}~\\text{{cm}}"
                    ch=f"{pt(L[0])}{pt(L[2])}"
                    sol = (f"D'après le théorème de Pythagore dans le triangle "
                           f"{pt(L[0])}{pt(L[1])}{pt(L[2])} rectangle en {pt(rd)} :\n\n"
                           f"${ch}^2 = {pt(L[0])}{pt(L[1])}^2 + {pt(L[1])}{pt(L[2])}^2$\n\n"
                           f"${ch}^2 = ({ca}~\\text{{cm}})^2 + ({cb}~\\text{{cm}})^2 = {ca**2}~\\text{{cm}}^2 + {cb**2}~\\text{{cm}}^2 = {hyp**2}~\\text{{cm}}^2$\n\n"
                           f"Donc ${ch} = \\sqrt{{{hyp**2}}}~\\text{{cm}} = {hyp}~\\text{{cm}}$")
                    fig_a, fig_b = ca, cb
                    q_diff = 2.0 + _multiplication_weight(ca,ca) + _multiplication_weight(cb,cb) + _addition_weight(ca**2,cb**2) + 1.0
                else:
                    d1=f"{pt(L[0])}{pt(L[2])} = {hyp}~\\text{{cm}}"
                    d2=f"{pt(L[0])}{pt(L[1])} = {ca}~\\text{{cm}}"
                    ch=f"{pt(L[1])}{pt(L[2])}"
                    sol = (f"D'après le théorème de Pythagore dans le triangle "
                           f"{pt(L[0])}{pt(L[1])}{pt(L[2])} rectangle en {pt(rd)} :\n\n"
                           f"${pt(L[0])}{pt(L[2])}^2 = {pt(L[0])}{pt(L[1])}^2 + {ch}^2$\n\n"
                           f"Donc ${ch}^2 = {pt(L[0])}{pt(L[2])}^2 - {pt(L[0])}{pt(L[1])}^2 "
                           f"= ({hyp}~\\text{{cm}})^2 - ({ca}~\\text{{cm}})^2 = {hyp**2}~\\text{{cm}}^2 - {ca**2}~\\text{{cm}}^2 = {cb**2}~\\text{{cm}}^2$\n\n"
                           f"Donc ${ch} = \\sqrt{{{cb**2}}}~\\text{{cm}} = {cb}~\\text{{cm}}$")
                    fig_a, fig_b = ca, cb
                    q_diff = 3.0 + _multiplication_weight(hyp,hyp) + _multiplication_weight(ca,ca) + _addition_weight(hyp**2,ca**2) + 1.5
            else:
                c1=random.randint(2,8); c2=random.randint(c1+1,12)
                if mode==2:
                    sq=c1**2+c2**2
                    d1=f"{pt(L[0])}{pt(L[1])} = {c1}~\\text{{cm}}"
                    d2=f"{pt(L[1])}{pt(L[2])} = {c2}~\\text{{cm}}"
                    ch=f"{pt(L[0])}{pt(L[2])}"
                    simpl=simplify(sqrt(sq)); sl=latex(simpl)
                    sol = (f"D'après le théorème de Pythagore :\n\n"
                           f"${ch}^2 = ({c1}~\\text{{cm}})^2 + ({c2}~\\text{{cm}})^2 = {c1**2}~\\text{{cm}}^2 + {c2**2}~\\text{{cm}}^2 = {sq}~\\text{{cm}}^2$\n\n"
                           f"Donc ${ch} = \\sqrt{{{sq}}}$")
                    if simpl != sqrt(sq): sol += f"$ = {sl}$ cm"
                    else: sol += " cm"
                    fig_a, fig_b = c1, c2
                    q_diff = 3.5 + _multiplication_weight(c1,c1) + _multiplication_weight(c2,c2) + _sqrt_simplification_cost(sq)
                    if not is_perfect_square(sq): q_diff += 1.5
                else:
                    sq=c2**2-c1**2
                    d1=f"{pt(L[0])}{pt(L[2])} = {c2}~\\text{{cm}}"
                    d2=f"{pt(L[0])}{pt(L[1])} = {c1}~\\text{{cm}}"
                    ch=f"{pt(L[1])}{pt(L[2])}"
                    simpl=simplify(sqrt(sq)); sl=latex(simpl)
                    sol = (f"D'après le théorème de Pythagore :\n\n"
                           f"${pt(L[0])}{pt(L[2])}^2 = {pt(L[0])}{pt(L[1])}^2 + {ch}^2$\n\n"
                           f"Donc ${ch}^2 = ({c2}~\\text{{cm}})^2 - ({c1}~\\text{{cm}})^2 = {c2**2}~\\text{{cm}}^2 - {c1**2}~\\text{{cm}}^2 = {sq}~\\text{{cm}}^2$\n\n"
                           f"Donc ${ch} = \\sqrt{{{sq}}}$")
                    if simpl != sqrt(sq): sol += f"$ = {sl}$ cm"
                    else: sol += " cm"
                    fig_a, fig_b = c1, c2
                    q_diff = 4.5 + _multiplication_weight(c2,c2) + _multiplication_weight(c1,c1) + _sqrt_simplification_cost(sq)
                    if not is_perfect_square(sq): q_diff += 1.5
            total_diff += q_diff
            # Figure TikZ
            max_dim = max(fig_a, fig_b)
            scale_a = max(2, 6 * fig_a / max_dim)
            scale_b = max(2, 6 * fig_b / max_dim)
            if fig_a >= fig_b:
                fig = ("\\begin{tikzpicture}[scale=0.35]\n"
                       f"\\draw (0,0) node[left]{{{pt_fig(L[0])}}} -- ({scale_a:.2f},0) node[right]{{{pt_fig(L[1])}}} "
                       f"-- ({scale_a:.2f},{scale_b:.2f}) node[above]{{{pt_fig(L[2])}}} -- cycle;\n"
                       f"\\draw ({scale_a - 0.4:.2f},0) rectangle ({scale_a:.2f},0.4);\n"
                       "\\end{tikzpicture}")
            else:
                fig = ("\\begin{tikzpicture}[scale=0.35]\n"
                       f"\\draw (0,{scale_a:.2f}) node[left]{{{pt_fig(L[0])}}} -- (0,0) node[below left]{{{pt_fig(L[1])}}} "
                       f"-- ({scale_b:.2f},0) node[right]{{{pt_fig(L[2])}}} -- cycle;\n"
                       f"\\draw (0,0) rectangle (0.4,0.4);\n"
                       "\\end{tikzpicture}")
            eq = (f"Le triangle {pt(L[0])}{pt(L[1])}{pt(L[2])} est rectangle en {pt(rd)}. "
                  f"On donne ${d1}$ et ${d2}$.\n\n"
                  f"\\begin{{center}}\n{fig}\n\\end{{center}}\n\n"
                  f"Calculer la valeur exacte de ${ch}$.\n")
            _last = [l.strip() for l in sol.split('\n') if l.strip()]
            _ans_raw = _last[-1] if _last else '?'
            _m = re.search(r'=\s*(\S+)\s*cm', _ans_raw)
            qr_final.append(_plain(_m.group(1) + ' cm') if _m else _plain(_ans_raw))
            enonces_tex.append(eq); solutions_tex.append(sol)
        enonce = "\\noindent\\textbf{Exercice} -- Théorème de Pythagore.\n\\medskip\n"
        for i,e in enumerate(enonces_tex): enonce += f"\n\\noindent\\textbf{{{i+1}.}} {e}\n\\medskip\n"
        corrige = ""
        for i,s in enumerate(solutions_tex): corrige += f"\\textbf{{{i+1}.}} {s}\n\n\\medskip\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_numbered(qr_final),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':qr_final}


# ═══════════════════════════════════════════════════════════════════════════════
# Thalès 3e — conservé quasi identique, ajout difficulte_raw
# ═══════════════════════════════════════════════════════════════════════════════

@register
class Thales3e(ExerciseGenerator):
    id="thales_3e"; name="Théorème de Thalès"; niveau="3e"
    category="Géométrie"; description="Configurations de Thalès, solutions en QR code"
    has_figure=True; qr_in_corrige=True
    difficulty_config = {'Facile':{'nb_questions':2},'Moyen':{'nb_questions':4},'Difficile':{'nb_questions':6}}
    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':4,'min':1,'max':6}]

    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',4); enonces_all=""; qr_parts=[]; corrige_parts=[]; total_diff=0.0
        for q in range(n):
            papillon = (q >= n//2)
            ab=random.randint(2,5); ac=ab+random.randint(2,4)
            abp=random.choice([i for i in range(1,6) if i!=ab])
            acp=Rational(ac*abp,ab)
            chaines=[f"{pt('A')}{pt('B')} = {ab}", f"{pt('A')}{pt('C')} = {ac}", f"{pt('A')}{ptp('B')} = {abp}"]
            random.shuffle(chaines); donnees=", ".join(chaines)
            div=random.choice([6,5,4]); A=Point(0,0); B=Point(ab,0)
            C=Point(-ac if papillon else ac, 0)
            Bd=B.rotate(pi/div); ABd=Line(A,Bd); cc=Circle(A,abp)
            inters=intersection(cc,ABd); Bp=max(inters,key=lambda p:float(p[0].evalf()))
            Cp = -(Rational(ac,ab))*Bp if papillon else (Rational(ac,ab))*Bp

            def sf(p): return f"({float(p[0].evalf()):.3f},{float(p[1].evalf()):.3f})"
            def lb(p,dx,dy): return f"({float(p[0].evalf())+dx:.3f},{float(p[1].evalf())+dy:.3f})"

            fig = "\\begin{tikzpicture}[scale=0.8]\n"
            for pa,pb in [(A,B),(B,C),(A,Bp),(Bp,Cp),(B,Bp),(C,Cp)]:
                fig += f"\\draw [thick] {sf(pa)}--{sf(pb)};\n"
            if papillon:
                fig += f"\\draw {lb(A,0.1,-0.5)} node {{{pt_fig('A')}}};\n"
                fig += f"\\draw {lb(B,0.3,0)} node {{{pt_fig('B')}}};\n"
                fig += f"\\draw {lb(C,-0.5,0)} node {{{pt_fig('C')}}};\n"
                fig += f"\\draw {lb(Bp,0.3,0.2)} node {{{pt_fig('B')}'}};\n"
                fig += f"\\draw {lb(Cp,-0.5,-0.2)} node {{{pt_fig('C')}'}};\n"
            else:
                fig += f"\\draw {lb(A,-0.4,-0.3)} node {{{pt_fig('A')}}};\n"
                fig += f"\\draw {lb(B,0,-0.5)} node {{{pt_fig('B')}}};\n"
                fig += f"\\draw {lb(C,0,-0.5)} node {{{pt_fig('C')}}};\n"
                fig += f"\\draw {lb(Bp,-0.4,0.3)} node {{{pt_fig('B')}'}};\n"
                fig += f"\\draw {lb(Cp,0.3,0.3)} node {{{pt_fig('C')}'}};\n"
            fig += "\\end{tikzpicture}\n"

            eq = (f"\\noindent\\textbf{{{q+1}.}} Les droites ({pt('B')}{ptp('B')}) et ({pt('C')}{ptp('C')}) sont parallèles. {donnees}.\n\n"
                  f"\\begin{{center}}\n{fig}\\end{{center}}\n"
                  f"Déterminer en justifiant la valeur exacte de {pt('A')}{ptp('C')}.")
            if q < n - 1: eq += "\n\n\\bigskip\n"
            else: eq += "\n"
            enonces_all += eq

            acp_latex = latex(acp).replace('\\frac', '\\dfrac')
            qr_parts.append(f"E{q+1} : AC'={acp}")
            corrige_parts.append(
                f"\\textbf{{{q+1}.}} Comme ({pt('B')}{ptp('B')}) et ({pt('C')}{ptp('C')}) sont parallèles, d'après le théorème de Thalès : "
                f"\\[\\dfrac{{{pt('A')}{ptp('C')}}}{{{pt('A')}{pt('C')}}}=\\dfrac{{{pt('A')}{ptp('B')}}}{{{pt('A')}{pt('B')}}}=\\dfrac{{{abp}}}{{{ab}}}.\\]"
                f"Donc \\[{pt('A')}{ptp('C')}={ac}\\times\\dfrac{{{abp}}}{{{ab}}}={acp_latex}.\\]\\medskip\n")

            # Difficulté cognitive : identifier la config, poser le ratio, produit en croix
            q_diff = 3.0  # Méthode (identifier Thalès + poser les rapports)
            q_diff += _multiplication_weight(ac, abp)
            q_diff += _fraction_cost(ac * abp, ab)
            if papillon: q_diff += 1.0  # Configuration papillon = plus dur à lire
            total_diff += q_diff

        enonce = "\\noindent\\textbf{Exercice} -- Théorème de Thalès\n\n\\medskip\n" + enonces_all
        corrige = "".join(corrige_parts)
        qr_data = " ; ".join(qr_parts) + f" ; Time : {datetime.datetime.now()}"
        qr_answers = [p.split('=',1)[1] for p in qr_parts if '=' in p]
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_numbered([p.split('=',1)[1] for p in qr_parts if '=' in p]),'qr_data':qr_data,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':qr_answers}

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  2nde                                                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

@register
class Puissances2nde(ExerciseGenerator):
    id="puissances_2nde"; name="Puissances de 10"; niveau="2nde"
    category="Nombres et calculs"; description="Unique puissance de 10"
    difficulty_config = {'Facile':{'nb_questions':3},'Moyen':{'nb_questions':4},'Difficile':{'nb_questions':6}}
    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':4,'min':2,'max':8}]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',4); et,st=[],[]; total_diff=0.0
        for i in range(n):
            if i%2==0:
                a,b,c=random.randint(-3,3),random.randint(-3,3),random.randint(1,4)
                et.append(f"\\dfrac{{10^{{{a}}} \\times 10^{{{b}}}}}{{10^{{{c}}}}}"); st.append(f"10^{{{a+b-c}}}")
                q_diff = 1.5 + _addition_weight(abs(a),abs(b)) + _addition_weight(abs(a+b),abs(c))
                if a<0: q_diff+=0.5
                if b<0: q_diff+=0.5
            else:
                a,b,k,c=random.randint(-3,3),random.randint(1,3),random.randint(2,3),random.randint(1,4)
                et.append(f"\\dfrac{{10^{{{a}}} \\times (10^{{{b}}})^{{{k}}}}}{{10^{{{c}}}}}"); st.append(f"10^{{{a+b*k-c}}}")
                q_diff = 2.5 + _multiplication_weight(b,k) + _addition_weight(abs(a),abs(b*k)) + _addition_weight(abs(a+b*k),abs(c))
                if a<0: q_diff+=0.5
            total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Écrire sous la forme d'une unique puissance de 10.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for i,s in enumerate(st):
            # Corrigé avec étape intermédiaire
            corrige += f"\\item ${et[i]} = {s}$\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige(st),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


@register
class Inequations2nde(ExerciseGenerator):
    id="inequations_2nde"; name="Inéquations du 1er degré"; niveau="2nde"
    category="Nombres et calculs"; description="Solutions en intervalles (normes françaises)"
    difficulty_config = {'Facile':{'nb_questions':4,'niveau_max':2},'Moyen':{'nb_questions':6,'niveau_max':3},'Difficile':{'nb_questions':8,'niveau_max':4}}
    @staticmethod
    def get_config():
        return [
            {'key':'nb_questions','label':'Nombre de questions','type':'int','default':6,'min':2,'max':12},
            {'key':'niveau_max','label':'Niveau max (1-4)','type':'int','default':3,'min':1,'max':4},
        ]
    def _ok(self, ineq):
        try:
            lhs=expand(ineq.lhs); rhs=expand(ineq.rhs)
            if lhs.as_coefficients_dict()[x]==rhs.as_coefficients_dict()[x]: return False
            sol=solve_univariate_inequality(ineq,x,relational=False)
            if sol is S.EmptySet or sol==S.Reals: return False
            return True
        except: return False
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n=config.get('nb_questions',6); nmax=config.get('niveau_max',3)
        comps=[Lt,Gt,Le,Ge]; et,st,corriges=[],[],[]; total_diff=0.0
        for i in range(n):
            level=min((i*nmax)//n+1,nmax)
            cr=[random.choice([1,-1])*j for j in range(2,10)]; co=cr[:]
            while True:
                a,b,c,d,e=random.choice(cr),random.choice(co),random.choice(co),random.choice(co),random.choice(cr)
                if level==1: e1,e2=a*x,b
                elif level==2: e1,e2=a*x+b,c
                elif level==3: e1,e2=a*x+b,e*x+d
                else: e1=factor(a*(x+b)); e2=c*x+d
                comp=random.choice(comps); ineq=comp(e1,e2)
                if self._ok(ineq): break
            sol=solve_univariate_inequality(ineq,x,relational=False)
            et.append(latex(ineq)); st.append(interval_from_solution(sol))
            # Difficulté
            q_diff = 1.5 * level + 1.0  # Méthode + complexité croissante
            if level >= 3: q_diff += 1.5  # Regrouper les x
            if a < 0 or (level >= 3 and e < 0): q_diff += 1.0  # Inversion du sens
            total_diff += q_diff
            # Corrigé détaillé — résolution étape par étape
            sol_latex = interval_from_solution(sol)
            _csym = {Lt: '<', Gt: '>', Le: r'\leq', Ge: r'\geq'}
            _fsym = {Lt: '>', Gt: '<', Le: r'\geq', Ge: r'\leq'}
            cs = _csym[comp]
            def _lx(coef):
                if coef == 1: return 'x'
                if coef == -1: return '-x'
                return f"{coef}x"
            if level == 1:
                cs2 = _fsym[comp] if a < 0 else cs
                rhs_l = latex(Rational(b, a)).replace('\\frac', '\\dfrac')
                detail = (f"${_lx(a)} {cs} {b}$\n\n"
                          f"$\\Leftrightarrow x {cs2} {rhs_l}$")
            elif level == 2:
                cs2 = _fsym[comp] if a < 0 else cs
                rhs1 = c - b
                rhs_l = latex(Rational(rhs1, a)).replace('\\frac', '\\dfrac')
                detail = (f"${latex(e1)} {cs} {c}$\n\n"
                          f"$\\Leftrightarrow {_lx(a)} {cs} {c} - ({b}) = {rhs1}$\n\n"
                          f"$\\Leftrightarrow x {cs2} {rhs_l}$")
            else:
                cd = a - e; cn = d - b
                cs2 = _fsym[comp] if cd < 0 else cs
                rhs_l = latex(Rational(cn, cd)).replace('\\frac', '\\dfrac')
                detail = (f"${latex(e1)} {cs} {latex(e2)}$\n\n"
                          f"$\\Leftrightarrow {_lx(cd)} {cs} {cn}$\n\n"
                          f"$\\Leftrightarrow x {cs2} {rhs_l}$")
            corriges.append(detail + f"\n\n$S = {sol_latex}$")
        enonce = "\\noindent\\textbf{Exercice} -- Résoudre les inéquations suivantes.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for c in corriges: corrige += f"\\item {c}\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige([f'S = {s}' for s in st]),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


# ═══════════════════════════════════════════════════════════════════════════════
# Racines carrées 2nde — difficulté cognitive à la Training2ndeNum.py
# ═══════════════════════════════════════════════════════════════════════════════

@register
class RacinesCarrees2nde(ExerciseGenerator):
    id="racines_2nde"; name="Racines carrées"; niveau="2nde"
    category="Nombres et calculs"; description="Simplifier √n, combiner a√b±c√d, (a-b√c)²"
    difficulty_config = {
        'Facile':    {'nb_simplifier': 3, 'nb_combiner': 0, 'nb_radicaux': 0, 'nb_binome': 0},
        'Moyen':     {'nb_simplifier': 2, 'nb_combiner': 2, 'nb_radicaux': 1, 'nb_binome': 1},
        'Difficile': {'nb_simplifier': 2, 'nb_combiner': 3, 'nb_radicaux': 1, 'nb_binome': 2},
    }
    @staticmethod
    def get_config():
        return [
            {'key':'nb_simplifier','label':'Simplifier √n','type':'int','default':2,'min':0,'max':4},
            {'key':'nb_combiner','label':'Combiner a√b ± c√d','type':'int','default':2,'min':0,'max':4},
            {'key':'nb_radicaux','label':'Sommes de radicaux','type':'int','default':1,'min':0,'max':4},
            {'key':'nb_binome','label':'Développer (a-b√c)²','type':'int','default':1,'min':0,'max':3},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        ns=config.get('nb_simplifier',2); nc=config.get('nb_combiner',2)
        nr=config.get('nb_radicaux',1); nb=config.get('nb_binome',1)
        et,st=[],[]; total_diff=0.0
        for _ in range(ns):
            nums=random.choices([2,3,5,7],k=4); sq=random.sample(nums,k=random.randint(2,3))
            prod=1
            for nn in sq: prod*=nn**2
            mult=random.choice([2,3,5,7])
            if is_perfect_square(prod): prod*=mult
            et.append(f"\\sqrt{{{prod}}}"); st.append(latex(simplify(sqrt(prod))))
            total_diff += _sqrt_simplification_cost(prod)
        for _ in range(nc):
            b1,b2=random.sample([2,3,5,7,10,11,13],2)
            a,b,c,d=[random.randint(1,5) for _ in range(4)]
            ops=[random.choice(["+","-"]) for _ in range(3)]
            def ft(co,ba): return f"\\sqrt{{{ba}}}" if co==1 else f"{co}\\sqrt{{{ba}}}"
            expr=f"{ft(a,b1)} {ops[0]} {ft(b,b2)} {ops[1]} {ft(c,b1)} {ops[2]} {ft(d,b2)}"
            se = (a*sqrt(b1)+(b if ops[0]=="+" else -b)*sqrt(b2)
                  +(c if ops[1]=="+" else -c)*sqrt(b1)+(d if ops[2]=="+" else -d)*sqrt(b2))
            et.append(expr); st.append(latex(simplify(se)))
            # Difficulté : simplifier chaque radical + combiner
            q_diff = 0.0
            for coef, base in [(a,b1),(b,b2),(c,b1),(d,b2)]:
                q_diff += _sqrt_simplification_cost(base * coef**2) if coef > 1 else _sqrt_simplification_cost(base)
            q_diff += 2.0  # Combinaison de termes semblables
            total_diff += q_diff
        for _ in range(nr):
            base = random.choice([2, 3, 5, 7])
            perfect_squares = [4, 9, 16, 25, 36]
            squares = random.sample(perfect_squares, 3) + [1]
            random.shuffle(squares)
            coeffs = [random.randint(1, 5) for _ in range(4)]
            for _try in range(20):
                signs = [random.choice([1, -1]) for _ in range(4)]
                if sum(signs[i] * coeffs[i] for i in range(4)) != 0: break
            radicands = [squares[i] * base for i in range(4)]
            parts = []
            for sgn, coef, rad in zip(signs, coeffs, radicands):
                coef_txt = '' if coef == 1 else str(coef)
                term = f"{coef_txt}\\sqrt{{{rad}}}"
                if not parts: parts.append(term if sgn > 0 else f"-{term}")
                else: parts.append(("+ " if sgn > 0 else "- ") + term)
            expr = " ".join(parts).replace("  ", " ").strip()
            sym_expr = sum(sgn * coef * sqrt(rad) for sgn, coef, rad in zip(signs, coeffs, radicands))
            sol = latex(simplify(sym_expr)).replace('\\frac', '\\dfrac')
            et.append(expr); st.append(sol)
            q_diff = 0.0
            for rad in radicands: q_diff += _sqrt_simplification_cost(rad)
            q_diff += 3.0  # Combinaison de 4 radicaux
            total_diff += q_diff
        for _ in range(nb):
            a=random.randint(1,6); b=random.randint(1,5); rb=random.choice([2,3,5,7,10,11])
            ft2 = f"\\sqrt{{{rb}}}" if b==1 else f"{b}\\sqrt{{{rb}}}"
            et.append(f"({a} - {ft2})^2"); st.append(latex(expand((a-b*sqrt(rb))**2)))
            # (a - b√c)² = a² - 2ab√c + b²c
            q_diff = 3.0  # Reconnaître identité remarquable
            q_diff += _multiplication_weight(a,a) + _multiplication_weight(2*a,b) + _multiplication_weight(b*b,rb)
            q_diff += _sqrt_simplification_cost(rb)
            total_diff += q_diff
        total=ns+nc+nr+nb
        if total==0: return {'enonce':'','corrige':'','corrige_succinct':'','qr_data':None,'difficulte_raw':0,'qr_answers':[]}
        enonce = "\\noindent\\textbf{Exercice} -- Calculer et simplifier.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for s in st: corrige += f"\\item ${s}$\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige(st),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


@register
class Fractions2nde(ExerciseGenerator):
    id="fractions_2nde"; name="Calcul fractionnaire"; niveau="2nde"
    category="Nombres et calculs"; description="Somme/diff, priorité ×, fraction imbriquée"
    difficulty_config = {
        'Facile':    {'nb_somme': 3, 'nb_prod_diff': 0, 'nb_imbriquee': 0},
        'Moyen':     {'nb_somme': 2, 'nb_prod_diff': 2, 'nb_imbriquee': 1},
        'Difficile': {'nb_somme': 1, 'nb_prod_diff': 2, 'nb_imbriquee': 2},
    }
    @staticmethod
    def get_config():
        return [
            {'key':'nb_somme','label':'Somme/différence','type':'int','default':2,'min':0,'max':4},
            {'key':'nb_prod_diff','label':'a/b - c/d × e/f','type':'int','default':2,'min':0,'max':4},
            {'key':'nb_imbriquee','label':'Fraction imbriquée','type':'int','default':1,'min':0,'max':3},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n1=config.get('nb_somme',2); n2=config.get('nb_prod_diff',2); n3=config.get('nb_imbriquee',1)
        et,st,corriges=[],[],[]; total_diff=0.0
        from math import lcm
        for _ in range(n1):
            d1,d2=random.randint(2,10),random.randint(2,10)
            while d2==d1: d2=random.randint(2,10)
            n_1,n_2=random.randint(1,10),random.randint(1,10); op=random.choice(['+','-'])
            et.append(f"\\dfrac{{{n_1}}}{{{d1}}} {op} \\dfrac{{{n_2}}}{{{d2}}}")
            v=Rational(n_1,d1)+(Rational(n_2,d2) if op=='+' else -Rational(n_2,d2))
            v_l = latex(nsimplify(v,rational=True)).replace('\\frac','\\dfrac')
            st.append(v_l)
            dc = lcm(d1, d2); k1 = dc // d1; k2 = dc // d2
            num1 = n_1 * k1; num2 = n_2 * k2
            combined = num1 + (num2 if op == '+' else -num2)
            from math import gcd as _gcd
            already_reduced = _gcd(abs(combined), dc) == 1
            mid_s = f"\\dfrac{{{combined}}}{{{dc}}}"
            if k1 == 1 and k2 == 1:
                corriges.append(f"$\\dfrac{{{n_1} {op} {n_2}}}{{{dc}}} = {v_l}$")
            elif already_reduced:
                corriges.append(
                    f"$\\dfrac{{{n_1} \\times {k1}}}{{{d1} \\times {k1}}} {op} "
                    f"\\dfrac{{{n_2} \\times {k2}}}{{{d2} \\times {k2}}} "
                    f"= {mid_s}$")
            else:
                corriges.append(
                    f"$\\dfrac{{{n_1} \\times {k1}}}{{{d1} \\times {k1}}} {op} "
                    f"\\dfrac{{{n_2} \\times {k2}}}{{{d2} \\times {k2}}} "
                    f"= {mid_s} = {v_l}$")
            q_diff = 2.0 + _multiplication_weight(n_1, k1) + _multiplication_weight(n_2, k2) + _addition_weight(num1, num2)
            if dc != d1 and dc != d2: q_diff += 1.0
            total_diff += q_diff
        for _ in range(n2):
            a,b,c,d,e,f=random.randint(1,5),random.randint(2,6),random.randint(1,5),random.randint(2,6),random.randint(1,5),random.randint(2,6)
            et.append(f"\\dfrac{{{a}}}{{{b}}} - \\dfrac{{{c}}}{{{d}}} \\times \\dfrac{{{e}}}{{{f}}}")
            v=Rational(a,b)-Rational(c,d)*Rational(e,f)
            v_l = latex(nsimplify(v,rational=True)).replace('\\frac','\\dfrac')
            st.append(v_l)
            # Étape 1 : priorité ×
            prod_v = Rational(c*e, d*f)
            prod_l = latex(prod_v).replace('\\frac','\\dfrac')
            # Étape 2 : LCD et combinaison
            pnum = prod_v.numerator; pden = prod_v.denominator
            dc2 = lcm(b, pden); ka = dc2 // b; kp = dc2 // pden
            combined2 = a * ka - pnum * kp
            if ka == 1 and kp == 1:
                step2 = f"$= \\dfrac{{{a} - {pnum}}}{{{dc2}}} = {v_l}$"
            else:
                frac_raw = Rational(combined2, dc2)
                mid = f"\\dfrac{{{combined2}}}{{{dc2}}}"
                if frac_raw == v:
                    # déjà irréductible, pas besoin de répéter
                    step2 = (f"$= \\dfrac{{{a * ka}}}{{{dc2}}} - \\dfrac{{{pnum * kp}}}{{{dc2}}} "
                             f"= {mid}$")
                else:
                    step2 = (f"$= \\dfrac{{{a * ka}}}{{{dc2}}} - \\dfrac{{{pnum * kp}}}{{{dc2}}} "
                             f"= {mid} = {v_l}$")
            corriges.append(
                f"$= \\dfrac{{{a}}}{{{b}}} - {prod_l}$ (priorité $\\times$)\n\n{step2}")
            q_diff = 3.0 + _multiplication_weight(c,e) + _multiplication_weight(d,f) + 2.0
            total_diff += q_diff
        for _ in range(n3):
            while True:
                a,b,c=random.randint(1,5),random.randint(1,5),random.randint(2,6)
                d,e,f_,g=random.randint(1,5),random.randint(2,6),random.randint(1,5),random.randint(2,6)
                dv=Rational(d,e)-Rational(f_,g)
                if dv!=0: break
            et.append(f"\\dfrac{{{a} + \\dfrac{{{b}}}{{{c}}}}}{{\\dfrac{{{d}}}{{{e}}} - \\dfrac{{{f_}}}{{{g}}}}}")
            v=(a+Rational(b,c))/dv
            v_l = latex(nsimplify(v,rational=True)).replace('\\frac','\\dfrac')
            st.append(v_l)
            # Numérateur : a + b/c = (a*c + b)/c
            num_num = a * c + b
            num_l = latex(Rational(num_num, c)).replace('\\frac','\\dfrac')
            # Dénominateur : d/e - f/g = (d*g - f*e)/(e*g)
            den_num = d * g - f_ * e; den_den = e * g
            den_l = latex(Rational(den_num, den_den)).replace('\\frac','\\dfrac')
            # Division : num_l ÷ den_l = num_l × (den_den / den_num), gérer le signe
            inv_den_l = latex(Rational(den_den, den_num)).replace('\\frac','\\dfrac')
            corriges.append(
                f"Numérateur : ${a} + \\dfrac{{{b}}}{{{c}}} = \\dfrac{{{a} \\times {c} + {b}}}{{{c}}} = {num_l}$\n\n"
                f"Dénominateur : $\\dfrac{{{d}}}{{{e}}} - \\dfrac{{{f_}}}{{{g}}} = "
                f"\\dfrac{{{d} \\times {g} - {f_} \\times {e}}}{{{e} \\times {g}}} = {den_l}$\n\n"
                f"$= {num_l} \\div {den_l} = {num_l} \\times {inv_den_l} = {v_l}$")
            q_diff = 6.0
            total_diff += q_diff
        total=n1+n2+n3
        if total==0: return {'enonce':'','corrige':'','corrige_succinct':'','qr_data':None,'difficulte_raw':0,'qr_answers':[]}
        enonce = "\\noindent\\textbf{Exercice} -- Calculer et simplifier.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for s in corriges: corrige += f"\\item {s}\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige(st),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


# ═══════════════════════════════════════════════════════════════════════════════
# Vecteurs, Droites, Tableau de signes, Factorisation, Identités remarquables
# ═══════════════════════════════════════════════════════════════════════════════

@register
class Vecteurs2nde(ExerciseGenerator):
    id="vecteurs_2nde"; name="Vecteurs — coordonnées"; niveau="2nde"
    category="Géométrie"; description="Coordonnées, milieu, colinéarité"
    difficulty_config = {'Facile':{'nb_coord':3,'nb_milieu':2,'nb_colin':0},'Moyen':{'nb_coord':3,'nb_milieu':2,'nb_colin':2},'Difficile':{'nb_coord':4,'nb_milieu':2,'nb_colin':3}}
    @staticmethod
    def get_config():
        return [
            {'key':'nb_coord','label':'Questions coordonnées','type':'int','default':3,'min':0,'max':6},
            {'key':'nb_milieu','label':'Questions milieu','type':'int','default':2,'min':0,'max':4},
            {'key':'nb_colin','label':'Questions colinéarité','type':'int','default':2,'min':0,'max':4},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        enonce=""; corrige=""; ne=0; qr_vect=[]; total_diff=0.0
        nc=config.get('nb_coord',3)
        if nc>0:
            ne+=1
            enonce+=f"\\noindent\\textbf{{{ne})}} Calculer les coordonnées de ${vect('A','B')}$.\n\\begin{{enumerate}}\n"
            corrige+=f"\\textbf{{{ne})}}\n\\begin{{enumerate}}\n"
            for _ in range(nc):
                ax,ay,bx,by=[random.randint(-5,5) for _ in range(4)]
                enonce+=f"\\item ${pt('A')}({ax}\\,;\\,{ay})$ et ${pt('B')}({bx}\\,;\\,{by})$\n"
                corrige+=f"\\item ${vect('A','B')}({bx-ax}\\,;\\,{by-ay})$\n"
                qr_vect.append(f'AB({bx-ax};{by-ay})')
                total_diff += 1.5 + _addition_weight(abs(bx),abs(ax)) + _addition_weight(abs(by),abs(ay))
            enonce+="\\end{enumerate}\n"; corrige+="\\end{enumerate}\n"
        nm=config.get('nb_milieu',2)
        if nm>0:
            ne+=1
            enonce+=f"\\medskip\n\\noindent\\textbf{{{ne})}} Calculer les coordonnées du milieu de $[{pt('A')}{pt('B')}]$.\n\\begin{{enumerate}}\n"
            corrige+=f"\\textbf{{{ne})}}\n\\begin{{enumerate}}\n"
            for _ in range(nm):
                ax,ay,bx,by=[random.randint(-8,8) for _ in range(4)]
                mx=Rational(ax+bx,2); my=Rational(ay+by,2)
                enonce+=f"\\item ${pt('A')}({ax}\\,;\\,{ay})$ et ${pt('B')}({bx}\\,;\\,{by})$\n"
                corrige+=f"\\item ${pt('M')}\\left({latex(mx).replace(chr(92)+'frac',chr(92)+'dfrac')}\\,;\\,{latex(my).replace(chr(92)+'frac',chr(92)+'dfrac')}\\right)$\n"
                total_diff += 2.0 + _addition_weight(abs(ax),abs(bx)) + _addition_weight(abs(ay),abs(by)) + 0.8  # Division par 2
            enonce+="\\end{enumerate}\n"; corrige+="\\end{enumerate}\n"
        ncl=config.get('nb_colin',2)
        if ncl>0:
            ne+=1
            enonce+=f"\\medskip\n\\noindent\\textbf{{{ne})}} Les vecteurs ${vect_u('u')}$ et ${vect_u('v')}$ sont-ils colinéaires ?\n\\begin{{enumerate}}\n"
            corrige+=f"\\textbf{{{ne})}}\n\\begin{{enumerate}}\n"
            for _ in range(ncl):
                ux,uy=random.randint(-5,5),random.randint(-5,5)
                while ux==0 and uy==0: ux,uy=random.randint(-5,5),random.randint(-5,5)
                if random.random()<0.5:
                    k=random.choice([j for j in range(-3,4) if j!=0]); vx,vy=k*ux,k*uy; rep="Oui"
                else:
                    vx,vy=random.randint(-5,5),random.randint(-5,5)
                    if ux*vy-uy*vx==0: vy+=1
                    rep="Non"
                det=ux*vy-uy*vx
                enonce+=f"\\item ${vect_u('u')}({ux}\\,;\\,{uy})$ et ${vect_u('v')}({vx}\\,;\\,{vy})$\n"
                corrige+=f"\\item $\\det({vect_u('u')},{vect_u('v')}) = {ux}\\times({vy})-({uy})\\times{vx} = {det}$. {rep}.\n"
                total_diff += 3.0 + _multiplication_weight(ux,vy) + _multiplication_weight(uy,vx) + _addition_weight(abs(ux*vy),abs(uy*vx))
            enonce+="\\end{enumerate}\n"; corrige+="\\end{enumerate}\n"
        enonce = "\\noindent\\textbf{Exercice} -- Vecteurs et coordonnées.\\\\\n\\medskip\n" + enonce
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':corrige,'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in qr_vect]}



def _subst_x(a, b, xi_l):
    """Génère la chaîne y = ax·xi + b avec gestion de a=±1."""
    if a == 1:
        term = xi_l
    elif a == -1:
        term = f"-({xi_l})"
    else:
        term = f"{a} \\times ({xi_l})"
    if b == 0:
        return term
    elif b > 0:
        return f"{term} + {b}"
    else:
        return f"{term} - {-b}"

@register
class EquationsDroites2nde(ExerciseGenerator):
    id="droites_2nde"; name="Équations de droites"; niveau="2nde"
    category="Géométrie"; description="Équation par 2 points, intersection"
    difficulty_config = {'Facile':{'nb_eq_2pts':3,'nb_intersection':0},'Moyen':{'nb_eq_2pts':3,'nb_intersection':2},'Difficile':{'nb_eq_2pts':4,'nb_intersection':3}}
    @staticmethod
    def get_config():
        return [
            {'key':'nb_eq_2pts','label':'Équation par 2 points','type':'int','default':3,'min':0,'max':6},
            {'key':'nb_intersection','label':'Intersection','type':'int','default':2,'min':0,'max':4},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        enonce=""; corrige=""; ne=0; qr_droites=[]; total_diff=0.0
        n1=config.get('nb_eq_2pts',3)
        if n1>0:
            ne+=1
            enonce+=f"\\noindent\\textbf{{{ne})}} Déterminer l'équation réduite de la droite $({pt('A')}{pt('B')})$.\n\\begin{{enumerate}}\n"
            corrige+=f"\\textbf{{{ne})}}\n\\begin{{enumerate}}\n"
            for _ in range(n1):
                while True:
                    ax,ay,bx,by=[random.randint(-5,5) for _ in range(4)]
                    if ax!=bx: break
                m=Rational(by-ay,bx-ax); p=Rational(ay)-m*ax
                ml=latex(m).replace('\\frac','\\dfrac'); pl=latex(abs(p)).replace('\\frac','\\dfrac')
                eq=f"y = {ml}x"
                if p>0: eq+=f" + {pl}"
                elif p<0: eq+=f" - {pl}"
                enonce+=f"\\item ${pt('A')}({ax}\\,;\\,{ay})$ et ${pt('B')}({bx}\\,;\\,{by})$\n"
                corrige+=f"\\item $m = \\dfrac{{{by}-{ay}}}{{{bx}-{ax}}} = {ml}$ donc ${eq}$\n"
                qr_droites.append(_plain(eq))
                total_diff += 3.5 + _addition_weight(abs(by),abs(ay)) + _addition_weight(abs(bx),abs(ax)) + _fraction_cost(by-ay,bx-ax)
            enonce+="\\end{enumerate}\n"; corrige+="\\end{enumerate}\n"
        n2=config.get('nb_intersection',2)
        if n2>0:
            ne+=1
            enonce+=f"\\noindent\\textbf{{{ne})}} Déterminer le point d'intersection.\n\\begin{{enumerate}}\n"
            corrige+=f"\\textbf{{{ne})}}\n\\begin{{enumerate}}\n"
            for _ in range(n2):
                while True:
                    a1=random.choice([j for j in range(-5,6) if j!=0]); b1=random.randint(-5,5)
                    a2=random.choice([j for j in range(-5,6) if j!=0]); b2=random.randint(-5,5)
                    if a1!=a2: break
                xi=Rational(b2-b1,a1-a2); yi=a1*xi+b1
                def fd(a,b):
                    s=f"y = {a}x" if a not in [1,-1] else ("y = x" if a==1 else "y = -x")
                    if b>0: s+=f" + {b}"
                    elif b<0: s+=f" - {-b}"
                    return s
                enonce+=f"\\item $(d_1): {fd(a1,b1)}$ et $(d_2): {fd(a2,b2)}$\n"
                xi_l = latex(xi).replace('\\frac','\\dfrac')
                yi_l = latex(yi).replace('\\frac','\\dfrac')
                cd = a1 - a2; cn = b2 - b1
                cd_str = '' if cd == 1 else ('-' if cd == -1 else str(cd))
                xi_raw = Rational(cn, cd)
                if abs(cd) == 1:
                    # cd=±1 : une seule étape suffit
                    step_x = f"$\\Leftrightarrow x = {xi_l}$"
                else:
                    step_x = f"$\\Leftrightarrow {cd_str}x = {cn}$\n\n$\\Leftrightarrow x = {xi_l}$"
                corrige += (
                    f"\\item On cherche les couples $(x\\,;\\,y)$ vérifiant les deux équations :\n\n"
                    f"${fd(a1,b1).replace('y = ','')} = {fd(a2,b2).replace('y = ','')}$\n\n"
                    f"{step_x}\n\n"
                    f"puis $y = {_subst_x(a1, b1, xi_l)} = {yi_l}$\n\n"
                    f"Donc le point d'intersection est $\\left({xi_l}\\,;\\,{yi_l}\\right)$.\n"
                )
                total_diff += 5.0 + _fraction_cost(b2-b1,a1-a2) + _multiplication_weight(abs(a1),abs(int(xi.p))) if xi.q != 1 else 0.0
            enonce+="\\end{enumerate}\n"; corrige+="\\end{enumerate}\n"
        enonce = "\\noindent\\textbf{Exercice} -- Équations de droites.\n\\medskip\n" + enonce
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':corrige,'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':qr_droites}

# ═══════════════════════════════════════════════════════════════════════════════
# Tableau de signes
# ═══════════════════════════════════════════════════════════════════════════════

def _pm(v):
    return '+' if v > 0 else '-'

def _tkz_line_for_factor_from_signs(sign_left, sign_mid, sign_right, zero_at_first):
    if zero_at_first:
        return f", {_pm(sign_left)}, z, {_pm(sign_mid)}, t, {_pm(sign_right)}"
    return f", {_pm(sign_left)}, t, {_pm(sign_mid)}, z, {_pm(sign_right)}"

def _tkz_line_for_result(sign_left, sign_mid, sign_right, mark1, mark2):
    return f", {_pm(sign_left)}, {mark1}, {_pm(sign_mid)}, {mark2}, {_pm(sign_right)}"

def _build_sign_table(a, b, c, d, is_quotient=False):
    r_num = Rational(-b, a); r_den = Rational(-d, c)
    order = sorted([(r_num, 'num'), (r_den, 'den')], key=lambda t: float(t[0]))
    x1, t1 = order[0]; x2, t2 = order[1]
    test_left = x1 - 1; test_mid = Rational(x1 + x2, 2); test_right = x2 + 1
    num_left = 1 if (a * test_left + b) > 0 else -1
    num_mid = 1 if (a * test_mid + b) > 0 else -1
    num_right = 1 if (a * test_right + b) > 0 else -1
    den_left = 1 if (c * test_left + d) > 0 else -1
    den_mid = 1 if (c * test_mid + d) > 0 else -1
    den_right = 1 if (c * test_right + d) > 0 else -1
    res_left = num_left * den_left; res_mid = num_mid * den_mid; res_right = num_right * den_right
    num_expr = latex(a*x + b).replace('\\frac', '\\dfrac')
    den_expr = latex(c*x + d).replace('\\frac', '\\dfrac')
    res_expr = f"\\dfrac{{{num_expr}}}{{{den_expr}}}" if is_quotient else f"({num_expr})({den_expr})"
    x1s = latex(x1).replace('\\frac', '\\dfrac'); x2s = latex(x2).replace('\\frac', '\\dfrac')
    line_num = _tkz_line_for_factor_from_signs(num_left, num_mid, num_right, t1 == 'num')
    line_den = _tkz_line_for_factor_from_signs(den_left, den_mid, den_right, t1 == 'den')
    if is_quotient: mark1 = 'z' if t1 == 'num' else 'd'; mark2 = 'z' if t2 == 'num' else 'd'
    else: mark1 = 'z'; mark2 = 'z'
    line_res = _tkz_line_for_result(res_left, res_mid, res_right, mark1, mark2)
    def _expr_visual_weight(s):
        weight = len(s) + 4 * s.count('\\dfrac') + 2 * (s.count('(') + s.count(')')) + s.count('x')
        return weight
    first_col_weight = max(_expr_visual_weight(num_expr), _expr_visual_weight(den_expr), _expr_visual_weight(res_expr))
    first_col_lgt = min(7.5, max(3.0, round(2.2 + 0.055 * first_col_weight, 2)))
    return (
        "\\begin{center}\n\\begin{tikzpicture}\n"
        f"\\tkzTabInit[lgt={first_col_lgt},espcl=2]{{$x$ / 1, ${num_expr}$ / 1, ${den_expr}$ / 1, ${res_expr}$ / 1.5}}{{$-\\infty$, ${x1s}$, ${x2s}$, $+\\infty$}}\n"
        f"\\tkzTabLine{{{line_num}}}\n\\tkzTabLine{{{line_den}}}\n\\tkzTabLine{{{line_res}}}\n"
        "\\end{tikzpicture}\n\\end{center}\n")

@register
class TableauSignes2nde(ExerciseGenerator):
    id="tableau_signes_2nde"; name="Inéquations produit/quotient"; niveau="2nde"
    category="Fonctions"; description="(ax+b)(cx+d) ou quotient résolu via tableau de signes"
    difficulty_config = {'Facile':{'nb_questions':2},'Moyen':{'nb_questions':4},'Difficile':{'nb_questions':6}}
    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':4,'min':2,'max':8}]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n = config.get('nb_questions', 4); comps = [Lt, Gt, Le, Ge]
        et, st, ct = [], [], []; total_diff = 0.0
        for _ in range(n):
            while True:
                a = random.choice([1,-1])*random.randint(1,5); b = random.choice([1,-1])*random.randint(1,9)
                c = random.choice([1,-1])*random.randint(1,5); d = random.choice([1,-1])*random.randint(1,9)
                if Rational(-b,a) != Rational(-d,c): break
            is_quotient = random.choice([False, True])
            expr = ((a*x+b)/(c*x+d)) if is_quotient else ((a*x+b)*(c*x+d))
            comp = random.choice(comps); ineq = comp(expr, 0)
            try:
                sol = solve_univariate_inequality(ineq, x, relational=False)
                ss = interval_from_solution(sol)
            except Exception: ss = "\\text{Erreur}"
            et.append(latex(ineq).replace('\\frac', '\\dfrac'))
            st.append(ss); ct.append(_build_sign_table(a, b, c, d, is_quotient=is_quotient))
            q_diff = 4.0 + _fraction_cost(-b,a) + _fraction_cost(-d,c) + 2.0  # Tableau + lecture
            if is_quotient: q_diff += 1.5  # Quotient = valeurs interdites
            total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Résoudre à l'aide d'un tableau de signes.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = ""
        for i, sol in enumerate(st, start=1):
            corrige += f"\\noindent\\textbf{{{i})}}\\par\\smallskip\n{ct[i-1]}\\par\\smallskip\n\\begin{{center}}$S = {sol}$\\end{{center}}\\par\\medskip\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige([f'S = {s}' for s in st]),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


@register
class FactorisationCommun2nde(ExerciseGenerator):
    id = "factorisation_commun_2nde"; name = "Factorisation par facteur commun"; niveau = "2nde"
    category = "Calcul littéral"
    description = "Factoriser (ax+b)(cx+d) ± (ax+b)(ex+f) en dégageant le facteur commun"
    difficulty_config = {'Facile':{'nb_questions':2},'Moyen':{'nb_questions':3},'Difficile':{'nb_questions':4}}
    @staticmethod
    def get_config():
        return [{'key':'nb_questions','label':'Nombre de questions','type':'int','default':3,'min':1,'max':6}]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n = config.get('nb_questions', 3); et, st = [], []; total_diff = 0.0
        for q in range(n):
            for _ in range(50):
                a = random.choice([1,-1])*random.randint(1,6); b = random.choice([1,-1])*random.randint(2,7)
                c = random.choice([1,-1])*random.randint(2,7); d = random.choice([1,-1])*random.randint(2,7)
                e = random.choice([1,-1])*random.randint(2,7); f = random.choice([1,-1])*random.randint(1,7)
                sgn = random.choice([1, -1])
                inner = (c*x+d) + sgn*(e*x+f)
                if inner.coeff(x) == 0 and inner.coeff(x, 0) == 0: continue
                break
            fac_commun = a*x+b; fac2 = c*x+d; fac3 = e*x+f
            def _fmt_bin(p, q): return str(p*x+q).replace('**','^').replace('*','')
            fc_str = _fmt_bin(a,b); f2_str = _fmt_bin(c,d); f3_str = _fmt_bin(e,f)
            op = '+' if sgn == 1 else '-'
            enonce_str = f"$({fc_str})({f2_str}) {op} ({fc_str})({f3_str})$"
            inner_expr = fac2 + sgn*fac3; inner_expanded = expand(inner_expr)
            inner_str = str(inner_expanded).replace('**','^').replace('*','')
            solution_str = f"({fc_str})({inner_str})"
            et.append(enonce_str); st.append(solution_str)
            q_diff = 3.0 + _addition_weight(abs(c), abs(e)) + _addition_weight(abs(d), abs(f))
            q_diff += _sign_cost(sgn < 0) + 1.5  # Identifier le facteur commun
            total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Factoriser les expressions suivantes.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item {e}\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for s in st: corrige += f"\\item ${s}$\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige(st),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


@register
class IdentitesRemarquables2nde(ExerciseGenerator):
    id = "identites_remarquables_2nde"; name = "Identités remarquables"; niveau = "2nde"
    category = "Calcul littéral"
    description = "Factoriser via (a+b)²=a²+2ab+b², (a-b)²=a²-2ab+b², (a+b)(a-b)=a²-b²"
    difficulty_config = {
        'Facile':{'nb_questions':3,'types':'Différence de carrés uniquement'},
        'Moyen':{'nb_questions':3,'types':'Mixte'},
        'Difficile':{'nb_questions':4,'types':'Mixte'},
    }
    @staticmethod
    def get_config():
        return [
            {'key':'nb_questions','label':'Nombre de questions','type':'int','default':3,'min':2,'max':6},
            {'key':'types','label':'Types','type':'choice','default':'Mixte',
             'choices':['Mixte','Différence de carrés uniquement','Carré développé uniquement']},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n = config.get('nb_questions', 3); types_mode = config.get('types', 'Mixte')
        et, st = [], []; total_diff = 0.0
        def diff_carres():
            variant = random.choice(['simple', 'double'])
            if variant == 'simple':
                a = random.choice([1,-1])*random.randint(1,9); b = random.randint(2,9)
                enonce_ex = f"(x {'+' if a>=0 else '-'} {abs(a)})^2 - {b}^2"
                expr = (x+a)**2 - b**2; sol = factor(expr)
                return f"${enonce_ex}$", str(sol).replace('**','^').replace('*',''), 3.5
            else:
                a = random.choice([1,-1])*random.randint(1,7); b = random.randint(2,5)
                c = random.choice([1,-1])*random.randint(1,7)
                enonce_ex = f"(x {'+' if a>=0 else '-'} {abs(a)})^2 - ({b}x {'+' if c>=0 else '-'} {abs(c)})^2"
                expr = (x+a)**2 - (b*x+c)**2; sol = factor(expr)
                return f"${enonce_ex}$", str(sol).replace('**','^').replace('*',''), 5.0
        def carre_developpe():
            a = random.randint(2,5); b = random.choice([1,-1])*random.randint(2,9)
            expr = (a*x+b)**2; expanded = expand(expr)
            enonce_ex = str(expanded).replace('**','^').replace('*','')
            sol = f"({a}x {'+' if b>=0 else '-'} {abs(b)})^2"
            return f"${enonce_ex}$", sol, 4.0
        if types_mode == 'Différence de carrés uniquement': pool = [diff_carres]*n
        elif types_mode == 'Carré développé uniquement': pool = [carre_developpe]*n
        else:
            pool = [diff_carres, carre_developpe]; pool = [pool[i%2] for i in range(n)]
            random.shuffle(pool)
        for gen_fn in pool:
            enonce_q, sol_q, q_diff = gen_fn()
            et.append(enonce_q); st.append(sol_q); total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Factoriser en utilisant une identité remarquable.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item {e}\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for s in st: corrige += f"\\item ${s}$\n"
        corrige += "\\end{enumerate}\n"
        return {'enonce':enonce,'corrige':corrige,'corrige_succinct':_build_succinct_corrige(st),'qr_data':None,
                'difficulte':config.get('difficulte','Moyen'),
                'difficulte_raw':round(total_diff, 2),
                'qr_answers':[_plain(s) for s in st]}


# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  NOUVEAUX GÉNÉRATEURS                                                        ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

@register
class IntervallesValeurAbsolue2nde(ExerciseGenerator):
    id = "intervalles_abs_2nde"; name = "Intervalles et valeur absolue"; niveau = "2nde"
    category = "Nombres et calculs"
    description = "Appartenance à un intervalle, |x-a| ≤ r ↔ [a-r, a+r]"
    difficulty_config = {
        'Facile': {'nb_questions': 4, 'avec_abs': 'Non'},
        'Moyen':  {'nb_questions': 5, 'avec_abs': 'Mélange'},
        'Difficile': {'nb_questions': 6, 'avec_abs': 'Oui'},
    }
    @staticmethod
    def get_config():
        return [
            {'key': 'nb_questions', 'label': 'Nombre de questions', 'type': 'int', 'default': 5, 'min': 2, 'max': 10},
            {'key': 'avec_abs', 'label': 'Valeur absolue', 'type': 'choice', 'default': 'Mélange',
             'choices': ['Oui', 'Non', 'Mélange']},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n = config.get('nb_questions', 5)
        avec_abs = config.get('avec_abs', 'Mélange')
        et, st, corriges = [], [], []; total_diff = 0.0
        for i in range(n):
            use_abs = (avec_abs == 'Oui') or (avec_abs == 'Mélange' and i >= n // 2)
            if use_abs:
                # |x - a| ≤ r  ↔  a - r ≤ x ≤ a + r
                a_val = random.choice([1,-1]) * random.randint(1, 8)
                r_val = random.randint(1, 5)
                strict = random.choice([True, False])
                comp = '<' if strict else '\\leqslant'
                # Écriture sans parenthèses inutiles : |x - 3|, |x + 5|, |x|
                if a_val == 0:
                    abs_str = "|x|"
                elif a_val > 0:
                    abs_str = f"|x - {a_val}|"
                else:
                    abs_str = f"|x + {-a_val}|"
                enonce_str = f"{abs_str} {comp} {r_val}"
                lo = a_val - r_val; hi = a_val + r_val
                if strict:
                    sol_str = f"\\left] {lo} \\,;\\, {hi} \\right["
                else:
                    sol_str = f"\\left[ {lo} \\,;\\, {hi} \\right]"
                detail = (f"${enonce_str}$\n\n"
                          f"si et seulement si ${a_val} - {r_val} {comp.replace('leqslant','leq')} x {comp.replace('leqslant','leq')} {a_val} + {r_val}$\n\n"
                          f"si et seulement si $x \\in {sol_str}$")
                q_diff = 3.0 + _addition_weight(abs(a_val), r_val) * 2
                if a_val < 0: q_diff += 1.0
            else:
                # Appartenance : x ∈ [a; b] signifie a ≤ x ≤ b
                a_val = random.choice([1,-1]) * random.randint(0, 8)
                b_val = a_val + random.randint(1, 6)
                test_val = random.choice([a_val - 1, a_val, a_val + 1, b_val, b_val + 1,
                                          random.randint(a_val, b_val)])
                lo_open = random.choice([True, False])
                hi_open = random.choice([True, False])
                lb = '\\left]' if lo_open else '\\left['
                rb = '\\right[' if hi_open else '\\right]'
                interval_str = f"{lb} {a_val} \\,;\\, {b_val} {rb}"
                enonce_str = f"\\text{{Le nombre }} {test_val} \\text{{ appartient-il à }} {interval_str} \\text{{ ?}}"
                # Vérifier
                if lo_open:
                    lo_ok = test_val > a_val
                else:
                    lo_ok = test_val >= a_val
                if hi_open:
                    hi_ok = test_val < b_val
                else:
                    hi_ok = test_val <= b_val
                belongs = lo_ok and hi_ok
                sol_str = "Oui" if belongs else "Non"
                membership = r"$\in$" if belongs else r"$\notin$"
                detail = f"${test_val}$ {membership} ${interval_str}$"
                q_diff = 1.5
                if lo_open or hi_open: q_diff += 0.5  # Attention aux bornes ouvertes
            et.append(enonce_str); st.append(sol_str); corriges.append(detail)
            total_diff += q_diff
        enonce = "\\noindent\\textbf{Exercice} -- Intervalles et valeur absolue.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for d in corriges: corrige += f"\\item {d}\n"
        corrige += "\\end{enumerate}\n"
        corrige_succinct = _build_succinct_corrige(st)
        return {'enonce': enonce, 'corrige': corrige, 'corrige_succinct': corrige_succinct, 'qr_data': None,
                'difficulte': config.get('difficulte', 'Moyen'),
                'difficulte_raw': round(total_diff, 2),
                'qr_answers': [_plain(s) for s in st]}


@register
class FonctionsReference2nde(ExerciseGenerator):
    id = "fonctions_ref_2nde"; name = "Fonctions de référence"; niveau = "2nde"
    category = "Fonctions"
    description = "Comparer f(a) et f(b), résoudre f(x)=k pour carré, inverse, racine, cube"
    difficulty_config = {
        'Facile': {'nb_questions': 4, 'fonctions': 'Carré uniquement'},
        'Moyen':  {'nb_questions': 5, 'fonctions': 'Mixte'},
        'Difficile': {'nb_questions': 6, 'fonctions': 'Mixte'},
    }
    @staticmethod
    def get_config():
        return [
            {'key': 'nb_questions', 'label': 'Nombre de questions', 'type': 'int', 'default': 5, 'min': 2, 'max': 10},
            {'key': 'fonctions', 'label': 'Fonctions', 'type': 'choice', 'default': 'Mixte',
             'choices': ['Mixte', 'Carré uniquement', 'Inverse uniquement', 'Racine uniquement']},
        ]
    def generate(self, config):
        config = self._resolve_difficulty(config)
        n = config.get('nb_questions', 5)
        ftype = config.get('fonctions', 'Mixte')
        et, st, corriges = [], [], []; total_diff = 0.0

        func_pool = ['carre', 'inverse', 'racine', 'cube']
        if ftype == 'Carré uniquement': func_pool = ['carre']
        elif ftype == 'Inverse uniquement': func_pool = ['inverse']
        elif ftype == 'Racine uniquement': func_pool = ['racine']

        for i in range(n):
            func = random.choice(func_pool)
            task = random.choice(['comparer', 'resoudre']) if i >= n // 2 else 'comparer'

            if task == 'comparer':
                if func == 'carre':
                    a_val = random.choice([1,-1]) * random.randint(1, 8)
                    b_val = random.choice([1,-1]) * random.randint(1, 8)
                    while abs(a_val) == abs(b_val): b_val = random.choice([1,-1]) * random.randint(1, 8)
                    fa, fb = a_val**2, b_val**2
                    fname = "f(x) = x^2"
                    enonce_str = f"f(x) = x^2. \\text{{ Comparer }} f({a_val}) \\text{{ et }} f({b_val})"
                    comp = '>' if fa > fb else ('<' if fa < fb else '=')
                    detail = f"$f({a_val}) = {fa}$ et $f({b_val}) = {fb}$ donc $f({a_val}) {comp} f({b_val})$"
                    q_diff = 2.0 + _multiplication_weight(abs(a_val), abs(a_val)) + _multiplication_weight(abs(b_val), abs(b_val))
                elif func == 'inverse':
                    while True:
                        a_val = random.choice([1,-1]) * random.randint(1, 6)
                        b_val = random.choice([1,-1]) * random.randint(1, 6)
                        if a_val != 0 and b_val != 0 and a_val != b_val: break
                    fa = Rational(1, a_val); fb = Rational(1, b_val)
                    enonce_str = f"f(x) = \\dfrac{{1}}{{x}}. \\text{{ Comparer }} f({a_val}) \\text{{ et }} f({b_val})"
                    comp = '>' if fa > fb else ('<' if fa < fb else '=')
                    fal = latex(fa).replace('\\frac','\\dfrac'); fbl = latex(fb).replace('\\frac','\\dfrac')
                    detail = f"$f({a_val}) = {fal}$ et $f({b_val}) = {fbl}$ donc $f({a_val}) {comp} f({b_val})$"
                    q_diff = 2.5 + _fraction_cost(1, a_val) + _fraction_cost(1, b_val)
                elif func == 'racine':
                    a_val = random.randint(0, 10); b_val = random.randint(0, 10)
                    while a_val == b_val: b_val = random.randint(0, 10)
                    enonce_str = f"f(x) = \\sqrt{{x}}. \\text{{ Comparer }} f({a_val}) \\text{{ et }} f({b_val})"
                    comp = '>' if a_val > b_val else '<'
                    detail = f"$\\sqrt{{x}}$ est croissante sur $[0;+\\infty[$. Comme ${a_val} {comp.replace('>','>')} {b_val}$, $f({a_val}) {comp} f({b_val})$"
                    q_diff = 2.0
                else:  # cube
                    a_val = random.choice([1,-1]) * random.randint(1, 5)
                    b_val = random.choice([1,-1]) * random.randint(1, 5)
                    while a_val == b_val: b_val = random.choice([1,-1]) * random.randint(1, 5)
                    fa, fb = a_val**3, b_val**3
                    enonce_str = f"f(x) = x^3. \\text{{ Comparer }} f({a_val}) \\text{{ et }} f({b_val})"
                    comp = '>' if fa > fb else '<'
                    detail = f"$f({a_val}) = {fa}$ et $f({b_val}) = {fb}$ donc $f({a_val}) {comp} f({b_val})$"
                    q_diff = 3.0 + _multiplication_weight(abs(a_val), abs(a_val)) * 2
                sol_str = comp
            else:  # resoudre f(x) = k
                if func == 'carre':
                    k = random.randint(1, 10)**2  # carré parfait
                    r = int(math.isqrt(k))
                    enonce_str = f"f(x) = x^2. \\text{{ Résoudre }} f(x) = {k}"
                    sol_str = f"x = {r} \\text{{ ou }} x = -{r}"
                    detail = f"$x^2 = {k} \\Longleftrightarrow x = \\sqrt{{{k}}} = {r}$ ou $x = -\\sqrt{{{k}}} = -{r}$"
                    q_diff = 2.5 + _sqrt_simplification_cost(k)
                elif func == 'inverse':
                    k_num = random.choice([1,-1]) * random.randint(1, 5)
                    k_den = random.randint(2, 6)
                    k = Rational(k_num, k_den)
                    enonce_str = f"f(x) = \\dfrac{{1}}{{x}}. \\text{{ Résoudre }} f(x) = {latex(k).replace(chr(92)+'frac',chr(92)+'dfrac')}"
                    sol_val = Rational(k_den, k_num)
                    sol_str = f"x = {latex(sol_val).replace(chr(92)+'frac',chr(92)+'dfrac')}"
                    detail = f"$\\dfrac{{1}}{{x}} = {latex(k).replace(chr(92)+'frac',chr(92)+'dfrac')} \\Longleftrightarrow x = {latex(sol_val).replace(chr(92)+'frac',chr(92)+'dfrac')}$"
                    q_diff = 3.0
                else:
                    k = random.randint(1, 10)
                    enonce_str = f"f(x) = \\sqrt{{x}}. \\text{{ Résoudre }} f(x) = {k}"
                    sol_str = f"x = {k**2}"
                    detail = f"$\\sqrt{{x}} = {k} \\Longleftrightarrow x = {k}^2 = {k**2}$ (avec $x \\geq 0$)"
                    q_diff = 2.0 + _multiplication_weight(k, k)

            et.append(enonce_str); st.append(sol_str); corriges.append(detail)
            total_diff += q_diff

        enonce = "\\noindent\\textbf{Exercice} -- Fonctions de référence.\n\\begin{enumerate}\n"
        for e in et: enonce += f"\\item ${e}$\n"
        enonce += "\\end{enumerate}\n"
        corrige = "\\begin{enumerate}\n"
        for d in corriges: corrige += f"\\item {d}\n"
        corrige += "\\end{enumerate}\n"
        corrige_succinct = _build_succinct_corrige(st)
        return {'enonce': enonce, 'corrige': corrige, 'corrige_succinct': corrige_succinct, 'qr_data': None,
                'difficulte': config.get('difficulte', 'Moyen'),
                'difficulte_raw': round(total_diff, 2),
                'qr_answers': [_plain(s) for s in st]}

# ╔═══════════════════════════════════════════════════════════════════════════════╗
# ║  Système de difficulté statistique                                           ║
# ╚═══════════════════════════════════════════════════════════════════════════════╝

_DIFFICULTY_STATS_FILE = os.path.join(os.path.dirname(__file__), "difficulty_stats.json")
_DIFFICULTY_STATS_CACHE = None
_DIFFICULTY_CACHE_FORMAT_VERSION = 3
_DIFFICULTY_ESTIMATOR_VERSION = 6  # v4: corrigé improvements  # Bumped: cognitive model
_DIFFICULTY_MIN_SIGMA = 1.0


def get_difficulty_stats_file_path() -> str:
    return _DIFFICULTY_STATS_FILE

def _empty_difficulty_cache() -> dict:
    return {'_meta': {'format_version': _DIFFICULTY_CACHE_FORMAT_VERSION, 'estimator_version': _DIFFICULTY_ESTIMATOR_VERSION, 'updated_at': None}, 'stats': {}}

def _extract_stats_map(raw_cache) -> dict:
    if isinstance(raw_cache, dict) and 'stats' in raw_cache and isinstance(raw_cache['stats'], dict):
        meta = raw_cache.get('_meta') or {}
        return {'_meta': {'format_version': meta.get('format_version', _DIFFICULTY_CACHE_FORMAT_VERSION), 'estimator_version': meta.get('estimator_version', 1), 'updated_at': meta.get('updated_at')}, 'stats': dict(raw_cache['stats'])}
    if isinstance(raw_cache, dict):
        return {'_meta': {'format_version': 1, 'estimator_version': 1, 'updated_at': None}, 'stats': dict(raw_cache)}
    return _empty_difficulty_cache()

def _load_difficulty_stats_cache():
    global _DIFFICULTY_STATS_CACHE
    if _DIFFICULTY_STATS_CACHE is None:
        if os.path.exists(_DIFFICULTY_STATS_FILE):
            try:
                with open(_DIFFICULTY_STATS_FILE, 'r', encoding='utf-8') as fh:
                    _DIFFICULTY_STATS_CACHE = _extract_stats_map(json.load(fh))
            except Exception:
                _DIFFICULTY_STATS_CACHE = _empty_difficulty_cache()
        else:
            _DIFFICULTY_STATS_CACHE = _empty_difficulty_cache()
    return _DIFFICULTY_STATS_CACHE

def _stats_entries() -> dict:
    return _load_difficulty_stats_cache()['stats']

def clear_difficulty_stats_cache(save: bool = True):
    global _DIFFICULTY_STATS_CACHE
    _DIFFICULTY_STATS_CACHE = _empty_difficulty_cache()
    if save: _save_difficulty_stats_cache()

def _save_difficulty_stats_cache():
    cache = _load_difficulty_stats_cache()
    cache['_meta']['format_version'] = _DIFFICULTY_CACHE_FORMAT_VERSION
    cache['_meta']['estimator_version'] = _DIFFICULTY_ESTIMATOR_VERSION
    cache['_meta']['updated_at'] = datetime.datetime.now().isoformat(timespec='seconds')
    with open(_DIFFICULTY_STATS_FILE, 'w', encoding='utf-8') as fh:
        json.dump(cache, fh, ensure_ascii=False, indent=2, sort_keys=True)

def _normalize_config_for_stats(config: dict) -> dict:
    cleaned = {}
    for key, value in sorted((config or {}).items()):
        if key in {'difficulte'} or str(key).startswith('_'): continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            cleaned[str(key)] = value
        else: cleaned[str(key)] = str(value)
    return cleaned

def build_difficulty_signature(generator_cls, config: dict) -> str:
    payload = {
        'generator_id': generator_cls.id,
        'profile_version': getattr(generator_cls, 'difficulty_profile_version', 1),
        'estimator_version': _DIFFICULTY_ESTIMATOR_VERSION,
        'config': _normalize_config_for_stats(config),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Estimateur de difficulté — refonte v3 : priorité au score cognitif
# ═══════════════════════════════════════════════════════════════════════════════

def _score_integer_complexity(n: int) -> float:
    n = abs(int(n))
    if n <= 1: return 0.0
    score = 0.04 + math.log10(max(n, 1)) * 0.18
    if n > 12: score += 0.20 * math.log2(n / 12.0 + 1.0)
    if n >= 100: score += 0.28 * math.log10(n / 100.0 + 1.0)
    return score

def _max_parenthesis_depth(text: str) -> int:
    depth = 0; max_depth = 0
    for ch in text:
        if ch == '(': depth += 1; max_depth = max(max_depth, depth)
        elif ch == ')': depth = max(0, depth - 1)
    return max_depth

def _count_binary_minus(text: str) -> int:
    return len(re.findall(r'(?<=[0-9xX\}\)])\s*-\s*(?=[0-9xX\(\{])', text))

def _frac_nesting_bonus(text: str) -> tuple:
    pattern = re.compile(r'\\d?frac\s*\{')
    matches = list(pattern.finditer(text))
    if not matches: return 0, 0
    starts = {m.start() for m in matches}
    depth = 0; frac_depth = 0; max_frac_depth = 0; i = 0
    while i < len(text):
        if i in starts: frac_depth += 1; max_frac_depth = max(max_frac_depth, frac_depth)
        ch = text[i]
        if ch == '{': depth += 1
        elif ch == '}':
            depth = max(0, depth - 1)
            if frac_depth > depth: frac_depth = max(depth, 0)
        i += 1
    return len(matches), max_frac_depth


def _estimate_text_fallback(text: str) -> float:
    """Fallback textuel léger pour les générateurs sans score cognitif natif."""
    if not text or not str(text).strip(): return 0.0
    text = str(text)
    score = 0.0
    nb_items = len(re.findall(r'\\item', text))
    score += 1.1 * nb_items
    nb_frac, frac_depth = _frac_nesting_bonus(text)
    score += 0.95 * nb_frac
    if frac_depth > 1: score += 0.55 * (frac_depth - 1) * max(1, nb_frac)
    nb_sqrt = len(re.findall(r'\\sqrt\s*\{', text))
    score += 0.80 * nb_sqrt
    nb_pow = len(re.findall(r'\^\{?|\*\*', text))
    score += 0.50 * nb_pow
    nb_mult = len(re.findall(r'\\times|\\cdot', text))
    score += 0.32 * nb_mult
    nb_vars = len(re.findall(r'(?<![A-Za-z])x(?![A-Za-z])', text))
    score += 0.12 * nb_vars
    return score


def estimate_raw_difficulty_from_result(result: dict, level: str | None = None,
                                        generator_id: str | None = None,
                                        config: dict | None = None) -> float:
    """Estimateur de difficulté — v3 cognitive.

    Priorité 1 : si le générateur a calculé un score cognitif (clé difficulte_raw),
    on l'utilise directement. C'est le modèle fiable.

    Priorité 2 : analyse textuelle en fallback (pour les générateurs pas encore portés).
    """
    # ── Priorité 1 : score cognitif natif ────────────────────────────────
    if 'difficulte_raw' in result and result['difficulte_raw'] is not None:
        raw = float(result['difficulte_raw'])
        result['_difficulty_components'] = {'source': 'cognitive', 'total': round(raw, 3)}
        return raw

    # ── Priorité 2 : fallback textuel ────────────────────────────────────
    enonce = str(result.get('enonce', '') or '')
    corrige = str(result.get('corrige', '') or '')
    if not enonce.strip() and not corrige.strip():
        return 0.0

    score_e = _estimate_text_fallback(enonce)
    score_c = _estimate_text_fallback(corrige)
    total = 0.65 * score_e + 0.35 * score_c

    result['_difficulty_components'] = {
        'source': 'text_fallback',
        'enonce': round(score_e, 3),
        'corrige': round(score_c, 3),
        'total': round(total, 3),
    }
    return round(total, 3)


def get_or_compute_difficulty_stats(generator_cls, config: dict, samples: int = 80, force: bool = False) -> dict:
    cache = _load_difficulty_stats_cache()
    entries = _stats_entries()
    signature = build_difficulty_signature(generator_cls, config)
    entry = entries.get(signature)
    requested_samples = max(10, int(samples))
    if force: entry = None
    if entry and entry.get('n', 0) >= requested_samples:
        # Invalidate if estimator version changed
        if entry.get('estimator_version', 1) != _DIFFICULTY_ESTIMATOR_VERSION:
            entry = None
    if entry and entry.get('n', 0) >= requested_samples:
        return entry

    generator = generator_cls()
    level = getattr(generator_cls, 'niveau', None)
    can_increment = bool(entry) and all(k in entry for k in ('raw_sum', 'raw_sum_sq', 'n', 'min', 'max'))
    # Force fresh computation if estimator version changed
    if can_increment and entry.get('estimator_version', 1) != _DIFFICULTY_ESTIMATOR_VERSION:
        can_increment = False
    if can_increment:
        n = int(entry.get('n', 0)); raw_sum = float(entry.get('raw_sum', 0.0))
        raw_sum_sq = float(entry.get('raw_sum_sq', 0.0))
        min_val = float(entry.get('min', 0.0)); max_val = float(entry.get('max', 0.0))
        extra_needed = max(0, requested_samples - n)
    else:
        n = 0; raw_sum = 0.0; raw_sum_sq = 0.0; min_val = None; max_val = None
        extra_needed = requested_samples

    for _ in range(extra_needed):
        result = generator.generate(dict(config or {}))
        value = estimate_raw_difficulty_from_result(result, level=level, generator_id=generator_cls.id, config=config)
        n += 1; raw_sum += value; raw_sum_sq += value * value
        min_val = value if min_val is None else min(min_val, value)
        max_val = value if max_val is None else max(max_val, value)

    if n <= 0: mean = 0.0; sigma = 0.0
    else:
        mean = raw_sum / n
        variance = max(0.0, (raw_sum_sq / n) - (mean * mean))
        sigma = variance ** 0.5

    entry = {
        'generator_id': generator_cls.id, 'generator_name': generator_cls.name,
        'niveau': level, 'estimator_version': _DIFFICULTY_ESTIMATOR_VERSION,
        'config': _normalize_config_for_stats(config),
        'n': n, 'mean': round(mean, 6), 'sigma': round(sigma, 6),
        'sigma_effective': round(max(sigma, _DIFFICULTY_MIN_SIGMA), 6),
        'min': round(min_val if min_val is not None else 0.0, 6),
        'max': round(max_val if max_val is not None else 0.0, 6),
        'raw_sum': round(raw_sum, 6), 'raw_sum_sq': round(raw_sum_sq, 6),
        'updated_at': datetime.datetime.now().isoformat(timespec='seconds'),
    }
    entries[signature] = entry
    _save_difficulty_stats_cache()
    return entry


def compute_difficulty_zscore(generator_cls, config: dict, result: dict, calibration_samples: int = 80):
    level = getattr(generator_cls, 'niveau', None)
    raw = estimate_raw_difficulty_from_result(result, level=level, generator_id=generator_cls.id, config=config)
    stats = get_or_compute_difficulty_stats(generator_cls, config, samples=calibration_samples)
    sigma = max(float(stats.get('sigma') or 0.0), _DIFFICULTY_MIN_SIGMA)
    z = 0.0 if sigma < 1e-9 else (raw - float(stats.get('mean', 0.0))) / sigma
    return raw, z, stats


def generate_with_difficulty_filter(generator_cls, config: dict, z_center: float = 0.0,
                                    z_tolerance: float | None = None,
                                    calibration_samples: int = 80,
                                    max_attempts: int = 40) -> dict:
    generator = generator_cls()
    center = float(z_center)
    tolerance = None if z_tolerance is None else max(0.0, float(z_tolerance))
    chosen = None; best = None

    for attempt in range(1, max(1, int(max_attempts)) + 1):
        result = generator.generate(dict(config or {}))
        raw, z, stats = compute_difficulty_zscore(generator_cls, config, result, calibration_samples=calibration_samples)
        result['_difficulty_raw'] = raw
        result['_difficulty_zscore'] = z
        result['_difficulty_stats'] = stats
        result['_difficulty_attempt'] = attempt
        result['_difficulty_target_center'] = center
        result['_difficulty_target_tolerance'] = tolerance
        distance = abs(z - center)
        result['_difficulty_target_distance'] = distance
        if tolerance is None or distance <= tolerance:
            chosen = result; break
        if best is None or distance < best.get('_difficulty_target_distance', 10**9):
            best = result

    if chosen is None:
        chosen = best
        chosen['_difficulty_filter_fallback'] = True
    return chosen


# ═══════════════════════════════════════════════════════════════════════════════
# Utilitaires
# ═══════════════════════════════════════════════════════════════════════════════

def get_generators_by_level():
    result={}
    for gc in REGISTRY.values():
        result.setdefault(gc.niveau,[]).append(gc)
    order={'5e':0,'4e':1,'3e':2,'2nde':3,'1re':4,'Tle':5}
    for niv in result: result[niv].sort(key=lambda g:g.name)
    return dict(sorted(result.items(),key=lambda x:order.get(x[0],99)))

def list_all_generators():
    for gid,gc in REGISTRY.items():
        print(f"[{gc.niveau}] {gc.name} ({gid}): {gc.description}")
