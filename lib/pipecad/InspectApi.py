# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# :: Welcome to PipeCAD!                                      ::
# ::  ____                        ____     ______  ____       ::
# :: /\  _`\   __                /\  _`\  /\  _  \/\  _`\     ::
# :: \ \ \L\ \/\_\  _____      __\ \ \/\_\\ \ \L\ \ \ \/\ \   ::
# ::  \ \ ,__/\/\ \/\ '__`\  /'__`\ \ \/_/_\ \  __ \ \ \ \ \  ::
# ::   \ \ \/  \ \ \ \ \L\ \/\  __/\ \ \L\ \\ \ \/\ \ \ \_\ \ ::
# ::    \ \_\   \ \_\ \ ,__/\ \____\\ \____/ \ \_\ \_\ \____/ ::
# ::     \/_/    \/_/\ \ \/  \/____/ \/___/   \/_/\/_/\/___/  ::
# ::                  \ \_\                                   ::
# ::                   \/_/                                   ::
# ::                                                          ::
# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
# PipeCAD - Piping Design Software.
# Copyright (C) 2021 Wuhan OCADE IT. Co., Ltd.
# Author: Shing Liu(eryar@163.com)
# Date: 21:16 2021-09-16

import sys
import os
import inspect

try:
    # Try to access PipeCad if it is already loaded
    import PipeCad
except ImportError:
    # PipeCad might be exposed directly in the interpreter or via another way
    pass

def collect_api_info(output_file="PipeCad_API.txt"):
    """
    Inspects the PipeCad module/object and writes its attributes and methods to a file.
    """

    # Attempt to locate the PipeCad object
    target_module = None

    if 'PipeCad' in sys.modules:
        target_module = sys.modules['PipeCad']
    elif 'PipeCad' in locals():
        target_module = locals()['PipeCad']
    elif 'PipeCad' in globals():
        target_module = globals()['PipeCad']
    else:
        # If we can't find it, we can't inspect it
        print("Error: 'PipeCad' module or object not found. Please run this script inside PipeCAD application.")
        return

    try:
        with open(output_file, "w", encoding='utf-8') as f:
            f.write(f"PipeCAD API Inspection Report\n")
            f.write(f"Generated on: {os.path.abspath(output_file)}\n")
            f.write("=" * 60 + "\n\n")

            # Get all attributes
            attributes = dir(target_module)
            attributes.sort()

            for attr_name in attributes:
                # Skip internal attributes if desired, or keep them
                # if attr_name.startswith("__"): continue

                try:
                    attr_value = getattr(target_module, attr_name)
                    attr_type = type(attr_value).__name__

                    f.write(f"Name: {attr_name}\n")
                    f.write(f"Type: {attr_type}\n")

                    if callable(attr_value):
                        f.write("Category: Method/Function\n")
                        try:
                            # Try to get the signature
                            try:
                                sig = inspect.signature(attr_value)
                                f.write(f"Signature: {attr_name}{sig}\n")
                            except ValueError:
                                f.write(f"Signature: (Not available)\n")

                            # Try to get the docstring
                            doc = inspect.getdoc(attr_value)
                            if doc:
                                f.write(f"Documentation:\n{doc}\n")
                            else:
                                f.write("Documentation: None\n")

                        except Exception as e:
                             f.write(f"Error inspecting callable: {e}\n")
                    else:
                        f.write("Category: Attribute/Constant\n")
                        f.write(f"Value: {str(attr_value)}\n")

                    f.write("-" * 40 + "\n")

                except Exception as e:
                    f.write(f"Error accessing {attr_name}: {e}\n")
                    f.write("-" * 40 + "\n")

        print(f"Successfully wrote API info to {output_file}")

    except Exception as e:
        print(f"Failed to write output file: {e}")

# Automatically run when imported in PipeCAD
# Use a safe path or just the filename in the current working directory
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "PipeCad_API_Dump.txt")
print(f"Starting API inspection... Output: {path}")
collect_api_info(path)