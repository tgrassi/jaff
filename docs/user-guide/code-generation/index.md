---
tags:
    - User-guide
    - Code-generation
icon: lucide/code-2
---

# Code Generation

JAFF can turn any loaded network into ready-to-compile source files in C, C++, Fortran, Python, Rust, Julia, or R. The generation pipeline is template-driven: you write ordinary source files that contain special JAFF directives, and JAFF expands them into network-specific code.

<div class="grid cards" markdown>

- :lucide-form:{ .sm .middle } **Template Syntax**

    ***

    Learn the `$JAFF` directive language: `SUB`, `REPEAT`, `REDUCE`, `GET`, `HAS`, `END`, and the optional `REPLACE` modifier.

    [:octicons-arrow-right-24: Template Syntax](template-syntax.md)

- :lucide-settings-2:{ .sm .middle } **Configuration File**

    ***

    Configure `jaffgen` runs declaratively with a `jaff.toml` file: set network paths, template names, output directories, radiation bands, and data-table conversions.

    [:octicons-arrow-right-24: Configuration File](jaff-toml.md)

- :lucide-terminal:{ .sm .middle } **jaffgen CLI**

    ***

    Run the code-generation pipeline from the command line. Combine predefined templates, custom input directories, and individual files in a single invocation.

    [:octicons-arrow-right-24: jaffgen CLI](jaffgen.md)

</div>
