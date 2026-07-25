"""Detailed Year 8 maths curriculum and question generation.

The chapter and unit sequence is based on the curriculum supplied for EduPy.
Repeated units may appear in more than one chapter, while progress is recorded
against one stable unit id.
"""

import math
import random
from fractions import Fraction


def _unit(unit_id, title, focus, family):
    return {"id": unit_id, "title": title, "focus": focus, "family": family}


UNITS = {
    item["id"]: item for item in (
        _unit("power_notation", "Power notation and simple powers", "Repeated multiplication; square and cube numbers; calculating simple powers.", "powers"),
        _unit("hcf_lcm", "Highest common factor and lowest common multiple", "Listing multiples and factors for two or more numbers; applying HCF and LCM.", "factors"),
        _unit("prime_numbers", "Prime numbers", "Recognising primes; prime sequences; the sieve of Eratosthenes.", "factors"),
        _unit("negative_add_subtract", "Adding and subtracting positive and negative numbers", "Integer, decimal and fractional calculations; missing values; midpoints.", "negatives"),
        _unit("negative_multiply_divide", "Multiplying and dividing positive and negative numbers", "Sign rules; decimals and fractions; operation grids and missing values.", "negatives"),
        _unit("roots_further_powers", "Roots and further powers", "Integer powers; square and cube roots; estimates; order of operations.", "powers"),
        _unit("prime_factorisation", "Prime factorisation of a number", "Products of prime factors, including index notation.", "factors"),

        _unit("translations", "Translating a shape using directional language", "Translate and describe translations on a unit grid.", "transformations"),
        _unit("constructions", "Constructions with lines and angles", "Perpendicular and angle bisectors; perpendicular lines; accurate angles.", "constructions"),
        _unit("describe_integer_enlargement", "Describing an enlargement with a positive integer scale factor", "Identify and describe integer scale factors.", "transformations"),
        _unit("integer_enlargement", "Enlarging a shape by a positive integer scale factor", "Enlarge from a centre on coordinate and unit grids.", "transformations"),

        _unit("sample_spaces", "Sample space diagrams", "List combined outcomes; use arithmetic operators; calculate probabilities.", "probability"),
        _unit("mutually_exclusive", "Probabilities of mutually exclusive events", "Complements; event A or B; theoretical and expected frequency.", "probability"),
        _unit("experimental_probability", "Experimental probabilities, expectation and bias", "Relative frequency; expected values; reliability and bias.", "probability"),

        _unit("percentage_amount", "Calculating a simple percentage of an amount", "Find 50%, 10%, 5%, 1%, 25% and combined percentages by chunking.", "percentages"),
        _unit("percentage_of_number", "Determining what percentage one number is of another", "Convert a part of an amount into a percentage.", "percentages"),
        _unit("percentage_change", "Percentage change", "Calculate percentage increase, decrease, profit and loss.", "percentages"),
        _unit("percentage_over_100", "Percentage of an amount greater than 100%", "Use chunking to calculate percentages above 100%.", "percentages"),
        _unit("percentage_multipliers", "Percentage of an amount using decimal multipliers", "Multipliers above and below 100%; simple interest; reverse contexts.", "percentages"),

        _unit("congruent_shapes", "Properties of congruent shapes", "Identify congruent shapes and corresponding equal lengths and angles.", "congruence"),
        _unit("triangle_congruence", "Proving triangle congruence using SSS, SAS, ASA and RHS", "Select and apply valid triangle congruence tests.", "congruence"),

        _unit("cube_cuboid_volume", "Volume of a cube or cuboid", "Calculate volume and use cuboid nets.", "mensuration"),
        _unit("prism_volume", "Volume of a prism", "Use cross-sectional area and find missing dimensions.", "mensuration"),
        _unit("surface_area_prisms", "Surface area of cuboids and prisms", "Surface area, missing dimensions and costs.", "mensuration"),
        _unit("compound_volume", "Volume of more complex compound 3D shapes", "Combine and subtract prisms, cylinders, pyramids, cones and hemispheres.", "mensuration"),

        _unit("line_from_table", "Plotting a straight line from a table of values", "Complete tables and plot linear graphs using two or more points.", "graphs"),
        _unit("line_and_equation", "Relationship between a line and its equation", "Test points; find missing coordinates; use y = mx + c and standard form.", "graphs"),
        _unit("line_intercepts", "x and y intercepts of a line", "Find intercepts, their midpoint, enclosed areas and intermediate points.", "graphs"),
        _unit("gradient", "Gradient of a line", "Positive, negative and fractional gradients; slope triangles; collinearity.", "graphs"),
        _unit("line_equations", "Understanding the equation of a straight line", "Use slope-intercept and standard form; compare steepness.", "graphs"),
        _unit("drawing_lines", "Drawing a line from its equation", "Draw lines from y = mx + c, x + y = a and ax + by = c.", "graphs"),
        _unit("quadratic_graphs", "Plotting quadratic graphs from a table of values", "Complete tables, test points and plot y = ax² + bx + c.", "graphs"),

        _unit("rounding_place_value", "Rounding to the nearest 10, 100, 1000 and beyond", "Round whole numbers to a stated power of ten.", "rounding"),
        _unit("integer_powers_ten", "Multiplying and dividing integers by 10, 100 and 1000", "Scale integers using powers and multiples of ten.", "rounding"),
        _unit("decimal_powers_ten", "Multiplying and dividing decimals by 10, 100 and 1000", "Place-value shifts with decimals and positive powers of ten.", "rounding"),
        _unit("decimal_places", "Rounding to a given number of decimal places", "Round positive decimals to a stated number of places.", "rounding"),
        _unit("significant_figures", "Rounding to a given number of significant figures", "Round large and small numbers to one or more significant figures.", "rounding"),
        _unit("standard_form", "Converting to and from standard form", "Write, compare and order ordinary and standard-form numbers.", "standard_form"),
        _unit("standard_form_operations", "Multiplying and dividing numbers in standard form", "Multiply, divide and adjust standard-form answers.", "standard_form"),

        _unit("line_dot_plots", "Line and dot plots", "Read, complete, total and compare frequencies.", "data"),
        _unit("pictograms", "Pictograms", "Read keys; calculate totals and differences; determine a missing key.", "data"),
        _unit("bar_line_charts", "Bar charts and vertical line charts", "Read, draw, total, compare and interpret discrete and grouped charts.", "data"),
        _unit("simple_graphs", "Interpreting and presenting data in simple graphs", "Interpret line, scatter, time and other simple graphs.", "data"),
        _unit("simple_pie_charts", "Pie charts with simple fractions and percentages", "Draw and interpret equal sectors, angles, fractions and percentages.", "data"),
        _unit("scatter_graphs", "Scatter graphs and correlation", "Plot points; identify outliers, correlation and line-of-best-fit estimates.", "data"),

        _unit("algebraic_thinking", "Algebraic thinking", "Constraints, relationships, missing values, magic squares and overlapping structures.", "algebra"),
        _unit("numerical_index_laws", "Numerical index laws", "Multiply and divide powers; powers of powers; zero and unknown indices.", "powers"),
        _unit("algebraic_terminology", "Algebraic terminology", "Constants, variables, terms, expressions, equations and formulae.", "algebra"),
        _unit("multiply_terms", "Multiplying single algebraic terms", "Multiply variables and positive or negative coefficients.", "algebra"),
        _unit("divide_terms", "Dividing single algebraic terms", "Divide coefficients and variables; combine multiplication and division.", "algebra"),
        _unit("collect_like_terms", "Collecting like terms", "Combine positive and negative like terms with powers and variables.", "algebra"),
        _unit("algebraic_index_laws", "Algebraic index laws", "Multiply, divide and power algebraic terms; zero, negative and fractional indices.", "powers"),
        _unit("forming_expressions", "Forming linear expressions and formulae from context", "Build expressions and formulae for rules, perimeter, area and cost.", "algebra"),
        _unit("expand_single_bracket", "Expanding a single bracket", "Expand and simplify positive, negative and algebraic multipliers.", "algebra"),

        _unit("ratio_scaling", "Multiplicative scaling and ratio notation", "Related facts; repeated addition and multiplication; unequal shares and recipes.", "ratio"),
        _unit("similar_shapes", "Similar shapes with integer scale factors", "Represent and calculate corresponding lengths and integer scale factors.", "ratio"),
        _unit("scale_drawings", "Scale drawings including map scales", "Convert real and drawing measurements; maps, bearings and estimates.", "ratio"),
        _unit("describe_fractional_enlargement", "Describing enlargement with a positive fractional scale factor", "Recognise and describe decimal and fractional scale factors.", "transformations"),
        _unit("fractional_enlargement", "Enlarging a shape by a positive fractional scale factor", "Enlarge with unit, proper-fraction and improper-fraction scales.", "transformations"),

        _unit("fractions_same_denominator", "Adding and subtracting fractions with the same denominator", "Proper and improper fractions; answers within or beyond one whole.", "fractions"),
        _unit("fractions_of_amount", "Fractions of an amount", "Unit and non-unit fractions, including denominators up to 12.", "fractions"),
        _unit("fractions_related_denominators", "Adding and subtracting fractions with related denominators", "Convert one denominator before calculating.", "fractions"),
        _unit("fractions_any_denominator", "Adding and subtracting fractions with any denominator", "Use common denominators and find missing portions.", "fractions"),
        _unit("mixed_add_subtract", "Adding and subtracting mixed numbers with different denominators", "Regroup and exchange; proper and improper answers.", "fractions"),
        _unit("fraction_times_integer", "Multiplying fractions and mixed numbers by an integer", "Multiply proper fractions and mixed numbers by whole numbers.", "fractions"),
        _unit("proper_fraction_multiply", "Multiplying proper fractions", "Multiply, simplify and square fractions.", "fractions"),
        _unit("fraction_divide_integer", "Dividing fractions by integers", "Divide fractions and mixed numbers; locate fractional midpoints.", "fractions"),
        _unit("decimal_times_integer", "Multiplying a decimal by an integer", "Multiply decimals up to two decimal places by whole numbers.", "decimals"),
        _unit("decimal_multiplication", "Multiplying decimal numbers", "Use place value, equivalent fractions and related calculations.", "decimals"),
        _unit("decimal_divide_integer", "Dividing a decimal by an integer", "Exact division, extra decimal places and fractional midpoints.", "decimals"),
        _unit("decimal_division", "Dividing by decimal numbers", "Use related facts, equivalent fractions and place value.", "decimals"),
        _unit("fraction_multiply_advanced", "Further multiplying proper fractions", "Simplify, use powers and find fractions of capacities.", "fractions"),
        _unit("proper_improper_division", "Dividing proper and improper fractions", "Simplify fractional values and multi-operation expressions.", "fractions"),
        _unit("mixed_number_multiply", "Multiplying fractions involving a mixed number", "Multiply mixed numbers and combine fractional operations.", "fractions"),
        _unit("mixed_number_divide", "Dividing fractions involving a mixed number", "Divide mixed and non-mixed values and solve contexts.", "fractions"),
        _unit("fraction_amount_problems", "Problem solving involving a fraction of an amount", "Groups, totals, original amounts and repeated fractions.", "fractions"),

        _unit("numerical_proportion", "Multiplicative scaling and numerical proportion relationships", "Direct proportion, tables, recipes, best value and scaled quantities.", "ratio"),
        _unit("exchange_rates", "Exchange rates", "Convert currencies, compare rates, include commission and multi-step contexts.", "ratio"),
        _unit("conversion_graphs", "Conversion graphs", "Draw, read and extrapolate conversion graphs.", "graphs"),
        _unit("real_life_graphs", "Real-life linear graphs", "Gradient, intercept, linear models and lines of best fit in context.", "graphs"),

        _unit("circle_terms", "Basic terms in relation to circles", "Radius, diameter, circumference, semicircles and quarter circles.", "circles"),
        _unit("circumference", "Circumference of a full circle", "Calculate exact and decimal circumferences; inverse and wheel problems.", "circles"),
        _unit("circle_area", "Area of a full circle", "Calculate exact and decimal areas; inverse and related-shape problems.", "circles"),

        _unit("linear_equations_one_side", "Solving linear equations with the variable on one side", "One-, two- and multi-step equations with integers and fractions.", "equations"),
        _unit("change_subject_simple", "Changing the subject where the variable appears once", "One or more inverse steps, including squares and roots.", "equations"),
        _unit("linear_equations_brackets", "Solving linear equations on one side including brackets", "Positive, fractional and negative solutions with brackets.", "equations"),
        _unit("linear_equations_both_sides", "Solving linear equations with the variable on both sides", "Unknowns and brackets on both sides.", "equations"),
        _unit("linear_equations_fractions", "Solving linear equations involving fractions", "Solve increasingly complex linear fractional equations.", "equations"),
        _unit("change_subject_advanced", "Changing the subject including brackets, powers and roots", "Rearrange multi-step formulae including fractional coefficients.", "equations"),

        _unit("dual_stacked_bars", "Dual and stacked bar charts", "Read, compare and calculate totals and differences.", "data"),
        _unit("pie_charts_any", "Pie charts with any proportion", "Draw and interpret marked angles, fractions, percentages and totals.", "data"),
        _unit("grouped_frequency", "Forming a grouped frequency table", "Read and create grouped tables using inequality notation.", "data"),
    )
}


