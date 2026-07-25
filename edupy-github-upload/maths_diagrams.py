"""Interactive Tk canvas diagrams used by visual maths questions."""

import math
import tkinter as tk

from settings import THEME, FONT_TEXT


WIDTH, HEIGHT = 660, 280


def render_diagram(parent, spec, response):
    """Render a question diagram and connect meaningful selections to response."""
    if not spec:
        return None
    frame = tk.Frame(parent, bg=THEME.get("panel_alt", THEME["bg"]), padx=10, pady=10)
    hint = tk.Label(frame, text="Interactive diagram · click or drag to explore", font=("Segoe UI", 9), bg=frame["bg"], fg=THEME.get("muted", THEME["fg"]), anchor="w")
    hint.pack(fill="x", pady=(0, 6))
    canvas = tk.Canvas(frame, width=WIDTH, height=HEIGHT, bg=THEME.get("input_bg", THEME["bg"]), highlightthickness=1, highlightbackground=THEME.get("border", THEME["accent"]), cursor="hand2")
    canvas.pack(fill="x")
    status = tk.Label(frame, text="", font=FONT_TEXT, bg=frame["bg"], fg=THEME["accent"], anchor="w")
    status.pack(fill="x", pady=(6, 0))
    kind = spec.get("kind")
    renderer = {
        "number_line": _number_line, "coordinate_grid": _coordinate_grid,
        "bar_chart": _bar_chart, "pie_chart": _pie_chart,
        "circle_parts": _circle_parts, "circle_measure": _circle_measure,
        "fraction_strip": _fraction_strip, "percentage_bar": _percentage_bar,
        "ratio_blocks": _ratio_blocks, "sample_space": _sample_space,
        "probability_scale": _probability_scale, "shape_scale": _shape_scale,
        "triangles": _triangles, "prism": _prism,
        "construction": _construction, "pictogram": _pictogram,
        "line_plot": _line_plot, "scatter_plot": _scatter_plot,
        "stacked_bar": _stacked_bar, "grouped_table": _grouped_table,
        "compound_prism": _compound_prism,
        "balance_scale": _balance_scale,
    }.get(kind)
    if renderer:
        renderer(canvas, status, response, spec)
    else:
        status.config(text="Diagram unavailable for this question.")
    return frame


def _set_status(status, text):
    status.config(text=text)


def _number_line(canvas, status, response, spec):
    low, high = spec.get("min", -10), spec.get("max", 10); left, right, y = 50, WIDTH-50, 135
    canvas.create_line(left, y, right, y, fill=THEME["fg"], width=3, arrow="both")
    for value in range(low, high+1):
        x = left + (value-low)/(high-low)*(right-left)
        length = 12 if value % 5 == 0 else 7
        canvas.create_line(x,y-length,x,y+length,fill=THEME.get("muted",THEME["fg"]))
        if value % 5 == 0: canvas.create_text(x,y+28,text=str(value),fill=THEME["fg"],font=("Segoe UI",9))
    marker = canvas.create_oval(0,0,0,0,fill=THEME["accent"],outline="")
    def choose(event):
        value = round(low + (event.x-left)/(right-left)*(high-low)); value=max(low,min(high,value))
        x=left+(value-low)/(high-low)*(right-left); canvas.coords(marker,x-9,y-9,x+9,y+9)
        if spec.get("response_mode", True): response.set(str(value))
        _set_status(status,f"Marker: {value}")
    canvas.bind("<Button-1>", choose); canvas.bind("<B1-Motion>", choose)


