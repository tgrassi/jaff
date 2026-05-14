---
tags:
    - Introduction
icon: lucide/house
---

# JAFF

<div align="left" markdown>
<div style="display: flex; align-items: center;">
    <img class="jaff-logo" src="assets/logo.png" alt="JAFF Logo" width="60" style="margin-right: 20px;">
    <div>
    <strong>Just Another Fancy Format</strong>
    <br>
    <em>An astrochemical network parser and multi-language code generator</em>
    </div>
</div>

---

<!--## Welcome to JAFF-->

JAFF is a comprehensive tool for working with astrochemical reaction networks. It provides a unified interface for parsing multiple network formats, analyzing chemical species and reactions, and generating optimized code for numerical simulations in multiple programming languages: `C`, `C++`, `Fortran`, `Python`, `Rust`, `Julia`, and `R`.

<div class="grid cards" markdown>

- :lucide-atom:{ .lg .middle } **Multi-format support**

    ***

    Parses `KIDA`, `UDFA`, `PRIZMO`, `KROME`, and `UCLCHEM` networks with automatic format detection.

- :lucide-chart-spline:{ .lg .middle } **Validation and Analysis**

    ***

    Automatically validates mass and charge conservation, and extracts elemental composition.

- :lucide-code:{ .lg .middle } **Code Generation**

    ***

    Generates optimized code for rates, ODEs, Jacobians, and fluxes `C`, `C++`, `Fortran`, `Python`, `Rust`, `Julia`, and `R` with optional CSE.

- :lucide-chart-no-axes-gantt:{ .lg .middle } **Template System**

    ***

    Powerful template language (JAFF directives) for customizing code generation to match any simulation framework.

</div>

---

## Quick Example

```python
from jaff import Network

# Load a chemical network
net = Network("networks/react_COthin")

# Access species information
print(f"Network contains {len(net.species)} species")
print(f"First species: {net.species[0].name}, mass: {net.species[0].mass} amu")

# Access reactions
for reaction in net.reactions[:3]:
    print(reaction.get_sympy())  # Symbolic representation

# Generate code
from jaff import Codegen
cg = Codegen(network=net, lang="cxx")
rate_code = cg.get_rates(idx_offset=0, rate_var="rate", brac_format="[]")
print(rate_code)
```

---

## Use Cases

### Astrochemistry Simulations

Generate efficient ODE solvers for modeling chemical evolution in:

- **Interstellar clouds** - dark clouds, molecular clouds
- **Protoplanetary disks** - planet formation environments
- **Planetary atmospheres** - exoplanet and solar system atmospheres
- **Stellar outflows** - AGB stars, supernovae

### Network Analysis

- Compare different reaction databases
- Identify missing species or reactions
- Validate stoichiometric conservation
- Extract element density matrices

### Code Integration

- Generate code compatible with existing simulation frameworks
- Customize output format with templates
- Optimize for performance with CSE
- Support multiple programming languages

---

## Supported Network Formats

| Format      | Description                            | Reference                                                            |
| ----------- | -------------------------------------- | -------------------------------------------------------------------- |
| **KIDA**    | Kinetic Database for Astrochemistry    | [A&A, 689, A63 (2024)](https://doi.org/10.1051/0004-6361/202450606)  |
| **UDFA**    | UMIST Database for Astrochemistry      | [A&A, 682, A109 (2024)](https://doi.org/10.1051/0004-6361/202346908) |
| **PRIZMO**  | Uses `->` separator with `VARIABLES{}` | [MNRAS 494, 4471 (2020)](https://doi.org/10.1093/mnras/staa971)      |
| **KROME**   | Comma-separated with `@format:` header | [MNRAS 439, 2386 (2014)](https://doi.org/10.1093/mnras/stu114)       |
| **UCLCHEM** | Comma-separated with `,NAN,` marker    | [AJ 154 38 (2017)](https://doi.org/10.3847/1538-3881/aa773f)         |

---

## What's Next?

<div class="grid cards" markdown>

- :lucide-rocket:{ .lg .middle } **Getting Started**

    ***

    Install JAFF and run your first network analysis

    [:octicons-arrow-right-24: Installation Guide](getting-started/installation.md)

- :material-book-open-variant:{ .lg .middle } **User Guide**

    ***

    Learn how to work with networks, species, and reactions

    [:lucide-book-open: User Guide](user-guide/loading-networks.md)

- :lucide-braces:{ .lg .middle } **Code Generation**

    ***

    Generate optimized code for your simulations

    [:octicons-arrow-right-24: Code Generation Guide](user-guide/code-generation.md)

- :lucide-folder-kanban:{ .lg .middle } **API Reference**

    ***

    Complete API documentation for all modules

    [:octicons-arrow-right-24: API Docs](api/index.md)

</div>

---

## Community & Support

- **GitHub Issues**: Report bugs and request features at [github.com/tgrassi/jaff/issues](https://github.com/tgrassi/jaff/issues)
- **Discussions**: Ask questions and share ideas
- **Contributing**: See our [Contributing Guide](development/contributing.md)

---

## Citation

If you use JAFF in your research, please cite:

```bibtex
@software{jaff2024,
  title = {JAFF: Just Another Fancy Format},
  author = {JAFF Team},
  year = {2024},
  url = {https://github.com/tgrassi/jaff},
  version = {0.1.0}
}
```

---

## License

JAFF is released under the [MIT License](about/license.md).

---

!!! tip "New to astrochemistry?"
Check out our [Basic Concepts](getting-started/concepts.md) page to learn about chemical networks, reaction rates, and how JAFF can help your research.

!!! example "Ready to dive in?"
Jump straight to the [Quick Start Guide](getting-started/quickstart.md) to start using JAFF in minutes!
