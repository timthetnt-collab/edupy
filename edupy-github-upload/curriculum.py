"""Year 7-11 curriculum map, topic mastery, and personalised recommendations.

The Year 7-9 ordering is an Edupy sequence covering England's KS3 programmes of
study. Schools may sequence KS3 content differently. Years 10-11 build toward
the common GCSE subject content and assessment objectives.
"""

import datetime

import save_system
import year8_maths
import curriculum_catalog


CURRICULUM = {
    7: {
        "Maths": [
            ("number", "Integers and calculation"), ("fractions", "Fractions, decimals and percentages"),
            ("algebra", "Expressions and simple equations"), ("ratio", "Ratio and proportion"),
            ("geometry", "Angles and 2D geometry"), ("statistics", "Averages and data"),
        ],
        "English": [
            ("retrieval", "Retrieval and evidence"), ("inference", "Inference"),
            ("language", "Language choices"), ("narrative", "Narrative writing"),
            ("grammar", "Grammar and punctuation"),
        ],
    },
    8: {
        "Maths": year8_maths.topics(),
        "English": [
            ("inference", "Inference and evidence"), ("language", "Figurative language"),
            ("structure", "Text structure"), ("viewpoint", "Viewpoint and rhetoric"),
            ("comparison", "Comparing texts"),
        ],
    },
    9: {
        "Maths": [
            ("algebra", "Expanding, factorising and graphs"), ("number", "Accuracy and standard form"),
            ("geometry", "Pythagoras and similarity"), ("proportion", "Rates and proportion"),
            ("probability", "Combined probability"), ("statistics", "Scatter graphs and sampling"),
        ],
        "English": [
            ("analysis", "Analytical paragraphs"), ("language", "Language and terminology"),
            ("structure", "Structure and form"), ("comparison", "Critical comparison"),
            ("transactional", "Transactional writing"),
        ],
    },
    10: {
        "Maths": [
            ("number", "GCSE number and accuracy"), ("algebra", "Quadratics and simultaneous equations"),
            ("graphs", "Coordinates and graphs"), ("geometry", "Pythagoras and trigonometry"),
            ("probability", "Probability models"), ("statistics", "GCSE statistics"),
        ],
        "English": [
            ("ao1", "AO1: information and inference"), ("ao2", "AO2: language and structure"),
            ("ao4", "AO4: critical evaluation"), ("creative", "Creative writing"),
            ("accuracy", "Vocabulary, sentences and accuracy"),
        ],
    },
    11: {
        "Maths": [
            ("algebra", "Advanced algebra and functions"), ("graphs", "Quadratic and real-life graphs"),
            ("geometry", "Circle theorems, vectors and trigonometry"), ("proportion", "Compound measures and growth"),
            ("probability", "Conditional probability"), ("reasoning", "Multi-step GCSE reasoning"),
        ],
        "English": [
            ("ao2", "AO2: perceptive analysis"), ("ao3", "AO3: comparison"),
            ("ao4", "AO4: evaluation"), ("transactional", "Transactional writing"),
            ("revision", "Unseen text and exam strategy"),
        ],
    },
}


def topics_for(year, subject):
    year = min(11, max(7, int(year)))
    return curriculum_catalog.topics_for(year, subject)


def maths_chapters_for(year):
    """Return chapter groupings when a year has a detailed maths sequence."""
    if int(year) == 8:
        return year8_maths.chapters()
    return []


def topic_details(year, subject, topic_id):
    return curriculum_catalog.unit_details(year, subject, topic_id)


def chapters_for(year, subject):
    return curriculum_catalog.chapters_for(year, subject)


def question_family(year, subject, topic_id):
    return curriculum_catalog.question_family(year, subject, topic_id)


def curriculum_search(query="", year=None, subject=None, chapter=None):
    return curriculum_catalog.search(query, year, subject, chapter)


def pathways():
    return curriculum_catalog.pathways()


def pathway_units(pathway_id):
    return curriculum_catalog.pathway_units(pathway_id)


def topic_title(year, subject, topic_id):
    return dict(topics_for(year, subject)).get(topic_id, topic_id.replace("_", " ").title())


def record_mastery(data, username, subject, topic_id, earned, possible):
    """Record a result using cumulative evidence with a recent-performance bias."""
    user = save_system.get_user(data, username)
    if not user or possible <= 0:
        return 0
    subject_key = subject.title()
    topic = user.setdefault("mastery", {}).setdefault(subject_key, {}).setdefault(topic_id, {
        "attempts": 0, "earned": 0.0, "possible": 0.0, "recent": 0.0, "updated": None,
    })
    ratio = min(1.0, max(0.0, float(earned) / float(possible)))
    topic["attempts"] += 1
    topic["earned"] += float(earned)
    topic["possible"] += float(possible)
    topic["recent"] = ratio if topic["attempts"] == 1 else topic["recent"] * 0.65 + ratio * 0.35
    topic["updated"] = datetime.date.today().isoformat()
    recent = user.setdefault("recent_topics", [])
    recent.append({"subject": subject_key, "topic": topic_id, "score": round(ratio * 100), "date": topic["updated"]})
    user["recent_topics"] = recent[-30:]
    save_system.save_save(data)
    return mastery_percent(user, subject_key, topic_id)


def mastery_percent(user, subject, topic_id):
    topic = user.get("mastery", {}).get(subject.title(), {}).get(topic_id)
    if not topic or not topic.get("possible"):
        return 0
    cumulative = topic["earned"] / topic["possible"]
    return round((cumulative * 0.6 + topic.get("recent", cumulative) * 0.4) * 100)


def subject_mastery(user, year, subject):
    return {topic_id: mastery_percent(user, subject, topic_id) for topic_id, _ in topics_for(year, subject)}


def recommend_next(data, username, subject=None):
    user = save_system.get_user(data, username)
    if not user:
        return None
    year = user.get("selected_year", 7)
    subjects = [subject.title()] if subject else ["Maths", "English"]
    candidates = []
    for subject_name in subjects:
        for order, (topic_id, title) in enumerate(topics_for(year, subject_name)):
            record = user.get("mastery", {}).get(subject_name, {}).get(topic_id, {})
            attempts = record.get("attempts", 0)
            score = mastery_percent(user, subject_name, topic_id)
            detail = topic_details(year, subject_name, topic_id) or {}
            unmet = [prerequisite for prerequisite in detail.get("prerequisites", []) if mastery_percent(user, subject_name, prerequisite) < 50]
            if unmet:
                continue
            # Unseen topics come first in curriculum order; then prioritise weak evidence.
            priority = (0 if attempts == 0 else 1, score if attempts else order, attempts)
            candidates.append((priority, subject_name, topic_id, title, score, attempts))
    if not candidates:
        return None
    _, subject_name, topic_id, title, score, attempts = min(candidates, key=lambda item: item[0])
    if attempts == 0:
        reason = "Start this next curriculum topic"
    elif score < 50:
        reason = "Revisit this topic to strengthen the foundations"
    elif score < 75:
        reason = "One more practice session should build confidence"
    else:
        reason = "Keep this skill fresh"
    return {"subject": subject_name, "topic": topic_id, "title": title, "mastery": score, "reason": reason, "year": year}
