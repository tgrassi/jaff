from typing import TYPE_CHECKING

from sympy import Expr, Float, parse_expr

from ....config import SHIELDING_DATA_DIR
from ....drivers import HDF5
from ....errors import ParserError

if TYPE_CHECKING:
    from .... import Reaction
    from ....core.network import Network

LEIDEN_SPECIES_MAP: dict[str, str] = {
    "H2": "n_H2",
    "H": "n_H",
    "C": "n_C",
    "N2": "n_N2",
    "CO": "n_CO",
    "self": "",
}


def get_shielding(reaction: Reaction, network: Network) -> Expr:
    sprops = reaction.metadata["shielding"]
    if "shielded_by" not in sprops:
        raise ParserError("'shielded_by' must be specified for Leiden shielding tables")

    if "radiation" not in sprops:
        sprops["radiation"] = "ISRF"

    species_map = {**LEIDEN_SPECIES_MAP, "self": f"n_{reaction.reactants[0]}"}
    if any(sp not in species_map for sp in sprops["shielded_by"]):
        raise ParserError(f"Invalid shielding specie detected for reaction: {reaction}")

    sprops["radiation"] = sprops["radiation"].lower()
    h5group = f"{SHIELDING_DATA_DIR}/leiden.hdf5::{reaction.serialized}"
    h5obj = HDF5()

    shielding_table = h5obj.to_dict(h5group, include=sprops["shielded_by"])
    h5obj.from_dict(
        f"{reaction.metadata['jaffgen']['jaffgen_object'].jaffgen_config['output_dir']}/shielding_{reaction.serialized}.hdf5",
        shielding_table,
    )

    shielding: Expr = Float(1.0)
    for specie in sprops["shielded_by"]:
        shielding *= parse_expr(
            f"interp_{reaction.index}_shielding_{specie}({species_map[specie]})"
        )

    return shielding
