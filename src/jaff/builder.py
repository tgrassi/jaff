import os
import sys


class Builder:
    def __init__(self, network):
        self.network = network

    def build(self, template="python_solve_ivp", output_dir=None):
        print("Building network with template:", template)

        # prepare the template path
        path_template = os.path.join(
            os.path.dirname(__file__), "templates", "preprocessor", template
        )

        # prepare the build path (use current working directory if not specified)
        if output_dir is None:
            path_build = os.getcwd()
        else:
            path_build = output_dir

        # import module based on the template name
        try:
            module = __import__(f"jaff.plugins.{template}.plugin", fromlist=["main"])
        except ImportError:
            print(f"Error: Template '{template}' not found. Available templates are:")
            for template in os.listdir(
                os.path.join(os.path.dirname(__file__), "templates", "preprocessor")
            ):
                print(template)
            sys.exit(1)

        # call the main function of the module to preprocess the files
        # the definition of the main function is in the plugin folder
        module.main(self.network, path_template=path_template, path_build=path_build)

        print(f"Network built successfully using template '{template}'.")
        print(f"Output files are located in: {path_build}")

        return path_build
