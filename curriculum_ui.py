"""Student curriculum explorer, pathways, assessments, and teacher manager."""

import copy
import random
import tkinter as tk
from tkinter import ttk

import classes
import curriculum
import save_system
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import clear, make_button, make_card, make_label, make_page_header, make_progress_bar, make_scrollable, make_section_header, make_stat, show_popup, style_notebook


def _mastery_state(user, subject, topic):
    record = user.get("mastery", {}).get(subject, {}).get(topic, {})
    attempts = int(record.get("attempts", 0)); score = curriculum.mastery_percent(user, subject, topic)
    if not attempts: return "Not started", score
    if score < 50: return "Needs revisiting", score
    if score < 75: return "Developing", score
    return "Secure", score


def _open_unit(root, app, unit, lesson=False):
    app.difficulty_value = int(unit["year"])
    app.difficulty_name = f"Year {unit['year']}"
    if lesson:
        import learning_experience
        learning_experience.show_lesson(root, app, unit["subject"], unit["id"]); return
    if unit["subject"] == "Maths":
        import maths
        maths.show_maths_screen(root, app, unit["id"])
    else:
        import english
        english.show_english_screen(root, app, topic=unit["id"])


def relevant_assessment_type(app, subject, topic):
    assessments=app.experience_store.topic_assessments(app.current_user,topic)
    due={(item["subject"],item["topic"]) for item in app.experience_store.retention_due(app.current_user)}
    return "starting" if not assessments else "retention" if (subject,topic) in due else "end"


def start_relevant_assessment(root, app, year, subject, topic):
    show_topic_assessment(root,app,year,subject,topic,relevant_assessment_type(app,subject,topic))


def _unit_card(parent, root, app, unit, on_refresh=None, teacher=False):
    user = save_system.get_user(app.save_data, app.current_user) or {}
    state, mastery = _mastery_state(user, unit["subject"], unit["id"])
    prereq_titles=[]
    for prereq in unit.get("prerequisites", []):
        detail=curriculum.topic_details(unit["year"],unit["subject"],prereq)
        if detail: prereq_titles.append(detail["title"])
    detail = f"Year {unit['year']} · {unit['subject']} · {unit['chapter']}\n{', '.join(unit['subskills'])}\n{state} · Mastery {mastery}%"
    if prereq_titles: detail += "\nPrior knowledge: " + ", ".join(prereq_titles)
    card=make_card(parent,unit["title"],detail,"#B56BFF" if unit["subject"]=="English" else THEME["accent"])
    make_progress_bar(card,mastery,"#B56BFF" if unit["subject"]=="English" else THEME["accent"]).pack(fill="x",pady=(9,1))
    if teacher:
        make_button(card,"Preview",lambda u=unit:show_question_preview(root,app,u))
        make_button(card,"Assign",lambda u=unit:_seed_assignment(root,app,u))
    else:
        bookmarks={(item["subject"],item["topic"]) for item in app.experience_store.bookmarks(app.current_user)}
        assessment_type=relevant_assessment_type(app,unit["subject"],unit["id"])
        make_button(card,"Learn",lambda u=unit:_open_unit(root,app,u,True))
        make_button(card,"Practise",lambda u=unit:_open_unit(root,app,u,False))
        make_button(card,{"starting":"Starting Check","retention":"Retention Check","end":"Assess"}[assessment_type],lambda u=unit,t=assessment_type:show_topic_assessment(root,app,u["year"],u["subject"],u["id"],t))
        def bookmark(u=unit):
            app.experience_store.toggle_bookmark(app.current_user,u["year"],u["subject"],u["id"])
            if on_refresh:on_refresh()
        make_button(card,"★ Saved" if (unit["subject"],unit["id"]) in bookmarks else "☆ Save",bookmark)
    return card


