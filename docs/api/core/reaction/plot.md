---
tags:
    - Api
    - Reaction
---

# Reaction.plot

`#!python plot(ax=None)`

Plots the rate coefficient as a function of gas temperature on a log-log scale. The temperature axis spans \[`tmin`, `tmax`\]; when either is `None`, defaults of 2.73 K and 1e6 K are used respectively.

**Parameters**

**ax** : _matplotlib.axes.Axes or None, optional_
: Axes to plot on. If `None`, creates a new figure and displays it immediately.