CHAPTERS = [
    ("number_powers", "Number", ["power_notation", "hcf_lcm", "prime_numbers", "negative_add_subtract", "negative_multiply_divide", "roots_further_powers", "prime_factorisation"]),
    ("geometry", "Geometry", ["translations", "constructions", "describe_integer_enlargement", "integer_enlargement"]),
    ("probability", "Probability", ["sample_spaces", "mutually_exclusive", "experimental_probability"]),
    ("percentages", "Percentages", ["percentage_amount", "percentage_of_number", "percentage_change", "percentage_over_100", "percentage_multipliers"]),
    ("congruence", "Congruent Shapes", ["congruent_shapes", "triangle_congruence"]),
    ("mensuration", "Surface Area and Volume of Prisms", ["cube_cuboid_volume", "prism_volume", "surface_area_prisms", "compound_volume"]),
    ("graphs", "Graphs", ["line_from_table", "line_and_equation", "line_intercepts", "gradient", "line_equations", "drawing_lines", "quadratic_graphs"]),
    ("number_rounding", "Number: Rounding and Standard Form", ["rounding_place_value", "integer_powers_ten", "decimal_powers_ten", "decimal_places", "significant_figures", "standard_form", "standard_form_operations"]),
    ("interpreting_data", "Interpreting Data", ["line_dot_plots", "pictograms", "bar_line_charts", "simple_graphs", "simple_pie_charts", "scatter_graphs"]),
    ("algebra", "Algebra", ["algebraic_thinking", "numerical_index_laws", "algebraic_terminology", "multiply_terms", "divide_terms", "collect_like_terms", "algebraic_index_laws", "forming_expressions", "expand_single_bracket"]),
    ("shape_ratio", "Shape and Ratio", ["ratio_scaling", "similar_shapes", "scale_drawings", "integer_enlargement", "describe_fractional_enlargement", "fractional_enlargement"]),
    ("fractions_decimals", "Fractions and Decimals", ["fractions_same_denominator", "fractions_of_amount", "fractions_related_denominators", "fractions_any_denominator", "mixed_add_subtract", "fraction_times_integer", "proper_fraction_multiply", "fraction_divide_integer", "decimal_times_integer", "decimal_multiplication", "decimal_divide_integer", "decimal_division", "fraction_multiply_advanced", "proper_improper_division", "mixed_number_multiply", "mixed_number_divide", "fraction_amount_problems"]),
    ("proportion", "Proportion", ["ratio_scaling", "numerical_proportion", "exchange_rates", "conversion_graphs", "real_life_graphs"]),
    ("circles", "Circles", ["circle_terms", "circumference", "circle_area"]),
    ("equations", "Equations and Formulae", ["forming_expressions", "linear_equations_one_side", "change_subject_simple", "linear_equations_brackets", "linear_equations_both_sides", "linear_equations_fractions", "change_subject_advanced"]),
    ("comparing_data", "Comparing Data", ["pictograms", "bar_line_charts", "simple_graphs", "simple_pie_charts", "dual_stacked_bars", "pie_charts_any", "grouped_frequency"]),
]


