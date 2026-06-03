from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from cycler import cycler

if TYPE_CHECKING:
    from ..physics._typing import XsecsProps


class Plotter:
    """Publication-quality matplotlib wrapper with a clean, seaborn-like style.

    Instantiating applies the house ``rcParams`` globally.  Any keyword
    arguments override individual ``rcParams`` entries, e.g.
    ``Plotter(**{"font.size": 13})``.
    """

    #: Display labels for the three cross-section processes.
    _PROC_LABELS: dict[str, str] = {
        "photo_absorption": "Photoabsorption",
        "photo_dissociation": "Photodissociation",
        "photo_ionization": "Photoionization",
    }

    _PALETTE: list[str] = [
        "#4C72B0",
        "#DD8452",
        "#55A868",
        "#C44E52",
        "#8172B3",
        "#937860",
        "#DA8BC3",
        "#8C8C8C",
        "#CCB974",
        "#64B5CD",
    ]

    _RASTER: frozenset[str] = frozenset({"png", "jpg", "jpeg", "tif", "tiff"})

    _UNIT_TEX: dict[str, str] = {
        "cm^2": r"cm$^2$",
        "cm2": r"cm$^2$",
        "Mb": "Mb",
        "barn": "barn",
        "eV": "eV",
        "erg": "erg",
        "nm": "nm",
        "um": r"$\mu$m",
    }

    _ENERGY_LABELS: dict[str, str] = {
        "eV": "Photon energy (eV)",
        "erg": "Photon energy (erg)",
        "nm": "Wavelength (nm)",
        "um": r"Wavelength ($\mu$m)",
    }

    _RC_PARAMS: dict[str, Any] = {
        # Figure.
        "figure.figsize": (6.4, 4.0),
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        # Fonts -- sans-serif body, mathtext for math.
        "font.family": "sans-serif",
        "font.size": 11,
        "mathtext.fontset": "dejavusans",
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        # Lines + colour cycle.
        "lines.linewidth": 2.0,
        "lines.markersize": 5,
        "axes.prop_cycle": cycler(color=_PALETTE),
        # Spines -- full box (all four sides drawn).
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.linewidth": 0.9,
        "axes.edgecolor": "#333333",
        # Grid.
        "axes.grid": True,
        "grid.color": "#B0B0B0",
        "grid.linestyle": "-",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.35,
        "axes.axisbelow": True,
        # Ticks.
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 4,
        "ytick.major.size": 4,
        # Legend.
        "legend.frameon": False,
        "legend.loc": "best",
    }

    def __init__(self, **kwargs: Any) -> None:
        mpl.rcParams.update({**self._RC_PARAMS, **kwargs})

    def __fmt_unit(self, unit: str) -> str:
        """Render a unit string with mathtext superscripts where known."""

        return self._UNIT_TEX.get(unit, unit)

    def __energy_label(self, unit: str) -> str:
        """Axis label for a photon energy/wavelength *unit*."""

        return self._ENERGY_LABELS.get(unit, f"Photon energy ({self.__fmt_unit(unit)})")

    def __xsec_label(self, unit: str) -> str:
        """Axis label for a cross-section *unit*."""

        return rf"Cross section $\sigma$ ({self.__fmt_unit(unit)})"

    def __finish(
        self,
        fig: plt.Figure,
        show: bool,
        save: bool,
        filename: str,
        dpi: int = 300,
    ) -> None:
        """Lay out, optionally save (format from extension), optionally show."""
        fig.tight_layout()

        # Save before show: plt.show() may close/clear the figure.
        if save:
            ext = Path(filename).suffix.lower().lstrip(".")
            kw: dict[str, Any] = {"bbox_inches": "tight"}
            if ext in self._RASTER:
                kw["dpi"] = dpi
            fig.savefig(filename, **kw)

        if show:
            plt.show()

    def plot(
        self,
        x: list | float | np.ndarray,
        y: list | float | np.ndarray,
        fig: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        xlabel: str = "",
        ylabel: str = "",
        xscale: str = "linear",
        yscale: str = "linear",
        title: str = "",
        label: str = "",
        grid: bool = True,
        show: bool = True,
        save: bool = False,
        filename: str = "plot.png",
        **plot_kw: Any,
    ) -> tuple[plt.Figure, plt.Axes]:
        """Generic line plot.

        Parameters
        ----------
        x, y
            Data to plot.
        fig, ax
            Existing figure/axes to draw onto.  Created if ``None``.
        label
            Legend entry; a legend is drawn when non-empty.
        save
            Write to ``filename``.  Output format is inferred from the
            extension (``.png``, ``.pdf``, ``.svg``, ``.jpg`` ...).
        **plot_kw
            Forwarded to :meth:`matplotlib.axes.Axes.plot`.
        """
        if fig is None or ax is None:
            fig, ax = plt.subplots()

        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        ax.set_title(title)
        ax.grid(grid)
        ax.plot(x, y, label=label, **plot_kw)

        if label:
            ax.legend()

        self.__finish(fig, show, save, filename)

        return fig, ax

    def __draw_xsec_axes(
        self,
        ax: plt.Axes,
        x: np.ndarray,
        series: list[tuple[str, np.ndarray]],
        *,
        energy_unit: str,
        xsec_unit: str,
        energy_log: bool,
        xsec_log: bool,
        trim: bool,
        grid: bool,
        legend: bool,
        set_xlabel: bool = True,
        title: str = "",
        **plot_kw: Any,
    ) -> None:
        """Draw one or more cross-section curves onto a single axes.

        Shared by both the overlay and subplot layouts.  *series* is a list of
        ``(label, sigma)`` pairs already converted to *xsec_unit*; *x* is the
        photon energy already converted to *energy_unit*.
        """
        x = np.asarray(x)
        x_lo: float | None = None
        x_hi: float | None = None

        for label, y in series:
            y = np.asarray(y)
            ax.plot(x, y, label=label, **plot_kw)

            # Track the energy span where this curve has positive data.
            mask = np.isfinite(y) & (y > 0)
            if mask.any():
                lo, hi = float(x[mask].min()), float(x[mask].max())
                x_lo = lo if x_lo is None else min(x_lo, lo)
                x_hi = hi if x_hi is None else max(x_hi, hi)

        # Slight padding on the sides
        if trim and x_lo is not None and x_hi is not None and x_hi > x_lo:
            xr_lo, xr_hi = x_lo, x_hi
        else:
            finite = x[np.isfinite(x)]
            xr_lo = float(finite.min()) if finite.size else None
            xr_hi = float(finite.max()) if finite.size else None

        # Dynamic x-scale
        use_log_x = energy_log
        if (
            energy_log
            and xr_lo is not None
            and xr_hi is not None
            and xr_lo > 0
            and np.log10(xr_hi / xr_lo) < 1.0
        ):
            use_log_x = False

        ax.set_xscale("log" if use_log_x else "linear")
        ax.set_yscale("log" if xsec_log else "linear")
        if set_xlabel:
            ax.set_xlabel(self.__energy_label(energy_unit))
        ax.set_ylabel(self.__xsec_label(xsec_unit))
        if title:
            ax.set_title(title)
        ax.grid(grid)

        if trim and x_lo is not None and x_hi is not None and x_hi > x_lo:
            # Pad the limits by a few percent so the data does not sit flush
            # against the spines.  Pad multiplicatively on a log axis,
            # additively on a linear one.
            pad = 0.03
            if use_log_x:
                factor = (x_hi / x_lo) ** pad
                ax.set_xlim(x_lo / factor, x_hi * factor)
            else:
                margin = pad * (x_hi - x_lo)
                ax.set_xlim(x_lo - margin, x_hi + margin)

        if legend and len(series) > 1:
            ax.legend()

    def plot_xsec(
        self,
        xsecs: XsecsProps,
        processes: list[str] | None = None,
        layout: str = "overlay",
        fig: plt.Figure | None = None,
        ax: plt.Axes | None = None,
        energy_unit: str = "eV",
        xsec_unit: str = "cm^2",
        energy_log: bool = True,
        xsec_log: bool = True,
        trim: bool = True,
        title: str = "",
        grid: bool = True,
        show: bool = True,
        save: bool = False,
        filename: str = "xsec.png",
        **plot_kw: Any,
    ) -> tuple[plt.Figure, Any]:
        """Plot photo cross sections sigma(E) on log-log axes.

        Single home for cross-section plotting: handles unit conversion,
        axis scaling and labelling.  ``Reaction.plot_xsecs`` delegates here.

        Parameters
        ----------
        xsecs
            Mapping as returned by :func:`jaff.physics.get_xsec` -- carries
            ``photon_energy`` (eV) plus any of ``photo_absorption``,
            ``photo_dissociation``, ``photo_ionization`` (all in cm^2).
        processes
            Subset of the three process keys to draw.  Default: every
            process present (non-``None``) in ``xsecs``.
        layout
            ``"overlay"`` (default) draws every process on one axes;
            ``"subplots"`` draws one stacked panel per process sharing the
            energy axis.
        energy_unit
            Horizontal-axis unit: ``"eV"``, ``"erg"``, ``"nm"``, ``"um"``.
        xsec_unit
            Cross-section unit: ``"cm^2"``, ``"Mb"``, ``"barn"``.
        energy_log, xsec_log
            Log-scale the respective axis (default ``True``).
        trim
            Tighten the energy axis to the range where the cross section is
            positive (default ``True``).  Cross-section grids often pad the
            high-energy tail with zeros, which would otherwise stretch the
            axis far past the meaningful data.
        **plot_kw
            Forwarded to :meth:`matplotlib.axes.Axes.plot`.

        Returns
        -------
        tuple[Figure, Axes | numpy.ndarray]
            For ``layout="overlay"`` the second item is the single axes; for
            ``layout="subplots"`` it is the array of per-process axes.
        """
        from ..physics import units

        if layout not in ("overlay", "subplots"):
            raise ValueError(f"layout must be 'overlay' or 'subplots', got {layout!r}")

        energy = xsecs["photon_energy"]
        if energy is None:
            raise ValueError("xsecs has no 'photon_energy' data to plot.")

        if processes is None:
            processes = [k for k in self._PROC_LABELS if xsecs.get(k) is not None]
        # Keep only requested processes that actually carry data.
        processes = [p for p in processes if xsecs.get(p) is not None]
        if not processes:
            raise ValueError("xsecs has no cross-section data to plot.")

        # Data are stored as eV + cm^2; convert to the requested units.
        x = np.asarray(units.convert(energy, "eV", energy_unit))
        series = [
            (
                self._PROC_LABELS.get(k, k),
                np.asarray(units.convert(xsecs[k], "cm2", xsec_unit)),  # type: ignore
            )
            for k in processes
        ]

        common = dict(
            energy_unit=energy_unit,
            xsec_unit=xsec_unit,
            energy_log=energy_log,
            xsec_log=xsec_log,
            trim=trim,
            grid=grid,
            **plot_kw,
        )

        if layout == "subplots":
            n = len(series)
            fig, axes = plt.subplots(
                n, 1, sharex=True, figsize=(6.4, 2.6 * n), squeeze=False
            )
            axes = axes[:, 0]
            for i, (a, (label, y)) in enumerate(zip(axes, series)):
                self.__draw_xsec_axes(
                    a,
                    x,
                    [(label, y)],
                    legend=False,
                    set_xlabel=(i == n - 1),  # only the bottom panel
                    title=label,
                    **common,  # type: ignore
                )
            if title:
                fig.suptitle(title)
            self.__finish(fig, show, save, filename)
            return fig, axes

        # overlay
        if fig is None or ax is None:
            fig, ax = plt.subplots()
        self.__draw_xsec_axes(ax, x, series, legend=True, title=title, **common)  # type: ignore
        self.__finish(fig, show, save, filename)

        return fig, ax
