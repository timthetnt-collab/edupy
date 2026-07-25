"""EduPy 2 student, teacher and administrator feature workspaces."""

import datetime
import random
import time
import tkinter as tk
from tkinter import filedialog, ttk

import assignments
import classes
import curriculum
import curriculum_ui
import english
import maths
import save_system
import school_tools
from settings import THEME, FONT_SUBTITLE, FONT_TEXT
from ui import (clear, make_action_tile, make_button, make_card, make_label,
                make_page_header, make_progress_bar, make_scrollable,
                make_section_header, make_stat, show_popup, style_notebook)


def _profile(app):
    return save_system.get_user(app.save_data, app.current_user) or {}


def _owned_classes(app):
    role = _profile(app).get("role", "student")
    return classes.get_classes(app.save_data) if role == "admin" else classes.get_classes(app.save_data, app.current_user, "teacher")


def writing_feedback(text, year=7):
    """Return transparent, rubric-based writing guidance without pretending to be a teacher grade."""
    import re
    content = str(text).strip(); words = re.findall(r"[A-Za-z']+", content)
    sentences = [part.strip() for part in re.split(r"[.!?]+", content) if part.strip()]
    paragraphs = [part.strip() for part in content.split("\n") if part.strip()]
    vocabulary = len(set(word.lower() for word in words))
    checks = {
        "Development": min(100, round(len(words) / {7:80,8:110,9:140,10:180,11:220}.get(int(year),140) * 100)),
        "Structure": min(100, 25 * len(paragraphs) + (20 if len(sentences) >= 4 else 0)),
        "Sentence control": min(100, 20 * min(4, len({min(20, len(s.split())) for s in sentences})) + (20 if len(sentences) >= 3 else 0)),
        "Vocabulary": min(100, round(vocabulary / max(1, len(words)) * 180)),
        "Punctuation": min(100, 20 * len(set(re.findall(r"[,.!?;:\-()]", content))) + (20 if content[:1].isupper() else 0)),
    }
    strengths = [name for name, value in checks.items() if value >= 70]
    focus = sorted(checks, key=checks.get)[:2]
    suggestions = {
        "Development":"Add a specific example, then explain why it matters.",
        "Structure":"Use purposeful paragraphs and make each one move the response forward.",
        "Sentence control":"Mix shorter sentences with developed ones, then check each sentence is complete.",
        "Vocabulary":"Replace general words with precise verbs and nouns that fit the purpose.",
        "Punctuation":"Proofread capitals and sentence endings before adding ambitious punctuation.",
    }
    return {"scores":checks,"strengths":strengths,"focus":focus,
            "feedback":" ".join(suggestions[name] for name in focus),"word_count":len(words)}