def show_curriculum_explorer(root, app):
    clear(root)
    body=make_page_header(root,"Curriculum Explorer","Search every Maths and English unit, follow a pathway, or return to saved topics.",app.main_menu)
    style_notebook(root); notebook=ttk.Notebook(body,style="Edu.TNotebook"); notebook.pack(fill="both",expand=True)
    browse_frame=tk.Frame(notebook,bg=THEME["bg"]); pathways_frame=tk.Frame(notebook,bg=THEME["bg"]); saved_frame=tk.Frame(notebook,bg=THEME["bg"])
    notebook.add(browse_frame,text="Browse & Search"); notebook.add(pathways_frame,text="Pathways"); notebook.add(saved_frame,text="Saved")
    browse=make_scrollable(browse_frame); pathways=make_scrollable(pathways_frame); saved=make_scrollable(saved_frame)
    query=tk.StringVar(); year=tk.StringVar(value=str(app.difficulty_value)); subject=tk.StringVar(value="Maths"); status=tk.StringVar(value="All progress"); chapter=tk.StringVar(value="All chapters")
    filters=make_card(browse,"Find a unit","Search titles and sub-skills, then narrow by year, subject or progress.",THEME["accent"]); filters.pack(fill="x",pady=(0,10))
    row=tk.Frame(filters,bg=filters["bg"]); row.pack(fill="x",pady=7)
    search_entry=tk.Entry(row,textvariable=query,font=FONT_TEXT); search_entry.pack(side="left",fill="x",expand=True,ipady=7,padx=(0,7))
    ttk.Combobox(row,values=[str(y) for y in range(7,12)],textvariable=year,state="readonly",width=8).pack(side="left",padx=4)
    ttk.Combobox(row,values=["Maths","English"],textvariable=subject,state="readonly",width=10).pack(side="left",padx=4)
    chapter_combo=ttk.Combobox(row,textvariable=chapter,state="readonly",width=20);chapter_combo.pack(side="left",padx=4)
    ttk.Combobox(row,values=["All progress","Not started","Developing","Secure","Needs revisiting","Bookmarked"],textvariable=status,state="readonly",width=18).pack(side="left",padx=4)
    results=tk.Frame(browse,bg=THEME["bg"]); results.pack(fill="both",expand=True)
    chapter_options={"All chapters":None}
    def rebuild(*_):
        for child in results.winfo_children():child.destroy()
        units=curriculum.curriculum_search(query.get(),int(year.get()),subject.get(),chapter_options.get(chapter.get()))
        user=save_system.get_user(app.save_data,app.current_user) or {}
        if status.get()=="Bookmarked":
            bookmarked={(item["subject"],item["topic"]) for item in app.experience_store.bookmarks(app.current_user)};units=[u for u in units if (u["subject"],u["id"]) in bookmarked]
        elif status.get()!="All progress": units=[u for u in units if _mastery_state(user,u["subject"],u["id"])[0]==status.get()]
        make_section_header(results,f"{len(units)} matching units","Results update as you type.")
        for unit in units[:60]: _unit_card(results,root,app,unit,rebuild).pack(fill="x",pady=5)
        if len(units)>60: make_label(results,"Showing the first 60 results. Add a search term to narrow the list.",FONT_TEXT).pack(pady=12)
    def refresh_chapters(*_):
        chapter_options.clear();chapter_options["All chapters"]=None
        for item in curriculum.chapters_for(int(year.get()),subject.get()):chapter_options[item["title"]]=item["id"]
        chapter_combo["values"]=list(chapter_options)
        if chapter.get() not in chapter_options:chapter.set("All chapters")
    for variable in (query,year,subject,status,chapter):variable.trace_add("write",rebuild)
    year.trace_add("write",refresh_chapters);subject.trace_add("write",refresh_chapters);refresh_chapters()
    search_entry.bind("<Return>",rebuild); rebuild()

    active=set(app.experience_store.active_pathways(app.current_user))
    make_section_header(pathways,"Guided pathways","Join a route and work through its units in a useful order.")
    for path in curriculum.pathways():
        units=curriculum.pathway_units(path["id"]); card=make_card(pathways,path["title"],f"{path['description']}\n{len(units)} units",THEME["accent"]); card.pack(fill="x",pady=5)
        make_button(card,"Open Pathway",lambda p=path:show_pathway(root,app,p["id"]))
        def toggle(p=path):
            is_active=p["id"] not in set(app.experience_store.active_pathways(app.current_user)); app.experience_store.enroll_pathway(app.current_user,p["id"],is_active); show_curriculum_explorer(root,app)
        make_button(card,"Leave" if path["id"] in active else "Join",toggle)

    def rebuild_saved():
        for child in saved.winfo_children():child.destroy()
        records=app.experience_store.bookmarks(app.current_user)
        make_section_header(saved,"Saved units",f"{len(records)} topic(s) saved for later.")
        for record in records:
            unit=curriculum.topic_details(record["year"],record["subject"],record["topic"])
            if unit:_unit_card(saved,root,app,unit,rebuild_saved).pack(fill="x",pady=5)
        if not records:make_card(saved,"Nothing saved yet","Use ☆ Save on any curriculum unit to keep it here.").pack(fill="x",pady=8)
    rebuild_saved()


