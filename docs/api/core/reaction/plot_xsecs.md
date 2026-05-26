---
tags:
    - Api
    - Reaction
---

# plot_xsecs

`#!python plot_xsecs(ax=None, energy_unit="eV", energy_log=True, xsecs_log=True)`

Plots photo-ionisation cross sections against photon energy or wavelength. Does nothing (logs a message) if `xsecs_dict` is `None`. Cross-section data are stored in CGS units: energies in erg, cross-sections in cm². Wavelength conversions use `c` and `h` from `jaff.physics.constants.cgs`.

**Parameters**

**ax** : _matplotlib.axes.Axes or None, optional_
: Axes to plot on. If `None`, creates a new figure.

**energy_unit** : _str, optional_
: X-axis unit: `"eV"`, `"erg"`, `"nm"`, or `"um"`. Default `"eV"`.

**energy_log** : _bool, optional_
: Log-scale x-axis. Default `True`.

**xsecs_log** : _bool, optional_
: Log-scale y-axis. Default `True`.