def _coordinate_grid(canvas, status, response, spec):
    origin_x, origin_y, step = WIDTH//2, HEIGHT//2, 24
    for n in range(-12,13):
        colour = THEME.get("border", "#334")
        canvas.create_line(origin_x+n*step, 8, origin_x+n*step, HEIGHT-8, fill=colour)
    for n in range(-5,6): canvas.create_line(8,origin_y+n*step,WIDTH-8,origin_y+n*step,fill=THEME.get("border","#334"))
    canvas.create_line(8,origin_y,WIDTH-8,origin_y,fill=THEME["fg"],width=2,arrow="last")
    canvas.create_line(origin_x,HEIGHT-8,origin_x,8,fill=THEME["fg"],width=2,arrow="last")
    def point_xy(x,y,colour=THEME["accent"],radius=5):
        canvas.create_oval(origin_x+x*step-radius,origin_y-y*step-radius,origin_x+x*step+radius,origin_y-y*step+radius,fill=colour,outline="")
    if "line" in spec:
        m,c=spec["line"]; x1,x2=-12,12
        canvas.create_line(origin_x+x1*step,origin_y-(m*x1+c)*step,origin_x+x2*step,origin_y-(m*x2+c)*step,fill=THEME["accent"],width=3)
    if "quadratic" in spec:
        a,b,c=spec["quadratic"]; points=[]
        for i in range(-120,121):
            x=i/20; y=a*x*x+b*x+c
            points.extend((origin_x+x*step,origin_y-y*step))
        canvas.create_line(*points,fill=THEME["accent"],width=3,smooth=True)
    if "point" in spec:
        x,y=spec["point"]; point_xy(x,y,"#FFB84D",7)
        if "vector" in spec:
            dx,dy=spec["vector"]; canvas.create_line(origin_x+x*step,origin_y-y*step,origin_x+(x+dx)*step,origin_y-(y+dy)*step,fill="#58D68D",width=3,arrow="last")
    selected = canvas.create_oval(0,0,0,0,outline="#FFB84D",width=3)
    def choose(event):
        x=round((event.x-origin_x)/step); y=round((origin_y-event.y)/step)
        canvas.coords(selected,origin_x+x*step-8,origin_y-y*step-8,origin_x+x*step+8,origin_y-y*step+8)
        mode=spec.get("answer_mode")
        if mode == "point": response.set(f"{x},{y}")
        elif mode == "x_intercept": response.set(str(x))
        elif spec.get("select_x") == x:
            if "line" in spec: response.set(str(spec["line"][0]*x+spec["line"][1]))
        _set_status(status,f"Selected coordinate ({x}, {y})")
    canvas.bind("<Button-1>",choose)


def _bar_chart(canvas, status, response, spec):
    labels, values = spec["labels"], spec["values"]; maximum=max(values)+2; base=235; gap=125; start=85
    canvas.create_line(55,25,55,base,fill=THEME["fg"],width=2); canvas.create_line(55,base,WIDTH-30,base,fill=THEME["fg"],width=2)
    for tick in range(maximum+1):
        y=base-tick*190/maximum
        if tick%2==0: canvas.create_text(38,y,text=str(tick),fill=THEME.get("muted",THEME["fg"]),font=("Segoe UI",8))
    bars=[]
    for index,(label,value) in enumerate(zip(labels,values)):
        x=start+index*gap; top=base-value*190/maximum
        item=canvas.create_rectangle(x,top,x+58,base,fill=THEME["accent"],outline="",tags=("bar",str(index)))
        canvas.create_text(x+29,base+18,text=label,fill=THEME["fg"],font=FONT_TEXT); bars.append(item)
    def choose(event):
        found=canvas.find_closest(event.x,event.y)[0]
        tags=canvas.gettags(found)
        if "bar" not in tags:return
        index=int(tags[1]); response.set(str(values[index])); _set_status(status,f"{labels[index]} has frequency {values[index]}")
        for item in bars:canvas.itemconfigure(item,fill=THEME["accent"])
        canvas.itemconfigure(found,fill="#FFB84D")
    canvas.bind("<Button-1>",choose)


def _pie_chart(canvas, status, response, spec):
    numerator,denominator=spec["fraction"]; angle=360*numerator/denominator; box=(220,35,460,275)
    canvas.create_oval(*box,fill=THEME.get("panel_alt",THEME["bg"]),outline=THEME["fg"],width=2)
    sector=canvas.create_arc(*box,start=90,extent=-angle,fill=THEME["accent"],outline=THEME["fg"],width=2)
    def choose(event):
        canvas.itemconfigure(sector,fill="#FFB84D"); response.set(str(angle)); _set_status(status,f"Selected sector: {angle:g}°")
    canvas.bind("<Button-1>",choose)


