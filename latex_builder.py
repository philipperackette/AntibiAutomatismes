"""
Construction du document LaTeX complet.
Assemble les exercices générés en un fichier .tex prêt pour XeLaTeX.
v4 — Double mode corrigé (complet/succinct), corrections pédagogiques, numérotation corrigés, espacement, options séparées
"""

import datetime

from generators import generate_with_difficulty_filter


def build_preambule(titre: str, classe: str, is_controle: bool) -> str:
    """Construit le préambule LaTeX."""
    doc_type = "Contrôle" if is_controle else "Entraînement"
    header_left = f"{doc_type} : {titre}"

    pre = r"\documentclass[12pt,a4paper,french]{article}" + "\n"
    pre += r"\usepackage[utf8]{inputenc}" + "\n"
    pre += r"\usepackage{amsmath,lmodern,babel,geometry}" + "\n"
    pre += r"\usepackage{pgf,tikz}" + "\n"
    pre += r"\usepackage{tkz-tab}" + "\n"
    pre += r"\usepackage{fancyhdr}" + "\n"
    pre += r"\usepackage{qrcode}" + "\n"
    pre += r"\usepackage{enumitem}" + "\n"
    pre += r"\usepackage[useregional]{datetime2}" + "\n"
    pre += r"\geometry{top=2.8cm, left=2cm, right=2cm, bottom=2cm}" + "\n"
    pre += r"\pagestyle{fancy}" + "\n"
    pre += f"\\fancyhead[L]{{{header_left}}}\n"
    pre += f"\\fancyhead[R]{{{classe}}}\n"
    pre += r"\fancyfoot[C]{\tiny{Date de création : \DTMnow}}" + "\n"
    pre += r"\renewcommand{\labelenumi}{\arabic{enumi})}" + "\n"
    pre += r"\setlist[enumerate]{topsep=0.2em,itemsep=0.2em,parsep=0pt,partopsep=0pt}" + "\n"
    pre += r"\setlength{\headheight}{15pt}" + "\n"
    pre += r"\begin{document}" + "\n"
    return pre


def build_sujet_header(n_sujet: int, include_nom: bool = False, include_consigne: bool = False, consigne_texte: str = "") -> str:
    """En-tête d'un sujet individuel."""
    s = "\\begin{center}\n"
    s += f"\\textbf{{Sujet numéro {n_sujet}}}\n"
    s += "\\\\(à rendre avec la copie)\n"
    s += "\\end{center}\n\n"
    if include_nom:
        s += "Prénom, nom : ...............................................\\\\\n"
        s += "\\bigskip\n"
    if include_consigne and consigne_texte.strip():
        s += "\\begin{center}\n"
        s += f"\\textbf{{{consigne_texte.strip()}}}\n"
        s += "\\end{center}\n"
        s += "\\bigskip\n"
    s += "\n"
    return s


def build_corrige_header(n_sujet: int) -> str:
    """En-tête de page de corrigé."""
    s = "\\begin{center}\n"
    s += f"\\textbf{{Corrigé numéro {n_sujet}}}\\\\\n"
    s += "\\end{center}\n\n"
    return s


def build_qr_block(qr_data: str) -> str:
    """Bloc QR code inline en bas du sujet (pas via fancyfoot pour fiabilité)."""
    s = "\\vfill\n"
    s += "\\begin{flushright}\n"
    s += "\\qrset{height=1.5cm}\n"
    s += "\\qrset{level=M}\n"
    s += "\\qrcode{" + qr_data + "}\n"
    s += "\\end{flushright}\n"
    return s


