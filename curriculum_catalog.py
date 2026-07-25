"""Universal Years 7-11 curriculum catalogue for Maths and English."""

import year8_maths


BASE = {
    7: {
        "Maths": [("number","Integers and calculation"),("fractions","Fractions, decimals and percentages"),("algebra","Expressions and simple equations"),("ratio","Ratio and proportion"),("geometry","Angles and 2D geometry"),("statistics","Averages and data")],
        "English": [("retrieval","Retrieval and evidence"),("inference","Inference"),("language","Language choices"),("narrative","Narrative writing"),("grammar","Grammar and punctuation")],
    },
    8: {
        "English": [("inference","Inference and evidence"),("language","Figurative language"),("structure","Text structure"),("viewpoint","Viewpoint and rhetoric"),("comparison","Comparing texts")],
    },
    9: {
        "Maths": [("algebra","Expanding, factorising and graphs"),("number","Accuracy and standard form"),("geometry","Pythagoras and similarity"),("proportion","Rates and proportion"),("probability","Combined probability"),("statistics","Scatter graphs and sampling")],
        "English": [("analysis","Analytical paragraphs"),("language","Language and terminology"),("structure","Structure and form"),("comparison","Critical comparison"),("transactional","Transactional writing")],
    },
    10: {
        "Maths": [("number","GCSE number and accuracy"),("algebra","Quadratics and simultaneous equations"),("graphs","Coordinates and graphs"),("geometry","Pythagoras and trigonometry"),("probability","Probability models"),("statistics","GCSE statistics")],
        "English": [("ao1","AO1: information and inference"),("ao2","AO2: language and structure"),("ao4","AO4: critical evaluation"),("creative","Creative writing"),("accuracy","Vocabulary, sentences and accuracy")],
    },
    11: {
        "Maths": [("algebra","Advanced algebra and functions"),("graphs","Quadratic and real-life graphs"),("geometry","Circle theorems, vectors and trigonometry"),("proportion","Compound measures and growth"),("probability","Conditional probability"),("reasoning","Multi-step GCSE reasoning")],
        "English": [("ao2","AO2: perceptive analysis"),("ao3","AO3: comparison"),("ao4","AO4: evaluation"),("transactional","Transactional writing"),("revision","Unseen text and exam strategy")],
    },
}


MATHS_SKILLS = {
    "number": ["place value and representations","accurate calculation","factors, powers and roots","estimation and checking","multi-step number reasoning"],
    "fractions": ["equivalent forms","fraction operations","decimal place value","percentage conversion","fractional problem solving"],
    "algebra": ["notation and substitution","collecting and expanding","equations and inequalities","sequences and graphs","algebraic reasoning"],
    "ratio": ["ratio notation","sharing and scaling","direct proportion","unit rates","ratio problem solving"],
    "proportion": ["multiplicative relationships","rates and units","direct and inverse proportion","percentage multipliers","contextual modelling"],
    "geometry": ["properties and notation","angles and constructions","measure and formulae","transformations","geometric reasoning"],
    "statistics": ["representing data","averages and spread","interpreting charts","sampling","evidence-based comparison"],
    "probability": ["sample spaces","theoretical probability","combined events","relative frequency","probability reasoning"],
    "graphs": ["coordinates and scales","linear relationships","gradient and intercept","non-linear graphs","graph interpretation"],
    "reasoning": ["identify relevant information","connect multiple methods","justify each step","estimate and verify","communicate a conclusion"],
}

ENGLISH_SKILLS = {
    "retrieval": ["scan for key ideas","select precise evidence","distinguish explicit detail","synthesise information","answer concisely"],
    "inference": ["form an inference","select supporting evidence","analyse clues","consider alternatives","justify conclusions"],
    "language": ["identify precise choices","use terminology","analyse connotations","explain effects","develop interpretations"],
    "structure": ["track focus","identify shifts","analyse openings and endings","explain pace","connect structure to meaning"],
    "viewpoint": ["identify audience","establish a position","use rhetoric","sequence arguments","address counterarguments"],
    "comparison": ["form a comparative idea","select paired evidence","compare methods","compare perspectives","synthesise a judgement"],
    "narrative": ["shape character and setting","control viewpoint","build a turning point","vary pace","craft an ending"],
    "grammar": ["control clauses","vary sentences","use punctuation accurately","maintain agreement","edit for clarity"],
    "analysis": ["form a thesis","embed evidence","analyse methods","develop interpretations","link to the question"],
    "transactional": ["match form and audience","build an argument","use cohesive paragraphs","control register","finish persuasively"],
    "ao1": ["select information","infer accurately","synthesise sources","use references","answer the focus"],
    "ao2": ["analyse language","analyse structure","use terminology","explore effects","develop perceptive ideas"],
    "ao3": ["compare ideas","compare perspectives","connect methods","synthesise evidence","develop contrasts"],
    "ao4": ["form a judgement","evaluate evidence","analyse methods","qualify a view","conclude convincingly"],
    "creative": ["plan a central change","control viewpoint","use sensory detail","shape structure","edit accurately"],
    "accuracy": ["sentence boundaries","spelling patterns","punctuation choices","precise vocabulary","proofreading"],
    "revision": ["retrieve from memory","apply under time","review against criteria","target weaknesses","retain learning"],
}

STAGES = [
    ("foundation", "Core knowledge", "Fluency"),
    ("application", "Application", "Applied"),
    ("reasoning", "Reasoning and problem solving", "Reasoning"),
]