def _circle_parts(canvas, status, response, spec):
    cx,cy,r=WIDTH//2,135,100
    circumference=canvas.create_oval(cx-r,cy-r,cx+r,cy+r,outline=THEME["accent"],width=7,tags="circumference")
    radius=canvas.create_line(cx,cy,cx+r,cy,fill="#58D68D",width=7,tags="radius")
    diameter=canvas.create_line(cx-r,cy+30,cx+r,cy+30,fill="#FFB84D",width=7,tags="diameter")
    canvas.create_oval(cx-5,cy-5,cx+5,cy+5,fill=THEME["fg"],outline="")
    items={circumference:"circumference",radius:"radius",diameter:"diameter"}
    def choose(event):
        item=canvas.find_closest(event.x,event.y)[0]; answer=items.get(item)
        if answer: response.set(answer); _set_status(status,f"Selected: {answer}")
    canvas.bind("<Button-1>",choose)


def _circle_measure(canvas, status, response, spec):
    cx,cy,r=WIDTH//2,135,95; canvas.create_oval(cx-r,cy-r,cx+r,cy+r,outline=THEME["accent"],width=4)
    canvas.create_line(cx,cy,cx+r,cy,fill="#FFB84D",width=4,arrow="last"); canvas.create_text(cx+r/2,cy-18,text=f"r = {spec['radius']} cm",fill=THEME["fg"],font=FONT_TEXT)
    canvas.bind("<Button-1>",lambda e:_set_status(status,"Radius highlighted · use A = πr² or C = 2πr"))


def _fraction_strip(canvas, status, response, spec):
    parts,shaded=spec["parts"],spec["shaded"]; left,right,top,bottom=80,WIDTH-80,85,190; width=(right-left)/parts
    cells=[]
    for i in range(parts): cells.append(canvas.create_rectangle(left+i*width,top,left+(i+1)*width,bottom,fill=THEME["accent"] if i<shaded else THEME.get("panel_alt",THEME["bg"]),outline=THEME["fg"],width=2))
    def choose(event):
        index=max(0,min(parts-1,int((event.x-left)/width))); canvas.itemconfigure(cells[index],fill="#FFB84D"); _set_status(status,f"Part {index+1} of {parts}")
    canvas.bind("<Button-1>",choose)


def _percentage_bar(canvas, status, response, spec):
    percent=spec["percent"]; left,right,top,bottom=70,WIDTH-70,100,175; split=left+(right-left)*percent/100
    canvas.create_rectangle(left,top,right,bottom,fill=THEME.get("panel_alt",THEME["bg"]),outline=THEME["fg"],width=2)
    fill=canvas.create_rectangle(left,top,split,bottom,fill=THEME["accent"],outline="")
    label=canvas.create_text(split,75,text=f"{percent}%",fill=THEME["fg"],font=FONT_TEXT)
    def drag(event):
        value=max(0,min(100,round((event.x-left)/(right-left)*100))); x=left+(right-left)*value/100
        canvas.coords(fill,left,top,x,bottom); canvas.coords(label,x,75); canvas.itemconfigure(label,text=f"{value}%"); _set_status(status,f"Exploring {value}%")
    canvas.bind("<Button-1>",drag); canvas.bind("<B1-Motion>",drag)


def _ratio_blocks(canvas, status, response, spec):
    left_count,right_count=spec["left"],spec["right"]; total=left_count+right_count; size=min(58,500/total); x0=(WIDTH-total*size)/2
    blocks=[]
    for i in range(total): blocks.append(canvas.create_rectangle(x0+i*size,95,x0+(i+1)*size-4,165,fill=THEME["accent"] if i<left_count else "#B56BFF",outline=""))
    canvas.create_text(WIDTH/2,205,text=f"{left_count} : {right_count}",fill=THEME["fg"],font=("Segoe UI",18,"bold"))
    canvas.bind("<Button-1>",lambda e:_set_status(status,f"{total} equal parts altogether"))


def _sample_space(canvas, status, response, spec):
    rows,columns=spec["rows"],spec["columns"]; size=72; x0,y0=WIDTH/2-size*len(columns)/2,55
    for r,row in enumerate(rows):
        for c,column in enumerate(columns):
            outcome=f"{row}{column}"; item=canvas.create_rectangle(x0+c*size,y0+r*size,x0+(c+1)*size,y0+(r+1)*size,fill=THEME.get("panel_alt",THEME["bg"]),outline=THEME["fg"],tags=("cell",outcome))
            canvas.create_text(x0+(c+.5)*size,y0+(r+.5)*size,text=outcome,fill=THEME["fg"],font=FONT_TEXT,tags=("text",outcome))
    def choose(event):
        item=canvas.find_closest(event.x,event.y)[0]; tags=canvas.gettags(item)
        if len(tags)>1:_set_status(status,f"Outcome selected: {tags[1]}")
    canvas.bind("<Button-1>",choose)


