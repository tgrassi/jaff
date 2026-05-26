---
tags:
    - User-guide
    - Network
icon: lucide/network
---

# Working with Networks

Once a network is loaded, JAFF exposes a rich set of attributes and methods for inspecting species, reactions, and elements — and for exporting the network in various formats.

```python
from jaff import Network

net = Network("networks/h_photoionization/h_photo.jet")

print(f"Label:     {net.label}")
print(f"Species:   {net.species.count}")
print(f"Reactions: {net.reactions.count}")
print(f"Elements:  {net.elements.count}")
```

<div class="grid cards" markdown>

- :lucide-flask-conical:{ .lg .middle } **Network**

    ***

    Top-level `Network` object: constructor options, key attributes, export methods, and stoichiometry matrices.

    [:octicons-arrow-right-24: Network](network.md)

- :lucide-dna:{ .lg .middle } **Species**

    ***

    Work with individual `Specie` objects and the `Species` collection: lookup, filtering, mass, charge, and elemental composition.

    [:octicons-arrow-right-24: Species](species.md)

- :lucide-periodic-table:{ .lg .middle } **Elements**

    ***

    Query the element catalogue derived from all species: density matrices, truth matrices, atomic properties.

    [:octicons-arrow-right-24: Elements](elements.md)

- :lucide-zap:{ .lg .middle } **Reactions**

    ***

    Inspect individual `Reaction` objects and the `Reactions` catalogue: filtering, conservation checks, rate expressions, and code generation.

    [:octicons-arrow-right-24: Reactions](reactions.md)

- :lucide-terminal:{ .lg .middle } **jaffx CLI**

    ***

    Quick network inspection and rate-coefficient export from the command line — without running the full code-generation pipeline.

    [:octicons-arrow-right-24: jaffx](jaffx.md)

</div>