def show_pathway(root,app,pathway_id):
    path=next((item for item in curriculum.pathways() if item["id"]==pathway_id),None)
    if not path:show_curriculum_explorer(root,app);return
    clear(root); body=make_page_header(root,path["title"],path["description"],lambda:show_curriculum_explorer(root,app)); body=make_scrollable(body)
    app.experience_store.enroll_pathway(app.current_user,pathway_id,True)
    units=curriculum.pathway_units(pathway_id); user=save_system.get_user(app.save_data,app.current_user) or {}
    completed=sum(_mastery_state(user,u["subject"],u["id"])[0]=="Secure" for u in units)
    summary=make_card(body,"Pathway progress",f"{completed} of {len(units)} units secure",THEME["accent"]); summary.pack(fill="x",pady=(0,10)); make_progress_bar(summary,completed/max(1,len(units))*100).pack(fill="x",pady=8)
    for unit in units:_unit_card(body,root,app,unit).pack(fill="x",pady=5)


def _english_assessment_question(year,topic,index):
    import english
    family=curriculum.question_family(year,"English",topic); pool=[]
    for text in english.texts_for_year(year,family): pool.extend(text.get("questions",[]))
    pool.append(english.EXTRA_QUESTIONS[(year,topic)])
    question=copy.deepcopy(pool[index%len(pool)]); question["topic"]=topic
    question.setdefault("difficulty",min(4,1+index)); question.setdefault("category",["Fluency","Applied","Reasoning","Exam-style"][index%4])
    return question


