---
tags:
    - Api
    - Reaction
---

# get_latex

`#!python get_latex()`

Formats the reaction as a LaTeX math string with reactants and products joined by `\rightarrow`, wrapped in `$...$` for inline rendering. Species are formatted using their individual `Specie.latex` representations.

**Returns**

_str_
: Inline-math LaTeX string representing the reaction, e.g. `"$\mathrm{H} + \mathrm{O} \rightarrow \mathrm{OH}$"`.
