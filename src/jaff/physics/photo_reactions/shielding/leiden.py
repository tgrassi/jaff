from typing import TYPE_CHECKING

from astropy.units.cds import K
from sympy import Expr, Float, parse_expr

from ....config import SHIELDING_DATA_DIR
from ....drivers import HDF5
from ....errors import ParserError

if TYPE_CHECKING:
    from .... import Reaction
    from ....core.network import Network

LEIDEN_SPECIES_MAP: dict[str, str] = {
    "H2": "H2",
    "H": "H",
    "C": "C",
    "N2": "N2",
    "CO": "CO",
    "self": "",
}


def get_shielding(reaction: Reaction, network: Network) -> Expr:
    sprops = reaction.metadata["shielding"]
    if "shielded_by" not in sprops:
        raise ParserError("'shielded_by' must be specified for Leiden shielding tables")

    if "radiation" not in sprops:
        sprops["radiation"] = "ISRF"

    species_map = {**LEIDEN_SPECIES_MAP, "self": f"{reaction.reactants[0]}"}
    if any(sp not in species_map for sp in sprops["shielded_by"]):
        raise ParserError(f"Invalid shielding specie detected for reaction: {reaction}")

    sprops["radiation"] = sprops["radiation"].lower()
    h5group_core = f"{SHIELDING_DATA_DIR}/leiden.hdf5::{reaction.serialized}"
    h5group_rad = f"{h5group_core}/{sprops['radiation']}"
    h5obj = HDF5()

    ncol = h5obj.to_dict(h5group_core, include="N")
    shielding_table = h5obj.to_dict(h5group_rad, include=sprops["shielded_by"])
    h5dict = {**ncol, **shielding_table}

    h5obj.from_dict(
        f"{reaction.metadata['jaffgen']['jaffgen_object'].jaffgen_config['output_dir']}/shielding_{reaction.serialized}.hdf5",
        h5dict,
        mode="w",
    )

    shielding: Expr = Float(1.0)
    for specie in sprops["shielded_by"]:
        shielding *= parse_expr(
            f"interp_{reaction.index}_shielding_{specie}(ncol_{species_map[specie]})"
        )

    return shielding