def show_student_toolkit(root, app):
    clear(root); body=make_page_header(root,"My Learning Toolkit","Exams, planning, evidence, achievements and support in one place.",app.main_menu)
    body=make_scrollable(body); grid=tk.Frame(body,bg=THEME["bg"]);grid.pack(fill="both",expand=True)
    for column in range(3):grid.grid_columnconfigure(column,weight=1,uniform="student_tools")
    unread=sum(not item["read"] for item in app.experience_store.notifications(app.current_user))
    mistakes=len(app.experience_store.mistakes(app.current_user)); certificates=len(app.experience_store.certificates(app.current_user))
    tools=(
        ("Mock Exams","Timed Maths and English papers with flags and a result breakdown.",lambda:show_mock_exam_setup(root,app),"#4EA3FF"),
        ("Revision Calendar","A personalised schedule built around your assessment date.",lambda:__import__('learning_experience').show_revision_planner(root,app),"#B56BFF"),
        ("My Portfolio","Save essays, projects and examples you are proud of.",lambda:show_portfolio(root,app),"#58D68D"),
        (f"Notifications ({unread})","Deadlines, feedback, class activities and achievements.",lambda:show_notifications(root,app),"#FFB84D"),
        (f"Mistake Notebook ({mistakes})","Turn incorrect answers into focused revision.",lambda:show_mistake_notebook(root,app),"#FF7A8A"),
        (f"Certificates ({certificates})","Celebrate genuine progress and completed milestones.",lambda:show_certificates(root,app),"#FFD166"),
        ("Live Classroom","Answer teacher polls, quizzes and discussion prompts.",lambda:show_student_activities(root,app),"#5EC7C2"),
        ("Wellbeing Check-in","Pause, reflect and find the right kind of support.",lambda:show_wellbeing(root,app),"#9B8AFB"),
        ("Accessibility","Reading, spacing, motion, contrast and working-time preferences.",lambda:__import__('learning_experience').show_safety_centre(root,app),"#6EA8FF"),
        ("My Goals","Set manageable targets and reflect when you complete them.",lambda:school_tools.show_student_goals(root,app),"#58D68D"),
        ("Teacher Resources","Open lesson explanations published for your year.",lambda:school_tools.show_published_resources(root,app),"#4EA3FF"),
    )
    for index,(title,detail,command,accent) in enumerate(tools):
        make_action_tile(grid,title,detail,command,accent).grid(row=index//3,column=index%3,sticky="nsew",padx=6,pady=6)


def _exam_question(app, subject, index):
    year=app.difficulty_value; topics=[topic for topic,_ in curriculum.topics_for(year,subject)]
    topic=topics[index%len(topics)]
    if subject=="Maths":
        question=maths.generate_question_data(year,topic,difficulty=min(4,1+index//2),category=["Fluency","Applied","Reasoning","Exam-style"][index%4])
    else:
        question=curriculum_ui._english_assessment_question(year,topic,index)
    question=dict(question);question["topic"]=topic
    custom=app.experience_store.custom_questions(app.current_user,status="approved",year_group=year,subject=subject)
    if custom and index%4==3:
        source=custom[index%len(custom)];question={"topic":source["topic"],"prompt":source["prompt"],"type":source["type"],"custom_id":source["id"],
            "choices":source["choices"],"answer":source["answer"],"keywords":[word for word in source["answer"].lower().split() if len(word)>2],
            "explanation":"Compare your response with the teacher-approved expected answer.","max_score":source["marks"],"category":"Teacher-created","difficulty":3}
    return question


def show_mock_exam_setup(root,app):
    clear(root);body=make_page_header(root,"Mock Exam Centre","Practise under timed conditions, flag questions and review every mistake.",lambda:show_student_toolkit(root,app));body=make_scrollable(body)
    setup=make_card(body,"Create a paper","Choose a subject and paper length. Your recorded extra-time preference is applied automatically.",THEME["accent"]);setup.pack(fill="x",pady=8)
    subject=tk.StringVar(value="Maths");count=tk.StringVar(value="10")
    row=tk.Frame(setup,bg=setup["bg"]);row.pack(fill="x",pady=8)
    ttk.Combobox(row,values=["Maths","English"],textvariable=subject,state="readonly").pack(side="left",padx=4)
    ttk.Combobox(row,values=["5","10","15"],textvariable=count,state="readonly").pack(side="left",padx=4)
    make_button(setup,"Start Timed Paper",lambda:start_mock_exam(root,app,subject.get(),int(count.get())),wide=True)
    attempts=app.experience_store.mock_exams(app.current_user)
    make_section_header(body,"Previous papers",f"{len(attempts)} completed paper(s)")
    for item in attempts:
        score=round(item["earned"]/max(1,item["possible"])*100)
        make_card(body,f"Year {item['year']} {item['subject']}",f"{score}% · {item['completed_at'][:10]} · {item['duration']//60}m {item['duration']%60}s · {item['flagged']} flagged", "#58D68D" if score>=70 else "#FFB84D").pack(fill="x",pady=4)


def start_mock_exam(root,app,subject,count):
    questions=[_exam_question(app,subject,i) for i in range(count)]
    extra=app.experience_store.preferences(app.current_user).get("extra_time_percent",0)
    allowance=round(count*90*(1+extra/100));started=time.monotonic()
    state={"index":0,"earned":0.0,"possible":0.0,"flagged":set(),"results":[],"finished":False}
    def finish():
        if state["finished"]:return
        state["finished"]=True
        duration=round(time.monotonic()-started);app.experience_store.record_mock_exam(app.current_user,app.difficulty_value,subject,state["earned"],state["possible"],duration,len(state["flagged"]))
        score=round(state["earned"]/max(1,state["possible"])*100)
        if score>=80:app.experience_store.award_certificate(app.current_user,f"exam-{subject}-{score//10}",f"{subject} Mock Exam Distinction",f"Achieved {score}% in a Year {app.difficulty_value} timed paper.")
        clear(root);body=make_page_header(root,"Paper complete",f"Year {app.difficulty_value} {subject}",lambda:show_mock_exam_setup(root,app))
        stats=tk.Frame(body,bg=THEME["bg"]);stats.pack(fill="x",pady=15)
        make_stat(stats,f"{score}%","Score",THEME["accent"]).pack(side="left",fill="x",expand=True,padx=4);make_stat(stats,f"{state['earned']:g}/{state['possible']:g}","Marks","#58D68D").pack(side="left",fill="x",expand=True,padx=4);make_stat(stats,len(state["flagged"]),"Flagged","#FFB84D").pack(side="left",fill="x",expand=True,padx=4)
        by_category={}
        for result in state["results"]:
            bucket=by_category.setdefault(result["category"],[0,0]);bucket[0]+=result["earned"];bucket[1]+=result["possible"]
        for category,(earned,possible) in by_category.items():make_card(body,category,f"{round(earned/max(1,possible)*100)}% · {earned:g}/{possible:g} marks").pack(fill="x",pady=4)
        make_button(body,"Review Mistake Notebook",lambda:show_mistake_notebook(root,app),wide=True)
    def render():
        if state["index"]>=count:return finish()
        clear(root);question=questions[state["index"]];remaining=max(0,allowance-round(time.monotonic()-started))
        body=make_page_header(root,f"{subject} Mock Paper",f"Question {state['index']+1} of {count} · {question.get('category','Practice')}")
        timer=tk.Label(body,text=f"Time remaining {remaining//60:02d}:{remaining%60:02d}",font=FONT_SUBTITLE,bg=THEME["bg"],fg=THEME.get("warning",THEME["accent"]));timer.pack(anchor="e")
        current_index=state["index"]
        def tick():
            if state["finished"] or state["index"]!=current_index:return
            left=max(0,allowance-round(time.monotonic()-started))
            try:timer.config(text=f"Time remaining {left//60:02d}:{left%60:02d}")
            except tk.TclError:return
            if left<=0:
                for unanswered in questions[state["index"]:]:
                    possible=1 if subject=="Maths" else int(unanswered.get("max_score",1))
                    state["possible"]+=possible;state["results"].append({"earned":0,"possible":possible,"category":unanswered.get("category","Unanswered")})
                state["index"]=count;finish()
            else:root.after(1000,tick)
        tick()
        progress=make_progress_bar(body,state["index"]/count*100);progress.pack(fill="x",pady=(0,10))
        card=make_card(body,question.get("prompt","Question"),accent=THEME["accent"],padding=24);card.pack(fill="both",expand=True,padx=70,pady=10)
        response=tk.StringVar();textbox=None
        if question.get("type")=="multiple_choice":
            for choice in question.get("choices",[]):tk.Radiobutton(card,text=choice,value=choice,variable=response,font=FONT_TEXT,bg=card["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",card["bg"])).pack(anchor="w",pady=5)
        elif subject=="English" or question.get("type")=="extended":textbox=tk.Text(card,height=9,font=FONT_TEXT);textbox.pack(fill="both",expand=True,pady=8)
        else:tk.Entry(card,textvariable=response,font=FONT_SUBTITLE).pack(fill="x",ipady=7,pady=10)
        flagged=tk.BooleanVar(value=state["index"] in state["flagged"]);tk.Checkbutton(card,text="Flag this question to review",variable=flagged,font=FONT_TEXT,bg=card["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",card["bg"])).pack(anchor="w",pady=8)
        def submit():
            answer=textbox.get("1.0","end").strip() if textbox else response.get().strip()
            if not answer:show_popup(app,"Add an answer before moving on.");return
            if flagged.get():state["flagged"].add(state["index"])
            if subject=="Maths":earned=1 if maths.answer_is_correct(question,answer) else 0;possible=1;expected=question.get("answer","")
            else:earned,possible,_=english.mark_response(question,answer,app.difficulty_value);expected=question.get("answer") or question.get("explanation") or ", ".join(question.get("keywords",[]))
            state["earned"]+=earned;state["possible"]+=possible;state["results"].append({"earned":earned,"possible":possible,"category":question.get("category","Practice")})
            if earned<possible:app.experience_store.add_mistake(app.current_user,app.difficulty_value,subject,question["topic"],question.get("prompt",""),answer,expected)
            state["index"]+=1;render()
        make_button(card,"Save Answer & Continue",submit,wide=True)
        if question.get("custom_id"):
            make_button(card,"Report This Question as Unclear",lambda q=question:show_popup(app,"Report sent for administrator review." if app.experience_store.report_content(app.current_user,"Student reported this question as unclear.",q["custom_id"]) else "The report could not be saved."),wide=True,kind="secondary")
    render()


def show_portfolio(root,app):
    clear(root);body=make_page_header(root,"My Portfolio","Keep meaningful evidence of your work and progress.",lambda:show_student_toolkit(root,app));body=make_scrollable(body)
    form=make_card(body,"Add an item","Paste a short extract or describe where the work is stored. Do not add private contact information.",THEME["accent"]);form.pack(fill="x",pady=8)
    title=tk.Entry(form,font=FONT_TEXT);title.pack(fill="x",ipady=5,pady=4);title.insert(0,"Title of work")
    subject=tk.StringVar(value="English");ttk.Combobox(form,values=["Maths","English","Project","Other"],textvariable=subject,state="readonly").pack(fill="x",pady=4)
    description=tk.Text(form,height=3,font=FONT_TEXT);description.pack(fill="x",pady=4);evidence=tk.Text(form,height=5,font=FONT_TEXT);evidence.pack(fill="x",pady=4)
    def add():
        if app.experience_store.add_portfolio_item(app.current_user,title.get(),subject.get(),description.get("1.0","end"),evidence.get("1.0","end")):show_portfolio(root,app)
        else:show_popup(app,"Add a clear title before saving.")
    make_button(form,"Save to Portfolio",add,wide=True)
    items=app.experience_store.portfolio(app.current_user);make_section_header(body,"Saved work",f"{len(items)} item(s)")
    for item in items:
        card=make_card(body,item["title"],f"{item['subject']} · {item['created_at'][:10]}\n{item['description']}\n\n{item['evidence'][:350]}","#58D68D");card.pack(fill="x",pady=5)
        make_button(card,"Remove",lambda i=item["id"]:(app.experience_store.portfolio(app.current_user,i),show_portfolio(root,app)),kind="secondary")


def show_notifications(root,app):
    clear(root);body=make_page_header(root,"Notification Centre","Learning reminders and updates—without advertising or payment messages.",lambda:show_student_toolkit(root,app));body=make_scrollable(body)
    due=[item for item in assignments.assignments_for_student(app.save_data,app.current_user) if assignments.assignment_state(item,app.current_user) in ("To do","Overdue")]
    if due:
        card=make_card(body,"Assignment reminders",f"{len(due)} assignment(s) need attention.","#FF7043");card.pack(fill="x",pady=5);make_button(card,"Open Assignments",lambda:assignments.show_student_assignments(root,app))
    items=app.experience_store.notifications(app.current_user);make_section_header(body,"Updates",f"{sum(not x['read'] for x in items)} unread")
    for item in items:
        card=make_card(body,("● " if not item["read"] else "")+item["title"],f"{item['category']} · {item['created_at'][:10]}\n{item['message']}",THEME["accent"] if not item["read"] else THEME.get("border",THEME["accent"]));card.pack(fill="x",pady=4)
        if not item["read"]:make_button(card,"Mark Read",lambda i=item["id"]:(app.experience_store.notifications(app.current_user,i),show_notifications(root,app)),kind="secondary")
    if not items:make_card(body,"All clear","New feedback, activities and achievements will appear here.").pack(fill="x",pady=6)


def show_mistake_notebook(root,app):
    clear(root);body=make_page_header(root,"Mistake Notebook","Mistakes are revision clues—not labels.",lambda:show_student_toolkit(root,app));body=make_scrollable(body)
    items=app.experience_store.mistakes(app.current_user);make_section_header(body,"Ready to review",f"{len(items)} question(s)")
    for item in items:
        title=curriculum.topic_title(item["year"],item["subject"],item["topic"])
        card=make_card(body,title,f"{item['prompt']}\n\nYour answer: {item['response']}\nExpected focus: {item['expected']}","#FF7A8A");card.pack(fill="x",pady=5)
        unit=curriculum.topic_details(item["year"],item["subject"],item["topic"])
        if unit:make_button(card,"Practise Topic",lambda u=unit:curriculum_ui._open_unit(root,app,u,False))
        make_button(card,"I Can Do This Now",lambda i=item["id"]:(app.experience_store.mistakes(app.current_user,master_id=i),show_mistake_notebook(root,app)),kind="secondary")
    if not items:make_card(body,"Notebook clear","Incorrect mock-exam and assessment answers will appear here automatically.","#58D68D").pack(fill="x",pady=8)


def _refresh_certificates(app):
    exams=app.experience_store.mock_exams(app.current_user);portfolio=app.experience_store.portfolio(app.current_user)
    if exams:app.experience_store.award_certificate(app.current_user,"first-mock","First Mock Exam","Completed a full timed EduPy paper.")
    if len(portfolio)>=3:app.experience_store.award_certificate(app.current_user,"portfolio-3","Portfolio Builder","Saved three meaningful examples of work.")
    user=_profile(app);secure=sum(curriculum.mastery_percent(user,subject,topic)>=75 for subject,topics in user.get("mastery",{}).items() for topic in topics)
    if secure>=10:app.experience_store.award_certificate(app.current_user,"secure-10","Ten Topics Secure","Reached secure mastery in ten curriculum units.")


def show_certificates(root,app):
    _refresh_certificates(app);clear(root);body=make_page_header(root,"My Certificates","Milestones earned through real learning.",lambda:show_student_toolkit(root,app));body=make_scrollable(body)
    items=app.experience_store.certificates(app.current_user)
    for item in items:
        card=make_card(body,"★  "+item["title"],f"Awarded to {app.current_user}\n{item['detail']}\nIssued {item['issued_at'][:10]}","#FFD166");card.pack(fill="x",padx=80,pady=8)
        def export(c=item):
            path=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text certificate","*.txt")],initialfile=c["title"].replace(" ","_")+".txt")
            if path:
                with open(path,"w",encoding="utf-8") as handle:handle.write(f"EDUPY CERTIFICATE\n\n{c['title']}\nAwarded to {app.current_user}\n\n{c['detail']}\nIssued {c['issued_at'][:10]}\n")
        make_button(card,"Save Printable Copy",export,kind="secondary")
    if not items:make_card(body,"Your first certificate is waiting","Complete a mock exam, build your portfolio or secure ten curriculum units.").pack(fill="x",pady=8)


def show_wellbeing(root,app):
    clear(root);body=make_page_header(root,"Wellbeing Check-in","A private moment to notice how learning feels today.",lambda:show_student_toolkit(root,app));body=make_scrollable(body)
    make_card(body,"Important","EduPy is not an emergency or counselling service. If you feel unsafe or someone is in danger, tell a trusted adult immediately.","#FF7043").pack(fill="x",pady=8)
    form=make_card(body,"How are you feeling?","Choose 1 for struggling through to 5 for feeling good. Your note stays in your own check-in history.","#9B8AFB");form.pack(fill="x",pady=8)
    mood=tk.IntVar(value=3);row=tk.Frame(form,bg=form["bg"]);row.pack(pady=7)
    for value,label in ((1,"Very low"),(2,"Low"),(3,"Okay"),(4,"Good"),(5,"Great")):tk.Radiobutton(row,text=label,value=value,variable=mood,font=FONT_TEXT,bg=form["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",form["bg"])).pack(side="left",padx=8)
    note=tk.Text(form,height=4,font=FONT_TEXT);note.pack(fill="x",pady=6)
    def save():app.experience_store.wellbeing_checkin(app.current_user,mood.get(),note.get("1.0","end"));show_wellbeing(root,app)
    make_button(form,"Save Private Check-in",save,wide=True)
    make_card(body,"Small next steps","Try one: take a short screen break, get some water, reduce today’s task to ten minutes, or ask a trusted adult or teacher for help.","#58D68D").pack(fill="x",pady=8)
    history=app.experience_store.my_wellbeing(app.current_user,7)
    if history:make_card(body,"Recent pattern"," · ".join(f"{item['created_at'][:10]}: {item['mood']}/5" for item in history),THEME["accent"]).pack(fill="x",pady=6)


def show_student_activities(root,app):
    clear(root);body=make_page_header(root,"Live Classroom","Join teacher-led polls, quizzes and discussions.",lambda:show_student_toolkit(root,app));body=make_scrollable(body)
    items=app.experience_store.activities(app.current_user);make_section_header(body,"Live now",f"{len(items)} activity or activities")
    for item in items:
        card=make_card(body,item["title"],f"{item['type'].title()} · {item['prompt']}","#5EC7C2");card.pack(fill="x",pady=6);response=tk.StringVar()
        if item["options"]:
            for choice in item["options"]:tk.Radiobutton(card,text=choice,value=choice,variable=response,font=FONT_TEXT,bg=card["bg"],fg=THEME["fg"],selectcolor=THEME.get("panel_alt",card["bg"])).pack(anchor="w")
        else:tk.Entry(card,textvariable=response,font=FONT_TEXT).pack(fill="x",ipady=5,pady=5)
        make_button(card,"Send Response",lambda i=item,v=response:show_popup(app,"Response sent." if app.experience_store.respond_activity(app.current_user,i["id"],v.get()) else "Add a response first."))
    if not items:make_card(body,"Nothing live right now","Your teacher’s next poll, quiz or discussion will appear here.").pack(fill="x",pady=8)


def show_teacher_studio(root,app):
    role=_profile(app).get("role")
    if role not in ("teacher","admin"):app.main_menu();return
    clear(root);body=make_page_header(root,"Platform Studio","Create, teach, review and manage curriculum quality.",app.open_teacher_hub);body=make_scrollable(body)
    grid=tk.Frame(body,bg=THEME["bg"]);grid.pack(fill="both",expand=True)
    for column in range(3):grid.grid_columnconfigure(column,weight=1,uniform="studio")
    tools=[
        ("Question Builder","Create reusable questions and submit them for approval.",lambda:show_question_builder(root,app),"#4EA3FF"),
        ("Writing Feedback","Use a transparent Year 7–11 writing rubric.",lambda:show_writing_feedback(root,app),"#B56BFF"),
        ("Live Classroom","Run polls, quizzes and discussion prompts.",lambda:show_teacher_activities(root,app),"#5EC7C2"),
        ("Curriculum Coverage","See assigned, started and secure content by class.",lambda:show_coverage_map(root,app),"#58D68D"),
        ("Revision & Exams","Open curriculum assessments and exam preparation tools.",lambda:curriculum_ui.show_curriculum_manager(root,app),"#FFB84D"),
        ("Class Administration","Manage rosters, roles and class details.",lambda:classes.show_class_management(root,app),"#FF7A8A"),
        ("Assessment Builder","Generate, export and assign balanced curriculum papers.",lambda:school_tools.show_assessment_builder(root,app),"#4EA3FF"),
        ("Intervention Dashboard","Review explainable patterns and agree supportive next steps.",lambda:school_tools.show_intervention_dashboard(root,app),"#FFB84D"),
        ("Content Studio","Publish reusable lesson explanations and worked examples.",lambda:school_tools.show_content_studio(root,app),"#58D68D"),
    ]
    if role=="admin":tools.append(("Admin Dashboard","Accounts, safeguarding, privacy and content moderation.",lambda:__import__('admin_dashboard').show_admin_dashboard(root,app),"#FFD166"))
    for index,(title,detail,command,accent) in enumerate(tools):make_action_tile(grid,title,detail,command,accent).grid(row=index//3,column=index%3,sticky="nsew",padx=6,pady=6)


def show_question_builder(root,app):
    clear(root);body=make_page_header(root,"Teacher Question Builder","Create questions without editing code. Submitted questions require admin approval.",lambda:show_teacher_studio(root,app));body=make_scrollable(body)
    form=make_card(body,"New question","Choose a precise curriculum unit and include an unambiguous expected answer.",THEME["accent"]);form.pack(fill="x",pady=7)
    year=tk.StringVar(value="7");subject=tk.StringVar(value="Maths");qtype=tk.StringVar(value="short");topic=tk.StringVar()
    row=tk.Frame(form,bg=form["bg"]);row.pack(fill="x",pady=4)
    ttk.Combobox(row,values=[str(x) for x in range(7,12)],textvariable=year,state="readonly",width=8).pack(side="left",padx=3);ttk.Combobox(row,values=["Maths","English"],textvariable=subject,state="readonly",width=10).pack(side="left",padx=3);ttk.Combobox(row,values=["short","multiple_choice","extended"],textvariable=qtype,state="readonly",width=18).pack(side="left",padx=3)
    topic_combo=ttk.Combobox(form,textvariable=topic,state="readonly");topic_combo.pack(fill="x",pady=4);topic_map={}
    def topics(*_):
        topic_map.clear()
        for unit_id,title in curriculum.topics_for(int(year.get()),subject.get()):topic_map[f"{title} [{unit_id}]"]=unit_id
        topic_combo["values"]=list(topic_map)
        if topic.get() not in topic_map and topic_map:topic.set(next(iter(topic_map)))
    year.trace_add("write",topics);subject.trace_add("write",topics);topics()
    make_label(form,"Question prompt",FONT_TEXT).pack(anchor="w",pady=(8,0));prompt=tk.Text(form,height=4,font=FONT_TEXT);prompt.pack(fill="x",pady=4)
    make_label(form,"Expected answer",FONT_TEXT).pack(anchor="w",pady=(6,0));answer=tk.Entry(form,font=FONT_TEXT);answer.pack(fill="x",ipady=5,pady=4)
    make_label(form,"Multiple-choice options (separated by commas)",FONT_TEXT).pack(anchor="w",pady=(6,0));choices=tk.Entry(form,font=FONT_TEXT);choices.pack(fill="x",ipady=5,pady=4)
    def create(submit):
        options=[] if qtype.get()!="multiple_choice" else [x.strip() for x in choices.get().split(",")]
        result=app.experience_store.create_custom_question(app.current_user,int(year.get()),subject.get(),topic_map.get(topic.get(),""),qtype.get(),prompt.get("1.0","end"),answer.get(),options,1,submit)
        if result:show_question_builder(root,app)
        else:show_popup(app,"Check the prompt, answer and multiple-choice options.")
    make_button(form,"Save Draft",lambda:create(False));make_button(form,"Submit for Approval",lambda:create(True))
    items=app.experience_store.custom_questions(app.current_user);make_section_header(body,"My question bank",f"{len(items)} question(s)")
    for item in items:make_card(body,item["prompt"],f"Year {item['year']} {item['subject']} · {item['type'].replace('_',' ').title()} · {item['status'].title()}\nAnswer: {item['answer']}"+(f"\nModerator: {item['note']}" if item['note'] else ""),"#58D68D" if item["status"]=="approved" else "#FFB84D").pack(fill="x",pady=4)


def show_writing_feedback(root,app):
    clear(root);body=make_page_header(root,"Writing Feedback Studio","A transparent first review for teachers—not a replacement for professional judgement.",lambda:show_teacher_studio(root,app));body=make_scrollable(body)
    year=tk.StringVar(value="8");ttk.Combobox(body,values=[str(x) for x in range(7,12)],textvariable=year,state="readonly").pack(anchor="w",pady=5)
    response=tk.Text(body,height=15,font=FONT_TEXT);response.pack(fill="both",expand=True,pady=7);results=tk.Frame(body,bg=THEME["bg"]);results.pack(fill="x")
    def analyse():
        for child in results.winfo_children():child.destroy()
        report=writing_feedback(response.get("1.0","end"),int(year.get()))
        make_card(results,"Teacher review prompt",f"{report['word_count']} words · Strengths: {', '.join(report['strengths']) or 'Not enough evidence yet'}\nNext steps: {report['feedback']}",THEME["accent"]).pack(fill="x",pady=6)
        for name,value in report["scores"].items():
            card=make_card(results,name,f"Evidence indicator: {value}%");card.pack(fill="x",pady=3);make_progress_bar(card,value).pack(fill="x",pady=4)
    make_button(body,"Analyse Against Rubric",analyse,wide=True)


def show_teacher_activities(root,app):
    clear(root);body=make_page_header(root,"Live Classroom Studio","Create low-pressure polls, quizzes and discussion prompts.",lambda:show_teacher_studio(root,app));body=make_scrollable(body)
    owned=_owned_classes(app);class_map={f"{c['title']} · Year {c['year_group']}":c for c in owned};selected=tk.StringVar(value=next(iter(class_map),""));kind=tk.StringVar(value="poll")
    form=make_card(body,"Start an activity","Student names are not displayed in the live summary.","#5EC7C2");form.pack(fill="x",pady=6)
    ttk.Combobox(form,values=list(class_map),textvariable=selected,state="readonly").pack(fill="x",pady=3);ttk.Combobox(form,values=["poll","quiz","discussion"],textvariable=kind,state="readonly").pack(fill="x",pady=3)
    title=tk.Entry(form,font=FONT_TEXT);title.pack(fill="x",ipady=5,pady=3);title.insert(0,"Quick class check")
    prompt=tk.Entry(form,font=FONT_TEXT);prompt.pack(fill="x",ipady=5,pady=3);options=tk.Entry(form,font=FONT_TEXT);options.pack(fill="x",ipady=5,pady=3);options.insert(0,"Option A, Option B, Option C")
    def create():
        cls=class_map.get(selected.get());activity=app.experience_store.create_activity(app.current_user,cls["id"] if cls else "",title.get(),kind.get(),prompt.get(),options.get().split(",") if kind.get()!="discussion" else [])
        if activity:
            for student in cls.get("student_usernames",[]):app.experience_store.notify(student,"New live classroom activity",title.get(),"Classroom")
            show_teacher_activities(root,app)
        else:show_popup(app,"Choose a class and add a prompt.")
    make_button(form,"Start Live Activity",create,wide=True)
    for item in app.experience_store.activities(app.current_user):
        counts={choice:item["responses"].count(choice) for choice in item["options"]};summary=" · ".join(f"{k}: {v}" for k,v in counts.items()) if counts else f"{len(item['responses'])} response(s)"
        card=make_card(body,item["title"],f"{item['prompt']}\n{summary}","#5EC7C2");card.pack(fill="x",pady=5);make_button(card,"Close Activity",lambda i=item["id"]:(app.experience_store.close_activity(app.current_user,i),show_teacher_activities(root,app)),kind="secondary")


def coverage_rows(data, cls):
    students=cls.get("student_usernames",[]);year=cls.get("year_group",7);rows=[]
    assigned={}
    for work in data.get("assignments",{}).values():
        if work.get("class_id")!=cls.get("id"):continue
        target=assignments.curriculum_target(work.get("pack_id"))
        if target:assigned[(target["subject"],target["id"])]=assigned.get((target["subject"],target["id"]),0)+1
    for subject in ("Maths","English"):
        for topic,title in curriculum.topics_for(year,subject):
            scores=[curriculum.mastery_percent(data.get("users",{}).get(student,{}),subject,topic) for student in students]
            started=sum(score>0 for score in scores);secure=sum(score>=75 for score in scores)
            if assigned.get((subject,topic)) or started:rows.append({"subject":subject,"topic":topic,"title":title,"assigned":assigned.get((subject,topic),0),"started":started,"secure":secure,"average":round(sum(scores)/max(1,len(scores)))})
    return rows


def show_coverage_map(root,app):
    clear(root);body=make_page_header(root,"Curriculum Coverage Map","See what has been assigned, started and secured—without ranking children.",lambda:show_teacher_studio(root,app));body=make_scrollable(body)
    owned=_owned_classes(app);mapping={f"{c['title']} · Year {c['year_group']}":c for c in owned};selected=tk.StringVar(value=next(iter(mapping),""));selector=ttk.Combobox(body,values=list(mapping),textvariable=selected,state="readonly");selector.pack(fill="x",pady=6);results=tk.Frame(body,bg=THEME["bg"]);results.pack(fill="x")
    def rebuild(*_):
        for child in results.winfo_children():child.destroy()
        cls=mapping.get(selected.get());rows=coverage_rows(app.save_data,cls) if cls else []
        make_section_header(results,"Coverage evidence",f"{len(rows)} units with assignment or practice evidence")
        for item in rows:
            card=make_card(results,item["title"],f"{item['subject']} · Assigned {item['assigned']} time(s) · {item['started']}/{len(cls.get('student_usernames',[]))} started · {item['secure']} secure · Average {item['average']}%", "#58D68D" if item["secure"] else "#FFB84D");card.pack(fill="x",pady=3);make_progress_bar(card,item["average"]).pack(fill="x",pady=4)
        if not rows:make_card(results,"No coverage evidence yet","Assign a curriculum unit or let students begin independent practice.").pack(fill="x",pady=6)
    selected.trace_add("write",rebuild);rebuild()
