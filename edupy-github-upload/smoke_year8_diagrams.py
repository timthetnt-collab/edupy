"""Render every Year 8 interactive diagram type without publishing anything."""

import tkinter as tk

import maths_diagrams
import ui
import year8_maths
from run_edupy import configure_tk_runtime


TOPICS = [
    "negative_add_subtract", "gradient", "bar_line_charts", "simple_pie_charts",
    "circle_terms", "circle_area", "fractions_of_amount", "percentage_amount",
    "ratio_scaling", "sample_spaces", "mutually_exclusive", "integer_enlargement",
    "triangle_congruence", "cube_cuboid_volume", "constructions", "pictograms",
    "line_dot_plots", "scatter_graphs", "dual_stacked_bars", "grouped_frequency",
    "compound_volume",
]


def run():
    configure_tk_runtime()
    root = tk.Tk(); root.withdraw(); ui.configure_root(root)
    rendered = set()
    for topic in TOPICS:
        question = year8_maths.generate(topic)
        spec = question.get("diagram")
        if not spec:
            raise RuntimeError(f"{topic} did not provide a diagram")
        response = tk.StringVar(root)
        diagram = maths_diagrams.render_diagram(root, spec, response)
        diagram.pack(fill="both", expand=True)
        root.update_idletasks(); root.update()
        canvas = next(child for child in diagram.winfo_children() if child.winfo_class() == "Canvas")
        canvas.event_generate("<Button-1>", x=canvas.winfo_width() // 2, y=canvas.winfo_height() // 2)
        canvas.event_generate("<B1-Motion>", x=canvas.winfo_width() // 2 + 12, y=canvas.winfo_height() // 2)
        root.update_idletasks(); root.update()
        rendered.add(spec["kind"])
        diagram.destroy()
        print(f"OK: {topic} -> {spec['kind']}")
    root.destroy()
    print(f"Rendered {len(rendered)} distinct interactive diagram types.")


if __name__ == "__main__":
    run()
