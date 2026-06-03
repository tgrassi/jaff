---
tags:
    - Api
    - Reaction
---

# Reaction.plot_rate_coefficient

`#!python plot_rate_coefficient(fig=None, ax=None, title=None, grid=True, show=True, save=False, filename="")`

Plots the rate coefficient as a function of gas temperature on a log-log scale, using the styled `jaff.plotting.Plotter` house style. The temperature axis spans \[`tmin`, `tmax`\]; when either is `None`, defaults of 2.73 K and 1e6 K are used respectively.

**Parameters**

**fig, ax** : _matplotlib.figure.Figure / matplotlib.axes.Axes or None, optional_
: Existing figure/axes to draw on. Both are created if `None`.

**title** : _str or None, optional_
: Plot title. Defaults to the LaTeX reaction equation.

**grid** : _bool, optional_
: Draw a grid. Default `True`.

**show** : _bool, optional_
: Display the figure. Default `True`.

**save** : _bool, optional_
: Save to `filename` (format inferred from the extension). Default `False`.

**filename** : _str, optional_
: Output path. Defaults to `"<reaction>_rate.png"`.

**Returns**

_tuple\[matplotlib.figure.Figure, matplotlib.axes.Axes\]_
: The figure and axes drawn on.
