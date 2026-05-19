from __future__ import annotations

from typing import TYPE_CHECKING

from sympy import Basic, Expr, Float, Idx, MatrixSymbol

from jaff.core.logger import jaff_progress

if TYPE_CHECKING:
    from .. import Reaction
    from .radiation import Radiation


def get_sfluxes(reactions: list["Reaction"], specie_index: dict[str, int]) -> list[Expr]:
    nspec = max(specie_index.values()) + 1 if specie_index else 0
    nreact = len(reactions)
    fluxes: list[Expr] = [Float(0.0) for _ in range(nreact)]
    nden_matrix = MatrixSymbol("nden", nspec, 1)

    for i, reaction in enumerate(reactions):
        flux = reaction.rate
        for reactant in reaction.reactants:
            flux *= nden_matrix[specie_index[str(reactant)]]

        fluxes[i] = flux

    return fluxes


def get_sodes(reactions: list["Reaction"], specie_index: dict[str, int]) -> list[Basic]:
    nspec = max(specie_index.values()) + 1 if specie_index else 0
    fluxes = get_sfluxes(reactions, specie_index)
    sodes: list[Basic] = [Float(0.0) for _ in range(nspec)]

    for i, reaction in enumerate(reactions):
        for rr in reaction.reactants:
            idx = (
                rr.index
                if isinstance(rr.fidx, str) and rr.fidx.startswith("idx_")
                else int(rr.fidx)
            )
            sodes[idx] -= fluxes[i]

        # Add flux to products
        for pp in reaction.products:
            idx = (
                pp.index
                if isinstance(pp.fidx, str) and pp.fidx.startswith("idx_")
                else int(pp.fidx)
            )
            sodes[idx] += fluxes[i]

    return sodes


def get_sradodes(
    radiation: "Radiation" | None, specie_index: dict[str, int], order: int = 0
) -> list[Expr]:
    # Check if radiation is enabled
    if radiation is None:
        raise RuntimeError("No radiation bands found. Radiation odes cannot be generated")

    # Raise if order is not supported
    if order not in [0, 1, 2, 3]:
        raise ValueError("Invalid order: Supported orders are 0, 1, 2, 3")

    rad_groups = radiation.groups
    nspec = max(specie_index.values()) + 1 if specie_index else 0
    nden = MatrixSymbol("nden", nspec, 1)

    den = MatrixSymbol(
        "radeden" if radiation.energy_density else "photden",
        radiation.nbands,
        1,
    )
    rflux = MatrixSymbol("rflux", radiation.nbands, 1)
    flux_map = {den[Idx(i)]: rflux[Idx(i)] for i in range(radiation.nbands)}
    grate, gflux = (
        [Float(0.0)] * radiation.nbands,
        [Float(0.0)] * radiation.nbands,
    )

    for group in jaff_progress.track(
        rad_groups, description="Generating radiation equations"
    ):
        group_rate: Basic = Float(0.0)
        group_dRad_dt_extra = Float(0.0)
        for reaction, props in group.props.items():
            rrate = props["k"]
            group_dRad_dt_extra += props["delta_rad"]
            for reactant in reaction.reactants:
                rrate *= nden[Idx(specie_index[str(reactant)])]

            group_rate -= rrate

        # Flux
        flux = group_rate.xreplace(flux_map)
        # dRad_dt_extra assumed to be in units of energy density rate
        group_rate += group_dRad_dt_extra / (
            1 if radiation.energy_density else (group.eavg or 1)
        )

        grate[group.index] = group_rate
        gflux[group.index] = flux

    radodes: list[Expr] = [Float(0.0) for _ in range(2 * radiation.nbands)]

    for i, (rate, flux) in enumerate(zip(grate, gflux)):
        ei, fi = radiation.ordered_index(i, order)
        radodes[ei] = rate
        radodes[fi] = flux

    return radodes
