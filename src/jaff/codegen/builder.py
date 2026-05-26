"""High-level build orchestrator for JAFF plugin-based code generation.

This module provides :class:`Builder`, a convenience wrapper that locates a
named plugin, resolves the template directory, and delegates the full
code-generation pipeline to the plugin's ``main()`` entry point.

Plugin discovery
----------------
Plugins live in ``jaff.plugins.<template_name>.plugin`` and must expose a
``main(network, *, path_template, path_build)`` function.  The *template_name*
corresponds to a sub-directory under
``<jaff_codegen>/templates/preprocessor/``.
"""

import os
import sys


class Builder:
    """Orchestrate plugin-based code generation for a chemical network.

    :class:`Builder` is the top-level entry point for users who want to
    generate a complete solver project (e.g. a Python ``solve_ivp`` wrapper or
    a C++ CVODE driver) from a parsed network by selecting a named template.

    Parameters
    ----------
    network : Network
        Parsed chemical reaction network passed unchanged to the plugin.

    Attributes
    ----------
    network : Network
        The network instance provided at construction time.
    """

    def __init__(self, network) -> None:
        """Store the network for later use by :meth:`build`.

        Parameters
        ----------
        network : Network
            Parsed chemical reaction network.
        """
        self.network = network

    def build(self, template: str = "python_solve_ivp", output_dir: str | None = None) -> str:
        """Generate a complete solver project using a named plugin template.

        Resolves the template directory, dynamically imports the plugin module
        ``jaff.plugins.<template>.plugin``, and calls its ``main()`` function
        with the network and resolved paths.  After a successful build the
        output directory path is returned.

        If the plugin cannot be imported, all available template names are
        printed to stdout and the process exits with code ``1``.

        Parameters
        ----------
        template : str, optional
            Name of the plugin template to use.  Must match a sub-directory
            under ``<jaff_codegen>/templates/preprocessor/`` and a
            ``jaff.plugins.<template>.plugin`` module.
            Default ``"python_solve_ivp"``.
        output_dir : str or None, optional
            Destination directory for the generated files.  When ``None`` the
            current working directory is used.

        Returns
        -------
        str
            Absolute path to the directory containing the generated output files.

        Raises
        ------
        SystemExit
            If the named plugin module cannot be imported (exit code ``1``).
        """
        print("Building network with template:", template)

        # Resolve the template directory bundled with the jaff.codegen package
        path_template = os.path.join(
            os.path.dirname(__file__), "templates", "preprocessor", template
        )

        # Resolve the output directory (default: current working directory)
        if output_dir is None:
            path_build = os.getcwd()
        else:
            path_build = output_dir

        # Dynamically import the plugin module using its fully-qualified name
        try:
            module = __import__(f"jaff.plugins.{template}.plugin", fromlist=["main"])
        except ImportError:
            print(f"Error: Template '{template}' not found. Available templates are:")
            # List all sub-directories in the preprocessor templates folder
            for template in os.listdir(
                os.path.join(os.path.dirname(__file__), "templates", "preprocessor")
            ):
                print(template)
            sys.exit(1)

        # Delegate all code generation and file writing to the plugin's main()
        module.main(self.network, path_template=path_template, path_build=path_build)

        print(f"Network built successfully using template '{template}'.")
        print(f"Output files are located in: {path_build}")

        return path_build