def _probability_scale(canvas, status, response, spec):
    left,right,y=80,WIDTH-80,140; value=spec["value"]; x=left+value*(right-left)
    canvas.create_line(left,y,right,y,fill=THEME["fg"],width=5); canvas.create_text(left,y+30,text="0",fill=THEME["fg"],font=FONT_TEXT); canvas.create_text(right,y+30,text="1",fill=THEME["fg"],font=FONT_TEXT)
    marker=canvas.create_oval(x-11,y-11,x+11,y+11,fill=THEME["accent"],outline="")
    canvas.bind("<Button-1>",lambda e:(canvas.itemconfigure(marker,fill="#FFB84D"),_set_status(status,f"Complement: {1-value:g}")))


def _shape_scale(canvas, status, response, spec):
    scale=spec["scale"]; original=[(100,190),(170,190),(145,115)]; enlarged=[(360,210),(360+70*scale,210),(360+45*scale,210-75*scale)]
    canvas.create_polygon(*sum(original,()),fill=THEME["accent"],outline=THEME["fg"],width=2)
    target=canvas.create_polygon(*sum(enlarged,()),fill="#B56BFF",outline=THEME["fg"],width=2,state="hidden")
    shown={"value":False}
    def toggle(event):
        shown["value"]=not shown["value"]; canvas.itemconfigure(target,state="normal" if shown["value"] else "hidden"); _set_status(status,f"Scale factor {scale} · click to compare")
    canvas.bind("<Button-1>",toggle)


def _triangles(canvas, status, response, spec):
    first=[(90,210),(230,210),(145,65)]; second=[(390,210),(530,210),(445,65)]
    canvas.create_polygon(*sum(first,()),outline=THEME["accent"],fill="",width=4); canvas.create_polygon(*sum(second,()),outline="#B56BFF",fill="",width=4)
    canvas.create_text(WIDTH/2,245,text=f"Evidence shown for {spec['rule']}",fill=THEME["fg"],font=FONT_TEXT)
    canvas.bind("<Button-1>",lambda e:(response.set(spec["rule"]),_set_status(status,f"Selected congruence rule: {spec['rule']}")))


def _prism(canvas, status, response, spec):
    l,w,h=spec["dimensions"]; offset={"value":35}
    def draw():
        canvas.delete("all"); x,y=220,75; dx,dy=offset["value"],-30; rw,rh=220,130
        canvas.create_rectangle(x,y,x+rw,y+rh,outline=THEME["accent"],width=4)
        canvas.create_polygon(x,y,x+dx,y+dy,x+rw+dx,y+dy,x+rw,y,fill="",outline="#B56BFF",width=3)
        canvas.create_polygon(x+rw,y,x+rw+dx,y+dy,x+rw+dx,y+rh+dy,x+rw,y+rh,fill="",outline="#B56BFF",width=3)
        canvas.create_text(x+rw/2,y+rh+25,text=f"length {l} cm",fill=THEME["fg"],font=FONT_TEXT)
        canvas.create_text(x-45,y+rh/2,text=f"height {h} cm",fill=THEME["fg"],font=FONT_TEXT)
        canvas.create_text(x+rw+55,y-20,text=f"width {w} cm",fill=THEME["fg"],font=FONT_TEXT)
    def rotate(event): offset["value"]=-offset["value"]; draw(); _set_status(status,"View rotated · dimensions stay unchanged")
    draw(); canvas.bind("<Button-1>",rotate)


def _construction(canvas, status, response, spec):
    x1,x2,y=190,470,145; radius=185
    canvas.create_line(x1,y,x2,y,fill=THEME["fg"],width=4)
    canvas.create_oval(x1-radius,y-radius,x1+radius,y+radius,outline=THEME["accent"],width=2,dash=(5,4))
    canvas.create_oval(x2-radius,y-radius,x2+radius,y+radius,outline="#B56BFF",width=2,dash=(5,4))
    canvas.create_line(WIDTH/2,20,WIDTH/2,265,fill="#FFB84D",width=4,dash=(8,4))
    canvas.create_text(x1,y+25,text="A",fill=THEME["fg"],font=FONT_TEXT); canvas.create_text(x2,y+25,text="B",fill=THEME["fg"],font=FONT_TEXT)
    def choose(event):
        response.set("perpendicular bisector"); _set_status(status,"Equal compass arcs locate the perpendicular bisector")
    canvas.bind("<Button-1>",choose)