def _expanded_units(year, subject, family, base_title):
    skills = (MATHS_SKILLS if subject == "Maths" else ENGLISH_SKILLS)[family]
    units = []
    previous = None
    for index, (stage, label, category) in enumerate(STAGES):
        unit_id = family if index == 0 else f"{family}_{stage}"
        start = 0 if index == 0 else 2 if index == 1 else 3
        selected = skills[:3] if index == 0 else skills[start:start+3]
        if len(selected) < 3: selected = (selected + skills)[:3]
        units.append({
            "id": unit_id, "title": f"{base_title}: {label}", "year": year, "subject": subject,
            "chapter_id": family, "chapter": base_title, "family": family, "stage": stage,
            "subskills": selected, "prerequisites": [previous] if previous else [],
            "question_categories": ["Fluency", "Applied", "Reasoning", "Exam-style"],
            "primary_category": category,
            "resources": resources_for_family(subject, family),
        })
        previous = unit_id
    return units


def resources_for_family(subject, family):
    if subject == "English": return ["annotatable text", "planning frame", "model paragraph"]
    if family in ("geometry",): return ["interactive geometry", "coordinate grid", "worked construction"]
    if family in ("graphs", "statistics"): return ["interactive graph", "data table", "chart explorer"]
    if family == "probability": return ["sample-space explorer", "probability scale", "trial simulator"]
    if family in ("fractions", "ratio", "proportion"): return ["bar model", "ratio blocks", "worked example"]
    return ["worked example", "guided steps", "interactive check"]


def chapters_for(year, subject):
    year, subject = int(year), subject.title()
    if year == 8 and subject == "Maths":
        result=[]
        for chapter_id,title,units in year8_maths.chapters():
            chapter_units=[]; previous=None
            for u in units:
                chapter_units.append({
                    "id":u["id"],"title":u["title"],"year":8,"subject":"Maths","chapter_id":chapter_id,
                    "chapter":title,"family":u["family"],"stage":"mixed","subskills":[part.strip() for part in u["focus"].split(";")],
                    "prerequisites":[previous] if previous else [],"question_categories":["Fluency","Applied","Reasoning","Exam-style"],
                    "primary_category":"Fluency",
                    "resources":resources_for_family("Maths",u["family"]),
                }); previous=u["id"]
            result.append({"id":chapter_id,"title":title,"units":chapter_units})
        return result
    result=[]
    for family,title in BASE[year][subject]:
        result.append({"id":family,"title":title,"units":_expanded_units(year,subject,family,title)})
    return result


def units_for(year, subject):
    result=[];seen=set()
    for chapter in chapters_for(year,subject):
        for unit in chapter["units"]:
            if unit["id"] not in seen:
                seen.add(unit["id"]);result.append(unit)
    return result


def topics_for(year, subject):
    return [(unit["id"],unit["title"]) for unit in units_for(year,subject)]


def unit_details(year, subject, unit_id):
    return next((unit for unit in units_for(year,subject) if unit["id"] == unit_id),None)


def question_family(year, subject, unit_id):
    unit=unit_details(year,subject,unit_id)
    return unit["family"] if unit else unit_id


PATHWAYS = {
    "year7_foundations": {"title":"Year 7 Foundations","description":"A supported route through essential secondary Maths and English.","years":[7],"subjects":["Maths","English"],"stages":["foundation"]},
    "catch_up_maths": {"title":"Catch-up Maths","description":"Rebuild important number, fraction, algebra, ratio and geometry foundations.","years":[7,8,9],"subjects":["Maths"],"stages":["foundation"]},
    "gcse_foundation": {"title":"GCSE Foundation","description":"Core Year 10–11 knowledge and application for GCSE preparation.","years":[10,11],"subjects":["Maths","English"],"stages":["foundation","application"]},
    "gcse_higher": {"title":"GCSE Higher","description":"Reasoning-heavy Maths and analytical English preparation.","years":[10,11],"subjects":["Maths","English"],"stages":["reasoning","mixed"]},
    "exam_preparation": {"title":"Exam Preparation","description":"Timed application, exam-style practice and targeted review.","years":[11],"subjects":["Maths","English"],"stages":["application","reasoning","mixed"]},
    "english_reading": {"title":"English Reading","description":"Evidence, inference, language, structure, comparison and evaluation.","years":[7,8,9,10,11],"subjects":["English"],"families":["retrieval","inference","language","structure","comparison","analysis","ao1","ao2","ao3","ao4"]},
    "english_writing": {"title":"English Writing","description":"Narrative, creative, transactional and accurate writing.","years":[7,8,9,10,11],"subjects":["English"],"families":["narrative","viewpoint","transactional","creative","grammar","accuracy"]},
}


def pathways():
    return [{"id":key,**value} for key,value in PATHWAYS.items()]


def pathway_units(pathway_id):
    path=PATHWAYS.get(pathway_id)
    if not path:return []
    result=[]
    for year in path["years"]:
        for subject in path["subjects"]:
            for unit in units_for(year,subject):
                if path.get("stages") and unit["stage"] not in path["stages"]:continue
                if path.get("families") and unit["family"] not in path["families"]:continue
                result.append(unit)
    return result


def search(query="", year=None, subject=None, chapter=None):
    needle=query.strip().lower(); result=[]
    years=[int(year)] if year else range(7,12); subjects=[subject.title()] if subject else ("Maths","English")
    for current_year in years:
        for current_subject in subjects:
            for unit in units_for(current_year,current_subject):
                haystack=" ".join([unit["title"],unit["chapter"],*unit["subskills"]]).lower()
                if needle and needle not in haystack:continue
                if chapter and unit["chapter_id"] != chapter:continue
                result.append(unit)
    return result