def show_topic_assessment(root,app,year,subject,topic,assessment_type="end"):
    import english, maths, maths_diagrams
    title=curriculum.topic_title(year,subject,topic); state={"index":0,"earned":0.0,"possible":0.0,"results":[]}; count=5
    def render():
        clear(root)
        if state["index"]>=count:
            app.experience_store.record_topic_assessment(app.current_user,year,subject,topic,assessment_type,state["earned"],state["possible"])
            curriculum.record_mastery(app.save_data,app.current_user,subject,topic,state["earned"],state["possible"])
            score=round(state["earned"]/max(1,state["possible"])*100)
            body=make_page_header(root,"Assessment complete",f"{title} · {assessment_type.title()} check",lambda:show_curriculum_explorer(root,app))
            stats=tk.Frame(body,bg=THEME["bg"]);stats.pack(fill="x",pady=18);make_stat(stats,f"{score}%","Score",THEME["accent"]).pack(side="left",fill="x",expand=True,padx=5);make_stat(stats,f"{state['earned']:g}/{state['possible']:g}","Marks","#58D68D").pack(side="left",fill="x",expand=True,padx=5)
            category_scores={}
            for result in state["results"]:
                totals=category_scores.setdefault(result["category"],[0,0]);totals[0]+=result["earned"];totals[1]+=result["possible"]
            strengths=[name for name,(earned,possible) in category_scores.items() if earned/max(1,possible)>=.7]
            focus=[name for name,(earned,possible) in category_scores.items() if earned/max(1,possible)<.7]
            unit=curriculum.topic_details(year,subject,topic) or {}; prereqs=[curriculum.topic_details(year,subject,item) for item in unit.get("prerequisites",[])];prereqs=[item["title"] for item in prereqs if item]
            make_card(body,"Strengths",", ".join(strengths) if strengths else "You completed the full check and created useful evidence for your next step.","#58D68D").pack(fill="x",pady=6)
            misconception=("Review how you approach " + ", ".join(focus) + " questions. Compare each response with the worked method and identify the first step that changed the answer.") if focus else "No repeated misconception was detected in this short check."
            make_card(body,"Possible misconception to review",misconception,"#FFB84D").pack(fill="x",pady=6)
            message="Schedule the retention check and continue to the next recommended unit." if score>=75 else ("Revisit this unit's worked examples and practise: " + ", ".join(unit.get("subskills",[])[:3])) if score>=50 else ("Review prior knowledge first: " + (", ".join(prereqs) if prereqs else ", ".join(unit.get("subskills",[])[:2])))
            make_card(body,"Recommended revision",message,"#58D68D" if score>=75 else "#FFB84D").pack(fill="x",pady=8);make_button(body,"Back to Curriculum",lambda:show_curriculum_explorer(root,app),wide=True);return
        question=maths.generate_question_data(year,topic,difficulty=min(4,1+state["index"]),category=["Fluency","Applied","Reasoning","Exam-style"][state["index"]%4]) if subject=="Maths" else _english_assessment_question(year,topic,state["index"])
        body=make_page_header(root,f"{assessment_type.title()} check",f"{title} · Question {state['index']+1} of {count} · {question.get('category','Practice')} · Level {question.get('difficulty',2)}",lambda:show_curriculum_explorer(root,app))
        card=make_card(body,question.get("prompt","Question"),accent=THEME["accent"],padding=22);card.pack(fill="both",expand=True,padx=70,pady=16)
        response=tk.StringVar(); text_response=None
        if subject=="Maths":
            diagram=maths_diagrams.render_diagram(card,question.get("diagram"),response)
            if diagram:diagram.pack(fill="x",pady=8)
        if question.get("type")=="multiple_choice":
            for choice in question.get("choices",[]):tk.Radiobutton(card,text=choice,value=choice,variable=response,font=FONT_TEXT,bg=card["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",card["bg"])).pack(anchor="w",pady=5)
        elif subject=="English":
            text_response=tk.Text(card,height=9,font=FONT_TEXT);text_response.pack(fill="both",expand=True,pady=10)
        else:
            tk.Entry(card,textvariable=response,font=FONT_SUBTITLE).pack(fill="x",pady=12,ipady=6)
        def submit():
            answer=text_response.get("1.0","end").strip() if text_response else response.get().strip()
            if not answer:show_popup(app,"Add an answer first.");return
            if subject=="Maths": earned=1 if maths.answer_is_correct(question,answer) else 0;possible=1;expected=question.get("answer","")
            else:earned,possible,_=english.mark_response(question,answer,year);expected=question.get("answer") or question.get("explanation") or ", ".join(question.get("keywords",[]))
            if earned<possible:
                app.experience_store.add_mistake(app.current_user,year,subject,topic,question.get("prompt",""),answer,expected)
            state["earned"]+=earned;state["possible"]+=possible;state["results"].append({"earned":earned,"possible":possible,"category":question.get("category","Practice")});state["index"]+=1;render()
        make_button(card,"Submit Answer",submit,wide=True)
    render()


def show_question_preview(root,app,unit):
    import english, maths
    question=maths.generate_question_data(unit["year"],unit["id"],difficulty=2,category="Applied") if unit["subject"]=="Maths" else _english_assessment_question(unit["year"],unit["id"],1)
    answer=question.get("answer") or ", ".join(question.get("keywords",[])) or "Teacher judgement using the success criteria"
    show_popup(app,f"{unit['title']}\n\n{question.get('prompt')}\n\nExpected answer / focus: {answer}\nCategory: {question.get('category','Applied')} · Difficulty {question.get('difficulty',2)}")


def _seed_assignment(root,app,unit):
    import assignments
    app.curriculum_assignment_seed={"year":unit["year"],"subject":unit["subject"],"topic":unit["id"],"title":unit["title"],"subskills":unit["subskills"]}
    assignments.show_teacher_assignments(root,app)


