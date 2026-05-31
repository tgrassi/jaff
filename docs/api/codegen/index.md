---
tags:
    - Api
    - Code-generation
icon: phosphor/brackets-curly
---

# jaff.codegen

The `jaff.codegen` subpackage contains the classes for generating solver source code from a chemical reaction network.

## Classes

| Class                             | Description                                                       |
| --------------------------------- | ----------------------------------------------------------------- |
| [`Builder`](builder/index.md)           | High-level build orchestrator using named plugin templates        |
| [`Codegen`](codegen/index.md)           | Low-level multi-language code generator (rates, ODEs, Jacobian)   |
| [`Preprocessor`](preprocessor/index.md) | Pragma-based template preprocessor for file-level code generation |

## Quick Start

```python
from jaff import Network
from jaff.codegen import Codegen, Builder, Preprocessor

net = Network("networks/react_COthin")

# High-level: build a ready-to-run solver
builder = Builder(net)
builder.build(template="python_solve_ivp", output_dir="output/")

# Low-level: generate individual code blocks
cg = Codegen(network=net, lang="c++")
rates = cg.get_rates_str(use_cse=True)
odes  = cg.get_ode_str(use_cse=True)
jac   = cg.get_jacobian_str(use_cse=True)
```