def chapters():
    return [(chapter_id, title, [UNITS[unit_id] for unit_id in unit_ids]) for chapter_id, title, unit_ids in CHAPTERS]


def topics():
    seen = set()
    result = []
    for _, _, unit_ids in CHAPTERS:
        for unit_id in unit_ids:
            if unit_id not in seen:
                seen.add(unit_id); result.append((unit_id, UNITS[unit_id]["title"]))
    return result


def details(topic):
    return UNITS.get(topic)


FAMILY_GUIDES = {
    "powers": ("Write repeated multiplication in index form and apply the index laws only when the bases match.", "Rewrite the power, identify the shared base, apply the correct law, then check by evaluating a small example.", "2³ × 2² = 2⁵ = 32.", "Multiplying the powers instead of adding indices when multiplying equal bases.", "base, index, power, square, cube, root"),
    "factors": ("Factors divide exactly; multiples appear in a times table; prime factors are the building blocks of whole numbers.", "List systematically or use a factor tree, circle common values, then choose the greatest factor or least multiple required.", "24 = 2³ × 3, while HCF(12,18) = 6.", "Confusing a factor with a multiple or stopping a factor tree at a composite number.", "factor, multiple, prime, HCF, LCM, factorisation"),
    "negatives": ("Negative numbers extend the number line below zero and follow consistent sign rules.", "For addition and subtraction, track movement on a number line. For multiplication and division, decide the sign before calculating the magnitude.", "−4 − (−7) = −4 + 7 = 3.", "Treating two adjacent negative signs as a single negative.", "integer, negative, difference, product, quotient, midpoint"),
    "rounding": ("Rounding gives a nearby value at a chosen level of accuracy.", "Locate the required place, inspect the next digit, round up for 5–9, then replace later place values appropriately.", "4,837 to 2 significant figures is 4,800.", "Counting decimal places from the first non-zero digit when the question asks for decimal places.", "place value, decimal place, significant figure, accuracy, estimate"),
    "standard_form": ("Standard form writes numbers as a × 10ⁿ where 1 ≤ a < 10.", "Move the decimal to create a coefficient from 1 to 10; count places for the power; adjust after operations.", "45,000 = 4.5 × 10⁴.", "Leaving a coefficient of 10 or more, which is not valid standard form.", "coefficient, power of ten, standard form, ordinary number"),
    "fractions": ("Fractions describe division and parts of a whole; equivalent fractions have the same value.", "Use a common denominator for addition, multiply across for multiplication, and multiply by the reciprocal for division; simplify last.", "2/3 + 1/4 = 8/12 + 3/12 = 11/12.", "Adding denominators when adding fractions.", "numerator, denominator, equivalent, reciprocal, mixed number"),
    "decimals": ("Decimal operations depend on place value, not on the visual length of the number.", "Estimate first, calculate using an equivalent integer method, then restore the decimal position and check the size.", "1.2 × 0.4 = 0.48.", "Placing the decimal point without checking against an estimate.", "place value, product, quotient, decimal, equivalent"),
    "percentages": ("A percentage is a fraction out of 100 and can be calculated by chunking or using a multiplier.", "Identify the original amount, convert the percentage to useful chunks or a decimal, multiply, and label the result.", "15% of 80 = 10% + 5% = 8 + 4 = 12.", "Using the new amount as the denominator in percentage-change questions.", "percentage, multiplier, original, change, profit, loss"),
    "ratio": ("Ratio and proportion compare quantities multiplicatively.", "Keep units consistent, find one part or one unit, then scale all linked quantities by the same multiplier.", "Share 30 in 2:3: five parts means one part is 6, giving 12 and 18.", "Using addition when the relationship requires multiplication.", "ratio, proportion, scale factor, unit rate, conversion"),
    "algebra": ("Algebra represents general relationships using symbols, terms and operations.", "Identify like terms and operations, substitute carefully, then simplify in a clear order.", "3x + 5x = 8x, but 3x + 5 cannot be combined.", "Combining terms that do not have identical variable parts.", "term, coefficient, variable, expression, formula, substitute"),
    "equations": ("An equation stays balanced when the same valid operation is applied to both sides.", "Simplify each side, undo operations in reverse order, keep both sides balanced, then substitute to check.", "3x + 4 = 19 → 3x = 15 → x = 5.", "Moving a term across the equals sign without understanding the inverse operation.", "equation, inverse, solution, subject, rearrange, balance"),
    "probability": ("Probability measures likelihood from 0 to 1; a complete set of mutually exclusive outcomes totals 1.", "List the sample space, count equally likely outcomes, form the fraction, then use relative frequency for experimental estimates.", "Two coins have HH, HT, TH, TT, so P(one head) = 2/4.", "Missing ordered outcomes such as HT and TH.", "outcome, event, sample space, relative frequency, mutually exclusive"),
    "graphs": ("Coordinates and equations show how two variables are related.", "Create or read a value table, plot accurate coordinates, use change in y over change in x for gradient, and identify the intercept.", "For y = 2x + 1, the gradient is 2 and y-intercept is 1.", "Calculating gradient as change in x divided by change in y.", "coordinate, gradient, intercept, linear, quadratic, equation"),
    "transformations": ("Transformations change a shape's position or size according to a precise rule.", "Track each vertex, apply the vector or scale factor from the stated centre, then join corresponding points in order.", "Translating (2,1) by (3,−2) gives (5,−1).", "Scaling from the origin when a different centre of enlargement is given.", "translation, vector, enlargement, centre, scale factor, corresponding"),
    "constructions": ("Geometric constructions use compass arcs and straight lines to create exact relationships.", "Keep the compass width fixed, draw intersecting arcs, then join or extend through their intersection.", "A perpendicular bisector comes from equal-radius arcs centred at both endpoints.", "Changing the compass width between matching arcs.", "construct, bisect, perpendicular, compass, arc, locus"),
    "congruence": ("Congruent shapes have exactly the same size and shape, even after a rotation or reflection.", "Match corresponding sides and angles, then justify triangles using SSS, SAS, ASA or RHS.", "Two right triangles with equal hypotenuse and one equal side satisfy RHS.", "Using AAA, which proves similarity but not congruence.", "congruent, corresponding, SSS, SAS, ASA, RHS"),
    "mensuration": ("Volume measures 3D space and surface area totals the exposed 2D faces.", "Write dimensions with units, choose V = area of cross-section × length or total all faces, calculate, then use cubic or square units.", "A 3 × 4 × 5 cuboid has volume 60 cm³.", "Using square units for volume or forgetting hidden faces in surface area.", "volume, surface area, prism, cross-section, cubic units"),
    "circles": ("Circle measurements are linked through radius, diameter and π.", "Identify the radius, use d = 2r, then select C = 2πr or A = πr² and keep exact π form if requested.", "For r = 4, C = 8π and A = 16π.", "Squaring the radius in circumference or forgetting to square it in area.", "radius, diameter, circumference, area, pi, sector"),
    "data": ("Charts and tables represent frequencies so patterns and comparisons can be interpreted accurately.", "Read the title, axes and key, identify the scale, extract exact values, then calculate or compare only what the evidence supports.", "A quarter of a pie chart represents 90° and 25%.", "Ignoring a pictogram key or assuming correlation proves causation.", "frequency, scale, key, sector, correlation, grouped data"),
}


