"""Portable EduPy launcher that locates Tcl/Tk before loading the interface."""

import os
import sys


def configure_tk_runtime():
    tcl_root = os.path.join(sys.base_prefix, "tcl")
    tcl_library = os.path.join(tcl_root, "tcl8.6")
    tk_library = os.path.join(tcl_root, "tk8.6")
    if os.path.isfile(os.path.join(tcl_library, "init.tcl")):
        os.environ.setdefault("TCL_LIBRARY", tcl_library)
    if os.path.isfile(os.path.join(tk_library, "tk.tcl")):
        os.environ.setdefault("TK_LIBRARY", tk_library)


if __name__ == "__main__":
    configure_tk_runtime()
    from main import App
    App()