def _pictogram(canvas, status, response, spec):
    labels,counts,key=spec["labels"],spec["counts"],spec.get("key",2); x0,y0=130,55
    canvas.create_text(WIDTH-120,25,text=f"★ = {key}",fill=THEME["fg"],font=FONT_TEXT)
    for row,(label,count) in enumerate(zip(labels,counts)):
        y=y0+row*50; canvas.create_text(75,y,text=label,fill=THEME["fg"],font=FONT_TEXT)
        for index in range(count): canvas.create_text(x0+index*42,y,text="★",fill=THEME["accent"],font=("Segoe UI",20),tags=("icon",str(row)))
    def choose(event):
        item=canvas.find_closest(event.x,event.y)[0]; tags=canvas.gettags(item)
        if "icon" in tags:
            row=int(tags[1]); response.set(str(counts[row]*key)); _set_status(status,f"{labels[row]} represents {counts[row]*key}")
    canvas.bind("<Button-1>",choose)


def _line_plot(canvas, status, response, spec):
    values=spec["values"]; low,high=min(values)-1,max(values)+1; left,right,y=70,WIDTH-50,210
    canvas.create_line(left,y,right,y,fill=THEME["fg"],width=3)
    for value in range(low,high+1):
        x=left+(value-low)/(high-low)*(right-left); canvas.create_line(x,y-8,x,y+8,fill=THEME["fg"]); canvas.create_text(x,y+25,text=str(value),fill=THEME["fg"],font=("Segoe UI",9))
        count=values.count(value)
        for level in range(count): canvas.create_text(x,y-22-level*25,text="×",fill=THEME["accent"],font=("Segoe UI",18,"bold"),tags=("dot",str(value)))
    def choose(event):
        item=canvas.find_closest(event.x,event.y)[0]; tags=canvas.gettags(item)
        if "dot" in tags:
            value=int(tags[1]); response.set(str(values.count(value))); _set_status(status,f"Frequency at {value}: {values.count(value)}")
    canvas.bind("<Button-1>",choose)


def _scatter_plot(canvas, status, response, spec):
    points=spec["points"]; left,bottom,scale_x,scale_y=70,235,45,18
    canvas.create_line(left,20,left,bottom,fill=THEME["fg"],width=2); canvas.create_line(left,bottom,WIDTH-30,bottom,fill=THEME["fg"],width=2)
    items=[]
    for x,y in points: items.append(canvas.create_oval(left+x*scale_x-5,bottom-y*scale_y-5,left+x*scale_x+5,bottom-y*scale_y+5,fill=THEME["accent"],outline=""))
    def choose(event):
        item=canvas.find_closest(event.x,event.y)[0]
        if item in items: canvas.itemconfigure(item,fill="#FFB84D"); _set_status(status,"Point selected · describe the overall trend, not one point")
    canvas.bind("<Button-1>",choose)


def _stacked_bar(canvas, status, response, spec):
    parts=spec["parts"]; colours=[THEME["accent"],"#B56BFF","#58D68D","#FFB84D"]; total=sum(parts); left,right,top,bottom=75,WIDTH-75,105,175; x=left
    for index,value in enumerate(parts):
        next_x=x+(right-left)*value/total; canvas.create_rectangle(x,top,next_x,bottom,fill=colours[index%len(colours)],outline=THEME["fg"],tags=("part",str(index))); canvas.create_text((x+next_x)/2,(top+bottom)/2,text=str(value),fill="#FFFFFF",font=FONT_TEXT); x=next_x
    canvas.create_text(WIDTH/2,215,text=f"Total = {total}",fill=THEME["fg"],font=FONT_TEXT)
    def choose(event): response.set(str(total)); _set_status(status,f"All stacked sections total {total}")
    canvas.bind("<Button-1>",choose)


