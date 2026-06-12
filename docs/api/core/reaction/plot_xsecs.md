---
tags:
    - Api
    - Reaction
---

# plot_xsecs

`#!python plot_xsecs(processes="all", layout="overlay", fig=None, ax=None, energy_unit="eV", xsec_unit="Mb", energy_log=True, xsecs_log=True, title=None, grid=True, show=True, save=False, filename="")`

Plots photo cross sections against photon energy or wavelength. Drawing, unit conversion, and labelling are delegated to `jaff.plotting.Plotter.plot_xsec`. Does nothing (logs a message and returns `None`) if `xsecs_dict` is `None` or no requested process has data. Cross-section data are stored as photon energies in eV and cross sections in cm²; both are converted to the requested units before plotting.

**Parameters**

**processes** : _str or list\[str\] or None, optional_
: Which cross-section processes to draw. `"all"` (default) or `None` plots every process that has data; a single key or a list of keys selects a subset. Valid keys: `"photo_absorption"`, `"photo_dissociation"`, `"photo_ionization"`. An invalid key raises `KeyError`.

**layout** : _str, optional_
: `"overlay"` (default) draws all processes on one axes; `"subplots"` gives each process its own stacked panel.

**fig, ax** : _matplotlib.figure.Figure / matplotlib.axes.Axes or None, optional_
: Existing figure/axes to draw on (overlay layout only). Created if `None`.

**energy_unit** : _str, optional_
: Horizontal-axis unit: `"eV"` (default), `"erg"`, `"nm"`, or `"um"`.

**xsec_unit** : _str, optional_
: Cross-section unit: `"Mb"` (default), `"cm^2"`, or `"barn"`.

**energy_log** : _bool, optional_
: Log-scale the energy axis. Default `True`.

**xsecs_log** : _bool, optional_
: Log-scale the cross-section axis. Default `True`.

**title** : _str or None, optional_
: Plot title. Defaults to the LaTeX reaction equation.

**grid** : _bool, optional_
: Draw a grid. Default `True`.

**show** : _bool, optional_
: Display the figure. Default `True`.

**save** : _bool, optional_
: Save to `filename` (format inferred from the extension). Default `False`.

**filename** : _str, optional_
: Output path. Defaults to `"<reaction>_<process>.png"`.

**Returns**

_tuple\[matplotlib.figure.Figure, matplotlib.axes.Axes\] or None_
: The figure and axes (overlay) or array of axes (subplots); `None` when there is no data to plot.