def guide(topic):
    unit = details(topic)
    if not unit:
        return None
    method = FAMILY_GUIDES[unit["family"]]
    return (f"{unit['focus']} {method[0]}", *method[1:])


def _q(prompt, answer, topic, explanation, kind="numeric", choices=None, accepted=None, diagram=None):
    return {"prompt": prompt, "answer": answer, "topic": topic, "explanation": explanation,
            "type": kind, "choices": choices or [], "accepted": accepted or [], "diagram": diagram}


def _round_sf(value, figures):
    if value == 0: return 0
    places = figures - int(math.floor(math.log10(abs(value)))) - 1
    return round(value, places)


def generate(topic):
    """Generate a checkable Year 8 question for every supplied unit."""
    unit = UNITS[topic]; family = unit["family"]
    if topic == "constructions":
        return _q("Click the construction, then name the line made by equal arcs from A and B.", "perpendicular bisector", topic, "Equal-radius arcs from both endpoints locate a perpendicular bisector.", "text", diagram={"kind":"construction"})
    if topic == "prism_volume":
        base,height,length=random.randint(3,8),random.randint(2,7),random.randint(4,10); area=base*height/2
        return _q(f"A triangular prism has cross-section base {base} cm, height {height} cm and length {length} cm. Find its volume.", area*length, topic, "Find the triangular cross-sectional area, then multiply by the prism length.", diagram={"kind":"prism", "dimensions":[length,base,height]})
    if topic == "compound_volume":
        first,second=random.choice([(60,36),(72,48),(90,30),(120,45)])
        return _q(f"A compound solid joins prisms of volume {first} cm³ and {second} cm³ without overlap. Find the total volume.", first+second, topic, "Split the solid into known prisms and add their volumes.", diagram={"kind":"compound_prism", "volumes":[first,second]})
    if topic == "mixed_add_subtract":
        whole1,whole2=random.randint(1,4),random.randint(1,3); f1,f2=Fraction(1,2),Fraction(1,4); answer=whole1+f1+whole2+f2
        return _q(f"Calculate {whole1} 1/2 + {whole2} 1/4. Give a mixed number or fraction.", str(answer), topic, "Convert to improper fractions or combine wholes and fractional parts using a common denominator.", "text")
    if topic == "fraction_times_integer":
        numerator,denominator,multiplier=random.choice([(2,3,6),(3,5,10),(5,8,4)])
        return _q(f"Calculate {numerator}/{denominator} × {multiplier}.", str(Fraction(numerator*multiplier,denominator)), topic, "Multiply the numerator by the integer, then simplify.", "text", diagram={"kind":"fraction_strip", "parts":denominator, "shaded":numerator})
    if topic == "fraction_divide_integer":
        numerator,denominator,divisor=random.choice([(3,4,2),(5,6,3),(7,8,2)])
        return _q(f"Calculate {numerator}/{denominator} ÷ {divisor}.", str(Fraction(numerator,denominator*divisor)), topic, "Multiply by the reciprocal of the integer, then simplify.", "text")
    if topic in ("mixed_number_multiply", "mixed_number_divide"):
        mixed=Fraction(3,2); other=Fraction(2,3)
        divide=topic == "mixed_number_divide"; answer=mixed/other if divide else mixed*other
        return _q(f"Calculate 1 1/2 {'÷' if divide else '×'} 2/3. Give the simplest fraction.", str(answer), topic, "Convert the mixed number to an improper fraction before multiplying or dividing.", "text")
    if topic == "algebraic_thinking":
        x=random.randint(2,7)
        return _q(f"A number is doubled and then 3 is added, giving {2*x+3}. Find the number.", x, topic, "Represent the relationship as 2x + 3, then use inverse operations.")
    if topic == "forming_expressions":
        price=random.randint(2,8)
        return _q(f"A taxi costs £{price} plus £3 per mile. Write the cost for m miles.", f"3m+{price}", topic, "Use a variable for the changing quantity and a constant for the fixed charge.", "text", accepted=[f"{price}+3m"])
    if topic == "linear_equations_both_sides":
        x=random.randint(2,9); a,b=random.randint(3,7),random.randint(1,2); c=random.randint(1,8); d=(a-b)*x+c
        return _q(f"Solve {a}x + {c} = {b}x + {d}.", x, topic, "Collect x terms on one side and constants on the other, then divide.")
    if topic == "linear_equations_brackets":
        x=random.randint(2,8); a=random.randint(2,5); b=random.randint(1,6); total=a*(x+b)
        return _q(f"Solve {a}(x + {b}) = {total}.", x, topic, "Divide by the outside multiplier, then undo the addition.")
    if topic == "linear_equations_fractions":
        x=random.choice([4,6,8,10,12]); divisor=random.choice([2,3,4]); constant=random.randint(1,6); total=x/divisor+constant
        return _q(f"Solve x/{divisor} + {constant} = {total:g}.", x, topic, "Subtract the constant, then multiply by the denominator.")
    if topic == "scale_drawings":
        scale=random.choice([50,100,200]); drawing=random.choice([3,4,6,8])
        return _q(f"A map uses 1 cm : {scale} m. Two places are {drawing} cm apart. Find the real distance in metres.", scale*drawing, topic, "Multiply the drawing measurement by the scale value.")
    if topic == "similar_shapes":
        scale=random.choice([2,3,4]); side=random.randint(3,9)
        return _q(f"Two shapes are similar with scale factor {scale}. A corresponding side is {side} cm on the smaller shape. Find the larger side.", scale*side, topic, "Corresponding lengths are multiplied by the linear scale factor.", diagram={"kind":"shape_scale", "scale":scale})
    if topic == "line_dot_plots":
        values=random.choices(range(2,9),k=12); target=random.choice(values)
        return _q(f"Use the line plot. What is the frequency at {target}?", values.count(target), topic, "Count the marks directly above the requested value.", diagram={"kind":"line_plot", "values":values})
    if topic == "pictograms":
        labels=["Red","Blue","Green"]; counts=[random.randint(2,5) for _ in labels]; target=random.randrange(3); key=2
        return _q(f"Use the pictogram. How many votes did {labels[target]} receive?", counts[target]*key, topic, "Count the symbols and multiply by the key.", diagram={"kind":"pictogram", "labels":labels, "counts":counts, "key":key})
    if topic == "scatter_graphs":
        correlation=random.choice(["positive","negative"]); xs=list(range(1,10))
        points=[[x, (x+random.randint(-1,1)) if correlation=="positive" else (11-x+random.randint(-1,1))] for x in xs]
        return _q("What type of correlation is shown?", correlation, topic, "Describe the overall direction of the point cloud; one unusual point does not determine the trend.", "multiple_choice", ["Positive","Negative","No correlation"], diagram={"kind":"scatter_plot", "points":points})
    if topic == "simple_graphs":
        m,c=random.choice([(2,1),(3,0),(1,4)]); x=random.randint(2,5)
        return _q(f"The graph follows y = {m}x + {c}. Read or calculate y when x = {x}.", m*x+c, topic, "Trace from x to the line and across to y, or substitute into the rule.", diagram={"kind":"coordinate_grid", "line":[m,c], "select_x":x})
    if topic == "dual_stacked_bars":
        parts=[random.randint(3,9) for _ in range(3)]
        return _q("Click the stacked bar and find its total frequency.", sum(parts), topic, "Add every section in the stack to obtain the total.", diagram={"kind":"stacked_bar", "parts":parts})
    if topic == "grouped_frequency":
        groups=["0 < x ≤ 10","10 < x ≤ 20","20 < x ≤ 30"]; frequencies=[random.randint(3,12) for _ in groups]; target=random.randrange(3)
        return _q(f"Use the grouped table. What is the frequency for {groups[target]}?", frequencies[target], topic, "Read the row whose inequality contains the requested interval.", diagram={"kind":"grouped_table", "groups":groups, "frequencies":frequencies})
    if topic == "power_notation":
        base, power = random.randint(2, 6), random.randint(2, 4)
        return _q(f"Calculate {base}^{power}.", base ** power, topic, "Multiply the base by itself the stated number of times.")
    if topic == "hcf_lcm":
        a, b = random.choice([(12,18),(15,25),(18,24),(20,30)])
        use_hcf = random.choice([True, False]); answer = math.gcd(a,b) if use_hcf else math.lcm(a,b)
        return _q(f"Find the {'HCF' if use_hcf else 'LCM'} of {a} and {b}.", answer, topic, "List factors for HCF or multiples for LCM, then select the greatest or least common value.")
    if topic == "prime_numbers":
        value = random.choice([17,19,23,29,31,37,49,51,57,77])
        answer = "prime" if all(value % d for d in range(2, int(value ** .5)+1)) else "not prime"
        return _q(f"Is {value} prime?", answer, topic, "A prime number has exactly two factors: 1 and itself.", "multiple_choice", ["Prime", "Not prime"])
    if topic == "prime_factorisation":
        value, answer = random.choice([(24,"2^3*3"),(36,"2^2*3^2"),(60,"2^2*3*5"),(84,"2^2*3*7")])
        return _q(f"Write {value} as a product of prime factors using powers.", answer, topic, "Use a factor tree until every branch ends in a prime.", "text")
    if family == "negatives":
        a, b = random.randint(-12, 12), random.choice([n for n in range(-10,11) if n])
        if topic == "negative_multiply_divide":
            return _q(f"Calculate {a} × ({b}).", a*b, topic, "Equal signs give a positive product; different signs give a negative product.", diagram={"kind":"number_line", "min":-20, "max":20, "target":max(-20,min(20,a*b))})
        return _q(f"Calculate {a} − ({b}).", a-b, topic, "Subtracting a negative is equivalent to adding its positive.", diagram={"kind":"number_line", "min":-20, "max":20, "target":max(-20,min(20,a-b))})
    if family == "powers":
        if topic in ("numerical_index_laws", "algebraic_index_laws"):
            a, b = random.randint(2,5), random.randint(2,5)
            return _q(f"Simplify x^{a} × x^{b}. Give the power of x.", a+b, topic, "When multiplying powers with the same base, add the indices.")
        root = random.choice([4,9,16,25,36,49,64,81,100])
        return _q(f"Find √{root}.", int(math.sqrt(root)), topic, "A square root is the positive number that multiplies by itself to make the value.")
    if family == "rounding":
        if topic == "rounding_place_value":
            value, place = random.randint(1200,9800), random.choice([10,100,1000])
            return _q(f"Round {value} to the nearest {place}.", round(value/place)*place, topic, "Check the digit immediately to the right of the rounding place.")
        if topic == "decimal_places":
            value, places = random.choice([(4.376,2),(8.054,1),(12.485,2)])
            return _q(f"Round {value} to {places} decimal place{'s' if places != 1 else ''}.", round(value,places), topic, "Keep the requested decimal places and inspect the next digit.")
        if topic == "significant_figures":
            value, figures = random.choice([(4837,2),(0.006784,2),(92750,3)])
            return _q(f"Round {value} to {figures} significant figures.", _round_sf(value,figures), topic, "Count significant digits from the first non-zero digit.")
        value = random.choice([2.4,3.75,0.68,12.5]); factor = random.choice([10,100,1000]); multiply = random.choice([True,False])
        return _q(f"Calculate {value} {'×' if multiply else '÷'} {factor}.", value*factor if multiply else value/factor, topic, "Move every digit through the place-value columns; do not merely add zeros.")
    if family == "standard_form":
        if topic == "standard_form":
            coefficient, power = random.choice([(3.2,4),(6.7,5),(4.05,3)])
            return _q(f"Write {coefficient} × 10^{power} as an ordinary number.", coefficient*10**power, topic, "A positive power moves the decimal point to the right.")
        a, b = random.randint(2,8), random.randint(2,8)
        return _q(f"Calculate ({a} × 10^3) × ({b} × 10^2). Give the ordinary number.", a*b*10**5, topic, "Multiply coefficients and add powers, then convert if requested.")
    if family == "fractions":
        d1, d2 = random.choice([(3,4),(4,5),(5,6),(6,8)])
        n1, n2 = random.randint(1,d1-1), random.randint(1,d2-1)
        if topic in ("fractions_of_amount", "fraction_amount_problems"):
            denominator = random.choice([3,4,5,6,8]); numerator = random.randint(1,denominator-1); amount = denominator*random.randint(3,12)
            return _q(f"Find {numerator}/{denominator} of {amount}.", numerator*amount/denominator, topic, "Divide by the denominator, then multiply by the numerator.", diagram={"kind":"fraction_strip", "parts":denominator, "shaded":numerator})
        if topic in ("fraction_times_integer", "proper_fraction_multiply", "fraction_multiply_advanced", "mixed_number_multiply"):
            answer = Fraction(n1*n2,d1*d2)
            return _q(f"Calculate {n1}/{d1} × {n2}/{d2}. Give the simplest fraction.", str(answer), topic, "Multiply numerators and denominators, then simplify.", "text", diagram={"kind":"fraction_strip", "parts":d1, "shaded":n1})
        if topic in ("fraction_divide_integer", "proper_improper_division", "mixed_number_divide"):
            divisor = random.randint(2,4); answer = Fraction(n1,d1*divisor)
            return _q(f"Calculate {n1}/{d1} ÷ {divisor}. Give the simplest fraction.", str(answer), topic, "Dividing by an integer is multiplying by its reciprocal.", "text")
        subtract = random.choice([True,False]); answer = Fraction(n1,d1) - Fraction(n2,d2) if subtract else Fraction(n1,d1)+Fraction(n2,d2)
        return _q(f"Calculate {n1}/{d1} {'−' if subtract else '+'} {n2}/{d2}. Give the simplest fraction.", str(answer), topic, "Use a common denominator, calculate the numerator, then simplify.", "text")
    if family == "decimals":
        a, b = random.choice([(1.2,0.4),(2.5,0.3),(3.6,1.2),(4.8,0.6)])
        divide = topic in ("decimal_divide_integer", "decimal_division")
        if divide:
            return _q(f"Calculate {a} ÷ {b}.", a/b, topic, "Scale both values by the same power of ten, then divide.")
        return _q(f"Calculate {a} × {b}.", a*b, topic, "Multiply as integers, then restore the total number of decimal places.")
    if family == "percentages":
        if topic == "percentage_of_number":
            part, whole = random.choice([(18,60),(24,80),(35,140),(45,180)])
            return _q(f"What percentage of {whole} is {part}?", part/whole*100, topic, "Divide the part by the whole and multiply by 100.")
        if topic == "percentage_change":
            old, new = random.choice([(80,92),(120,90),(50,65),(200,170)])
            return _q(f"A value changes from {old} to {new}. Find the percentage change.", abs(new-old)/old*100, topic, "Find the change, divide by the original amount, then multiply by 100.")
        percent = random.choice([5,10,15,25,35,120,150]); amount = random.choice([40,60,80,120,200])
        return _q(f"Find {percent}% of {amount}.", percent*amount/100, topic, "Use a known percentage or decimal multiplier, then scale.", diagram={"kind":"percentage_bar", "percent":min(percent,100)})
    if family in ("ratio",):
        if topic == "exchange_rates":
            rate, pounds = random.choice([(1.2,50),(1.15,80),(1.4,60)])
            return _q(f"£{pounds} is exchanged at €{rate} per £1. How many euros are received?", pounds*rate, topic, "Multiply by the exchange rate when converting from pounds to euros.")
        left,right = random.choice([(2,3),(3,5),(4,7)]); unit=random.randint(3,9); total=(left+right)*unit
        return _q(f"Share {total} in the ratio {left}:{right}. Give the larger share.", max(left,right)*unit, topic, "Add the parts, find one part, then multiply.", diagram={"kind":"ratio_blocks", "left":left, "right":right})
    if family == "algebra":
        if topic == "algebraic_terminology":
            return _q("In 5x + 7, what is the coefficient of x?", 5, topic, "The coefficient is the number multiplying the variable.")
        if topic == "multiply_terms":
            a,b=random.randint(2,6),random.randint(2,6); return _q(f"Simplify {a}x × {b}.", f"{a*b}x", topic, "Multiply the coefficients and keep the variable.", "text")
        if topic == "divide_terms":
            a,b=random.randint(2,6),random.randint(2,6); return _q(f"Simplify {a*b}x ÷ {b}.", f"{a}x", topic, "Divide the coefficients and retain unmatched variables.", "text")
        if topic == "collect_like_terms":
            a,b=random.randint(2,8),random.randint(2,8); return _q(f"Simplify {a}x + {b}x.", f"{a+b}x", topic, "Like terms have identical variable parts, so combine their coefficients.", "text")
        if topic == "expand_single_bracket":
            a,b=random.randint(2,6),random.randint(1,9); return _q(f"Expand {a}(x + {b}).", f"{a}x+{a*b}", topic, "Multiply every term inside the bracket.", "text", accepted=[f"{a*b}+{a}x"])
        x=random.randint(2,8); a,b=random.randint(2,6),random.randint(1,9)
        return _q(f"An expression is {a}x + {b}. Find its value when x = {x}.", a*x+b, topic, "Substitute the value for x, then follow the order of operations.")
    if family == "equations":
        x=random.randint(-5,10); a=random.randint(2,6); b=random.randint(1,12)
        if topic in ("change_subject_simple", "change_subject_advanced"):
            return _q("Make x the subject of y = 3x + 4.", "(y-4)/3", topic, "Undo addition first, then undo multiplication.", "text", accepted=["(y−4)/3","y/3-4/3"])
        return _q(f"Solve {a}x + {b} = {a*x+b}.", x, topic, f"Subtract {b} from both sides, then divide by {a}.")
    if family == "probability":
        if topic == "sample_spaces":
            return _q("Two fair coins are tossed. How many outcomes contain exactly one head?", 2, topic, "List HH, HT, TH and TT, then count HT and TH.", diagram={"kind":"sample_space", "rows":["H","T"], "columns":["H","T"]})
        if topic == "mutually_exclusive":
            p=random.choice([0.2,0.35,0.6,0.75]); return _q(f"P(win) = {p}. Find P(not win).", 1-p, topic, "Complementary probabilities total 1.", diagram={"kind":"probability_scale", "value":p})
        successes,trials=random.choice([(18,60),(24,80),(35,100)]); future=random.choice([200,300,400])
        return _q(f"An outcome occurred {successes} times in {trials} trials. Estimate its frequency in {future} trials.", successes/trials*future, topic, "Use relative frequency as the estimated probability, then multiply by future trials.")
    if family == "graphs":
        m=random.choice([-3,-2,-1,1,2,3]); c=random.randint(-4,4)
        if topic == "line_intercepts":
            c=random.choice([-6,-4,4,6]); m=random.choice([-2,-1,1,2]); answer=-c/m
            return _q(f"Find the x-intercept of y = {m}x + {c}.", answer, topic, "At the x-intercept, y = 0. Substitute and solve.", diagram={"kind":"coordinate_grid", "line":[m,c], "answer_mode":"x_intercept"})
        if topic == "gradient":
            return _q(f"A line passes through (0, {c}) and (2, {2*m+c}). Find its gradient.", m, topic, "Gradient is change in y divided by change in x.", diagram={"kind":"coordinate_grid", "line":[m,c]})
        if topic == "quadratic_graphs":
            x=random.randint(-3,3); return _q(f"For y = x² − 2, find y when x = {x}.", x*x-2, topic, "Substitute x, square it, then subtract 2.", diagram={"kind":"coordinate_grid", "quadratic":[1,0,-2]})
        x=random.randint(-3,3)
        return _q(f"For y = {m}x + {c}, find y when x = {x}.", m*x+c, topic, "Substitute x into the equation, multiply, then add the intercept.", diagram={"kind":"coordinate_grid", "line":[m,c], "select_x":x})
    if family == "transformations":
        if topic in ("translations",):
            x,y=random.randint(-3,2),random.randint(-3,2); dx,dy=random.choice([(2,1),(-2,3),(3,-1)])
            return _q(f"Point A is ({x},{y}). Translate it by ({dx},{dy}). Give x,y.", f"{x+dx},{y+dy}", topic, "Add the translation vector to the coordinates.", "pair", diagram={"kind":"coordinate_grid", "point":[x,y], "vector":[dx,dy], "answer_mode":"point"})
        scale=random.choice([2,3,0.5]); length=random.choice([3,4,6,8])
        return _q(f"A side of length {length} is enlarged by scale factor {scale}. Find the new length.", length*scale, topic, "Multiply every length by the scale factor.", diagram={"kind":"shape_scale", "scale":scale})
    if family == "constructions":
        return _q("Which construction creates points equally distant from both ends of a line segment?", "perpendicular bisector", topic, "Every point on the perpendicular bisector is equidistant from the endpoints.", "multiple_choice", ["Perpendicular bisector","Angle bisector","Parallel line","Arc"])
    if family == "congruence":
        choices=["SSS","SAS","ASA","RHS"]; answer=random.choice(choices)
        descriptions={"SSS":"all three corresponding sides","SAS":"two sides and the included angle","ASA":"two angles and one corresponding side","RHS":"a right angle, hypotenuse and one side"}
        return _q(f"Which congruence test uses {descriptions[answer]}?", answer, topic, "Congruence requires enough matching information to fix the triangle's size and shape.", "multiple_choice", choices, diagram={"kind":"triangles", "rule":answer})
    if family == "mensuration":
        l,w,h=random.randint(2,8),random.randint(2,7),random.randint(2,6)
        if topic == "surface_area_prisms": answer=2*(l*w+l*h+w*h); prompt=f"A cuboid is {l} cm by {w} cm by {h} cm. Find its surface area."
        else: answer=l*w*h; prompt=f"A cuboid is {l} cm by {w} cm by {h} cm. Find its volume."
        return _q(prompt, answer, topic, "Use all three dimensions for volume; for surface area total the six rectangular faces.", diagram={"kind":"prism", "dimensions":[l,w,h]})
    if family == "circles":
        if topic == "circle_terms":
            answer=random.choice(["radius","diameter","circumference"])
            return _q(f"Select the {answer} on the circle diagram.", answer, topic, "Radius goes centre-to-edge; diameter crosses through the centre; circumference is the boundary.", "text", diagram={"kind":"circle_parts", "answer":answer})
        radius=random.randint(2,10)
        if topic == "circumference": return _q(f"A circle has radius {radius} cm. Find its circumference in terms of π.", f"{2*radius}pi", topic, "Circumference = 2πr.", "text", accepted=[f"{2*radius}π"], diagram={"kind":"circle_measure", "radius":radius})
        return _q(f"A circle has radius {radius} cm. Find its area in terms of π.", f"{radius*radius}pi", topic, "Area = πr².", "text", accepted=[f"{radius*radius}π"], diagram={"kind":"circle_measure", "radius":radius})
    if family == "data":
        labels=["A","B","C","D"]; values=[random.randint(2,10) for _ in labels]; target=random.randrange(4)
        if topic in ("simple_pie_charts","pie_charts_any"):
            fraction=random.choice([(1,4),(1,3),(2,5)]); return _q(f"A pie-chart sector is {fraction[0]}/{fraction[1]} of the circle. Find its angle.", 360*fraction[0]/fraction[1], topic, "Multiply the fraction by 360°.", diagram={"kind":"pie_chart", "fraction":list(fraction)})
        return _q(f"Use the chart. What is the frequency for {labels[target]}?", values[target], topic, "Read the height using the numbered scale.", diagram={"kind":"bar_chart", "labels":labels, "values":values, "target":labels[target]})
    raise ValueError(f"No Year 8 generator for {topic}")
