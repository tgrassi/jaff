---
tags:
    - Api
    - Code-generation
icon: lucide/braces
---

# jaff.codegen

This section provides the details of the classes for generating optimized code from chemical reaction networks.

## Classes

| Class                             | Description                                                       |
| --------------------------------- | ----------------------------------------------------------------- |
| [`Builder`](builder.md)           | High-level build orchestrator using named plugin templates        |
| [`Codegen`](codegen.md)           | Low-level multi-language code generator (rates, ODEs, Jacobian)   |
| [`Preprocessor`](preprocessor.md) | Pragma-based template preprocessor for file-level code generation |

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