def show_curriculum_manager(root,app):
    user=save_system.get_user(app.save_data,app.current_user) or {}
    if user.get("role") not in ("teacher","admin"):app.main_menu();return
    clear(root);body=make_page_header(root,"Curriculum Manager","Browse, preview and assign exact units, then review class mastery.",app.open_teacher_hub);style_notebook(root)
    notebook=ttk.Notebook(body,style="Edu.TNotebook");notebook.pack(fill="both",expand=True);browse_frame=tk.Frame(notebook,bg=THEME["bg"]);mastery_frame=tk.Frame(notebook,bg=THEME["bg"]);notebook.add(browse_frame,text="Browse & Assign");notebook.add(mastery_frame,text="Class Mastery")
    browse=make_scrollable(browse_frame);mastery=make_scrollable(mastery_frame)
    query=tk.StringVar();year=tk.StringVar(value="7");subject=tk.StringVar(value="Maths")
    bar=make_card(browse,"Find curriculum content","Preview any unit or send it directly to the Assignment Centre.",THEME["accent"]);bar.pack(fill="x",pady=(0,8));row=tk.Frame(bar,bg=bar["bg"]);row.pack(fill="x");tk.Entry(row,textvariable=query,font=FONT_TEXT).pack(side="left",fill="x",expand=True,ipady=6);ttk.Combobox(row,values=[str(y) for y in range(7,12)],textvariable=year,state="readonly",width=8).pack(side="left",padx=5);ttk.Combobox(row,values=["Maths","English"],textvariable=subject,state="readonly",width=10).pack(side="left")
    results=tk.Frame(browse,bg=THEME["bg"]);results.pack(fill="both",expand=True)
    def rebuild(*_):
        for child in results.winfo_children():child.destroy()
        units=curriculum.curriculum_search(query.get(),int(year.get()),subject.get());make_section_header(results,f"{len(units)} units","Preview questions or assign a precise curriculum target.")
        for unit in units[:50]:_unit_card(results,root,app,unit,teacher=True).pack(fill="x",pady=4)
    for value in (query,year,subject):value.trace_add("write",rebuild)
    rebuild()
    owned=classes.get_classes(app.save_data) if user.get("role")=="admin" else classes.get_classes(app.save_data,app.current_user,"teacher");class_map={f"{item['title']} · Year {item['year_group']}":item for item in owned};class_var=tk.StringVar(value=next(iter(class_map),""));selector=ttk.Combobox(mastery,values=list(class_map),textvariable=class_var,state="readonly");selector.pack(fill="x",pady=8);mastery_results=tk.Frame(mastery,bg=THEME["bg"]);mastery_results.pack(fill="both",expand=True)
    def rebuild_mastery(*_):
        for child in mastery_results.winfo_children():child.destroy()
        cls=class_map.get(class_var.get())
        if not cls:make_card(mastery_results,"No classes","Create a class before reviewing curriculum mastery.").pack(fill="x");return
        students=cls.get("student_usernames",[]);units=curriculum.curriculum_search("",cls.get("year_group",7),cls.get("subject") if cls.get("subject") in ("Maths","English") else None)
        make_section_header(mastery_results,cls["title"],f"{len(students)} students · {len(units)} curriculum units")
        for unit in units:
            scores=[curriculum.mastery_percent(app.save_data.get("users",{}).get(name,{}),unit["subject"],unit["id"]) for name in students];attempted=sum(bool(app.save_data.get("users",{}).get(name,{}).get("mastery",{}).get(unit["subject"],{}).get(unit["id"],{}).get("attempts")) for name in students);average=round(sum(scores)/len(scores)) if scores else 0
            card=make_card(mastery_results,unit["title"],f"{attempted}/{len(students)} students started · Average mastery {average}%",THEME["accent"]);card.pack(fill="x",pady=4);make_progress_bar(card,average).pack(fill="x",pady=6);make_button(card,"Assign Support",lambda u=unit:_seed_assignment(root,app,u))
    class_var.trace_add("write",rebuild_mastery);rebuild_mastery()