def _grouped_table(canvas, status, response, spec):
    groups,frequencies=spec["groups"],spec["frequencies"]; x0,y0,width,row_h=150,45,360,42
    canvas.create_rectangle(x0,y0,x0+width,y0+row_h,fill=THEME["accent"],outline=THEME["fg"])
    canvas.create_text(x0+width*.3,y0+row_h/2,text="Group",fill="#FFFFFF",font=FONT_TEXT); canvas.create_text(x0+width*.75,y0+row_h/2,text="Frequency",fill="#FFFFFF",font=FONT_TEXT)
    for index,(group,freq) in enumerate(zip(groups,frequencies)):
        y=y0+(index+1)*row_h; canvas.create_rectangle(x0,y,x0+width,y+row_h,fill=THEME.get("panel_alt",THEME["bg"]),outline=THEME.get("border",THEME["fg"]),tags=("row",str(index)))
        canvas.create_text(x0+width*.3,y+row_h/2,text=group,fill=THEME["fg"],font=FONT_TEXT,tags=("row",str(index))); canvas.create_text(x0+width*.75,y+row_h/2,text=str(freq),fill=THEME["fg"],font=FONT_TEXT,tags=("row",str(index)))
    def choose(event):
        item=canvas.find_closest(event.x,event.y)[0]; tags=canvas.gettags(item)
        if "row" in tags:
            index=int(tags[1]); response.set(str(frequencies[index])); _set_status(status,f"{groups[index]} has frequency {frequencies[index]}")
    canvas.bind("<Button-1>",choose)


def _compound_prism(canvas, status, response, spec):
    a,b=spec["volumes"]; canvas.create_rectangle(120,105,350,220,fill=THEME["accent"],outline=THEME["fg"],width=3); canvas.create_rectangle(350,55,535,220,fill="#B56BFF",outline=THEME["fg"],width=3)
    canvas.create_text(235,160,text=f"Volume {a}",fill="#FFFFFF",font=FONT_TEXT); canvas.create_text(442,135,text=f"Volume {b}",fill="#FFFFFF",font=FONT_TEXT)
    def choose(event): response.set(str(a+b)); _set_status(status,f"Combined volume: {a} + {b} = {a+b}")
    canvas.bind("<Button-1>",choose)


def _balance_scale(canvas, status, response, spec):
    centre=WIDTH//2; canvas.create_line(centre,55,centre,225,fill=THEME["fg"],width=5); canvas.create_polygon(centre-45,245,centre+45,245,centre,205,fill=THEME.get("panel_alt",THEME["bg"]),outline=THEME["fg"])
    beam=canvas.create_line(145,105,WIDTH-145,105,fill=THEME["accent"],width=8)
    canvas.create_line(195,105,165,185,fill=THEME["fg"],width=2); canvas.create_line(WIDTH-195,105,WIDTH-165,185,fill=THEME["fg"],width=2)
    canvas.create_arc(115,155,215,215,start=180,extent=180,style="arc",outline="#FFB84D",width=4); canvas.create_arc(WIDTH-215,155,WIDTH-115,215,start=180,extent=180,style="arc",outline="#58D68D",width=4)
    canvas.create_text(165,180,text="x + a",fill=THEME["fg"],font=FONT_TEXT); canvas.create_text(WIDTH-165,180,text="b",fill=THEME["fg"],font=FONT_TEXT)
    canvas.bind("<Button-1>",lambda e:(canvas.itemconfigure(beam,fill="#58D68D"),_set_status(status,"Whatever operation you use, apply it to both sides")))


def diagram_for_family(family, question):
    """Provide an exploratory visual for non-Year-8 maths families."""
    answer=question.get("answer")
    try: numeric=float(answer)
    except (TypeError,ValueError): numeric=None
    if family == "number" and numeric is not None and -20 <= numeric <= 20:
        return {"kind":"number_line","min":-20,"max":20,"target":numeric,"response_mode":False}
    if family == "fractions": return {"kind":"fraction_strip","parts":8,"shaded":3}
    if family in ("ratio","proportion"): return {"kind":"ratio_blocks","left":2,"right":3}
    if family == "algebra": return {"kind":"balance_scale"}
    if family == "geometry": return {"kind":"shape_scale","scale":2}
    if family == "statistics":
        value=max(1,min(12,round(numeric or 6))); return {"kind":"bar_chart","labels":["A","B","C","D"],"values":[3,value,7,5],"target":"B"}
    if family == "probability": return {"kind":"probability_scale","value":max(0,min(1,numeric if numeric is not None else .4))}
    if family == "graphs":
        gradient=max(-4,min(4,numeric if numeric is not None else 2)); return {"kind":"coordinate_grid","line":[gradient,1]}
    if family == "reasoning": return {"kind":"percentage_bar","percent":65}
    return None