def build_document(
    titre: str,
    classe: str,
    is_controle: bool,
    nb_sujets: int,
    exercises: list,
    include_corrige: bool = True,
    corrige_position: str = "apres_sujet",
    corrige_mode: str = "complet",  # 'complet' or 'succinct'
    include_qr: bool = True,
    include_nom: bool = False,
    include_consigne: bool = False,
    consigne_texte: str = "",
    difficulty_filter_enabled: bool = False,
    difficulty_z_center: float = 0.0,
    difficulty_z_tolerance: float = 0.75,
    difficulty_calibration_samples: int = 80,
    difficulty_max_attempts: int = 40,
) -> str:
    """
    Construit le document LaTeX complet.

    Args:
        titre: Titre de l'évaluation
        classe: Nom de la classe
        is_controle: True pour contrôle, False pour entraînement
        nb_sujets: Nombre de sujets à générer
        exercises: Liste de dicts {'generator': ExerciseGenerator, 'config': dict}
        include_corrige: Inclure les corrigés en clair
        corrige_position: Position des corrigés ("apres_sujet" ou "a_la_fin")
        corrige_mode: Mode du corrigé ("complet" pour détaillé, "succinct" pour réponses seules)
        include_qr: Inclure des QR codes avec les solutions sur les sujets
        difficulty_filter_enabled: active le filtrage statistique par z-score
        difficulty_z_center: centre visé en unités d'écart-type
        difficulty_z_tolerance: demi-largeur de la plage de tolérance en unités d'écart-type

    Returns:
        str: Document LaTeX complet
    """
    preambule = build_preambule(titre, classe, is_controle)
    body = ""
    all_corriges = ""

    for n in range(1, nb_sujets + 1):
        body += build_sujet_header(n, include_nom=include_nom, include_consigne=include_consigne, consigne_texte=consigne_texte)

        sujet_corrige = ""
        sujet_qr_parts = []
        has_qr = False

        for i, ex_spec in enumerate(exercises):
            ex_num = i + 1
            gen_class = ex_spec['generator']
            gen_config = dict(ex_spec.get('config', {}))

            if difficulty_filter_enabled:
                result = generate_with_difficulty_filter(
                    gen_class,
                    gen_config,
                    z_center=difficulty_z_center,
                    z_tolerance=difficulty_z_tolerance,
                    calibration_samples=difficulty_calibration_samples,
                    max_attempts=difficulty_max_attempts,
                )
            else:
                generator = gen_class()
                result = generator.generate(gen_config)

            enonce = result['enonce']

            # ── Numérotation chronologique ──────────────────────────────────
            # Replace first occurrence of \textbf{Exercice} with \textbf{Exercice N}
            enonce = enonce.replace(
                '\\textbf{Exercice}',
                f'\\textbf{{Exercice {ex_num}}}',
                1
            )

            bareme = ex_spec.get('bareme', None)
            if bareme:
                enonce = enonce.replace(
                    f"\\textbf{{Exercice {ex_num}}}",
                    f"\\textbf{{Exercice {ex_num}}} ({bareme})",
                    1
                )

            body += enonce
            body += "\\bigskip\n\n"

            # Collecter le corrigé (complet ou succinct)
            corrige_key = 'corrige_succinct' if corrige_mode == 'succinct' and result.get('corrige_succinct') else 'corrige'
            if result.get(corrige_key):
                corrige = result[corrige_key].strip()
                sujet_corrige += f"\\noindent\\textbf{{Exercice {ex_num}}}\\par\n"
                sujet_corrige += "\\smallskip\n"
                sujet_corrige += corrige + "\n"
                sujet_corrige += "\\medskip\n\n"

            # ── QR : réponses finales ────────────────────────────────────────
            qr_answers = result.get('qr_answers') or []
            if qr_answers:
                has_qr = True
                answers_str = f"Ex{ex_num}: " + " | ".join(str(a) for a in qr_answers)
                sujet_qr_parts.append(answers_str)
            elif result.get('qr_data'):
                # legacy qr_data (Thalès)
                has_qr = True
                sujet_qr_parts.append(f"Ex{ex_num}: {result['qr_data']}")

        # QR code inline en bas du sujet (plus fiable que fancyfoot)
        if include_qr and has_qr:
            qr_data = "  //  ".join(sujet_qr_parts)
            body += build_qr_block(qr_data)

        body += "\\newpage\n"

        # Corrigé
        if include_corrige and sujet_corrige:
            corrige_page = build_corrige_header(n)
            corrige_page += sujet_corrige
            corrige_page += "\\newpage\n"

            if corrige_position == "apres_sujet":
                body += corrige_page
            else:
                all_corriges += corrige_page

    # Ajouter tous les corrigés à la fin
    if corrige_position == "a_la_fin" and all_corriges:
        body += "\\newpage\n"
        body += "\\begin{center}\n\\textbf{\\Large CORRIGÉS}\\end{center}\n\\newpage\n"
        body += all_corriges

    return preambule + body + "\\end{document}\n"
