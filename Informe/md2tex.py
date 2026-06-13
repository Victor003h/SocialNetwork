#!/usr/bin/env python3
"""Transcribe informe_final.md -> informe_final.tex (subconjunto de Markdown usado en el informe)."""
import pathlib
import re

HERE = pathlib.Path(__file__).parent
md = (HERE / "informe_final.md").read_text(encoding="utf-8")


def reflow(raw_lines):
    """Une líneas suaves (soft-wrap) en una sola línea lógica por párrafo / ítem,
    para que **negrita** o _énfasis_ que cruzan un salto se procesen completos.
    Respeta encabezados, reglas, tablas, listas y bloques de código."""
    out, buf, in_fence = [], None, False

    def flush():
        nonlocal buf
        if buf is not None:
            out.append(buf)
            buf = None

    for line in raw_lines:
        s = line.strip()
        if in_fence:
            out.append(line)
            if s.startswith("```"):
                in_fence = False
            continue
        if s.startswith("```"):
            flush()
            out.append(line)
            in_fence = True
            continue
        is_struct = s == "" or s.startswith("#") or s == "---" or s.startswith("|")
        is_item = bool(re.match(r"^\s*(-|\d+\.)\s+", line))
        if is_struct:
            flush()
            out.append(line)
        elif is_item:
            flush()
            buf = line.rstrip()
        else:  # texto de continuación
            buf = s if buf is None else buf.rstrip() + " " + s
    flush()
    return out


lines = reflow(md.split("\n"))

SPECIAL = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def esc(text: str) -> str:
    out = []
    for ch in text:
        out.append(SPECIAL.get(ch, ch))
    return "".join(out)


CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITAL_RE = re.compile(r"(?<![A-Za-z0-9])_([^_]+)_(?![A-Za-z0-9])")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline(text: str) -> str:
    """Convierte formato inline a LaTeX. Marca énfasis y código ANTES de escapar,
    usando centinelas que el escape no toca, y los materializa al final."""
    spans, links = [], []

    def stash_code(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    text = CODE_RE.sub(stash_code, text)  # 1) proteger código

    def stash_link(m):
        links.append((m.group(2), m.group(1)))
        return f"\x06{len(links) - 1}\x06"

    text = LINK_RE.sub(stash_link, text)  # 2) proteger links

    # 3) énfasis -> centinelas (texto interno aún por escapar)
    text = BOLD_RE.sub(lambda m: f"\x02{m.group(1)}\x03", text)
    text = ITAL_RE.sub(lambda m: f"\x04{m.group(1)}\x05", text)

    text = esc(text)  # 4) escapar especiales

    # 5) materializar centinelas
    text = (text.replace("\x02", r"\textbf{").replace("\x03", "}")
                .replace("\x04", r"\emph{").replace("\x05", "}"))

    def restore_link(m):
        url, label = links[int(m.group(1))]
        url = url.replace("%", r"\%").replace("#", r"\#").replace("_", r"\_")
        return r"\href{%s}{%s}" % (url, esc(label))

    text = re.sub(r"\x06(\d+)\x06", restore_link, text)

    def restore_code(m):
        body = esc(spans[int(m.group(1))])
        # Permitir cortes de línea dentro de identificadores largos.
        body = re.sub(r"(\\_|[./:])", r"\1\\allowbreak{}", body)
        return r"\texttt{%s}" % body

    text = re.sub(r"\x00(\d+)\x00", restore_code, text)
    return text


out = []
i = 0
in_list = None  # 'itemize' | 'enumerate' | None


def close_list():
    global in_list
    if in_list:
        out.append(f"\\end{{{in_list}}}")
        in_list = None


while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # Bloque de código cercado
    if stripped.startswith("```"):
        close_list()
        i += 1
        buf = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            buf.append(lines[i])
            i += 1
        i += 1
        out.append(r"\begin{lstlisting}")
        out.extend(buf)
        out.append(r"\end{lstlisting}")
        continue

    # Tabla
    if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
        close_list()
        header = [c.strip() for c in stripped.strip("|").split("|")]
        ncol = len(header)
        rows = []
        i += 2
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
            i += 1
        colspec = "|" + "|".join([r">{\raggedright\arraybackslash}p{%.2f\textwidth}" % (0.92 / ncol)] * ncol) + "|"
        out.append(r"\begin{center}\footnotesize")
        out.append(r"\begin{tabular}{%s}" % colspec)
        out.append(r"\hline")
        out.append(" & ".join(r"\textbf{%s}" % inline(h) for h in header) + r" \\ \hline")
        for r in rows:
            r = (r + [""] * ncol)[:ncol]
            out.append(" & ".join(inline(c) for c in r) + r" \\ \hline")
        out.append(r"\end{tabular}")
        out.append(r"\end{center}")
        continue

    # Encabezados
    if stripped.startswith("# "):
        close_list()
        out.append(r"\section*{%s}" % inline(stripped[2:]))
        i += 1
        continue
    if stripped.startswith("## "):
        close_list()
        out.append(r"\section{%s}" % inline(stripped[3:]))
        i += 1
        continue
    if stripped.startswith("### "):
        close_list()
        out.append(r"\subsection{%s}" % inline(stripped[4:]))
        i += 1
        continue

    # Regla horizontal
    if stripped == "---":
        close_list()
        out.append(r"\vspace{2pt}\noindent\rule{\textwidth}{0.4pt}\vspace{2pt}")
        i += 1
        continue

    # Listas
    m_ul = re.match(r"^(\s*)-\s+(.*)$", line)
    m_ol = re.match(r"^(\s*)\d+\.\s+(.*)$", line)
    if m_ul or m_ol:
        want = "itemize" if m_ul else "enumerate"
        content = (m_ul or m_ol).group(2)
        if in_list != want:
            close_list()
            out.append(f"\\begin{{{want}}}")
            in_list = want
        out.append(r"\item %s" % inline(content))
        i += 1
        continue

    # Línea en blanco
    if stripped == "":
        close_list()
        out.append("")
        i += 1
        continue

    # Continuación de un ítem de lista hard-wrapped (lazy continuation)
    if in_list and out:
        out[-1] = out[-1] + " " + inline(stripped)
        i += 1
        continue

    # Párrafo normal
    close_list()
    out.append(inline(stripped))
    i += 1

close_list()
body = "\n".join(out)

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setmonofont{DejaVu Sans Mono}[Scale=0.85]
\usepackage{polyglossia}
\setdefaultlanguage{spanish}
\usepackage[a4paper,margin=2cm]{geometry}
\usepackage{array}
\usepackage{xcolor}
\usepackage{listings}
\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
\usepackage{enumitem}
\setlist{nosep,leftmargin=1.3em,topsep=2pt}
\definecolor{codebg}{gray}{0.96}
\lstset{
  basicstyle=\ttfamily\small,
  backgroundcolor=\color{codebg},
  frame=single, rulecolor=\color{gray!40},
  breaklines=true, columns=fullflexible,
  xleftmargin=4pt, framexleftmargin=4pt,
  literate={á}{{\'a}}1 {é}{{\'e}}1 {í}{{\'i}}1 {ó}{{\'o}}1 {ú}{{\'u}}1 {ñ}{{\~n}}1 {§}{{\S}}1
}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\usepackage{titlesec}
\titlespacing*{\section}{0pt}{12pt}{4pt}
\titlespacing*{\subsection}{0pt}{8pt}{3pt}
\begin{document}
"""

tex = PREAMBLE + body + "\n\\end{document}\n"
(HERE / "informe_final.tex").write_text(tex, encoding="utf-8")
print("informe_final.tex generado")
