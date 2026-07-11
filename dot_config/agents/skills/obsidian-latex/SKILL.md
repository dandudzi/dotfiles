---
name: obsidian-latex
description: Write and revise MathJax-compatible LaTeX notation in Obsidian Markdown. Use for inline math, display equations, aligned formulas, symbols, delimiters, or migrating mathematical notes into Obsidian.
---

# Obsidian LaTeX

Use `$...$` for inline notation:

```markdown
Euler's identity is $e^{i\pi}+1=0$.
```

Use `$$...$$` for display notation:

```markdown
$$
\begin{aligned}
f(x) &= x^2 + 2x + 1 \\
     &= (x+1)^2
\end{aligned}
$$
```

Obsidian renders TeX notation through MathJax; it is not a full LaTeX document processor. Preserve existing delimiters, macros, and backslashes. Do not add document preambles, packages, filesystem includes, or compilation steps.

Verify complex formulas in Obsidian Reading view. Escape literal currency dollar signs as `\$` when they could be parsed as math.

## Discover more

Consult current MathJax TeX-input documentation for supported commands and extensions. Check the vault's existing notation conventions before introducing a new macro or delimiter style.
