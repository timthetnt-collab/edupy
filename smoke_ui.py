"""Render important EduPy screens without entering the interactive main loop.

This is a local developer check. It does not publish, connect to a server, or
simulate passwords. Run it with the project's private Python environment.
"""

import tkinter as tk

from run_edupy import configure_tk_runtime


def run():
    configure_tk_runtime()
    original_mainloop = tk.Tk.mainloop
    tk.Tk.mainloop = lambda self: None
    try:
        from main import App
        import assignments
        import admin_dashboard
        import classes
        import curriculum_ui
        import english
        import learning_experience
        import maths
        import minigames
        import progress
        import platform_features
        import teacher_dashboard

        app = App()
    finally:
        tk.Tk.mainloop = original_mainloop

    failures = []

    try:
        app.root.update_idletasks(); app.root.update()
        print("OK: Login")
    except Exception as error:
        failures.append(("Login", error)); print(f"FAILED: Login: {error}")
    app.root.withdraw()

    def account_for(role):
        return next((name for name, profile in app.save_data.get("users", {}).items() if profile.get("role") == role), None)

    def render(label, username, screen):
        if not username:
            return
        try:
            account = app.account_db.get_account(username)
            app.current_user = username
            app.difficulty_value = account.year_group if account else app.save_data["users"][username].get("selected_year", 7)
            app.difficulty_name = f"Year {app.difficulty_value}"
            screen(); app.root.update_idletasks(); app.root.update()
            print(f"OK: {label}")
        except Exception as error:
            failures.append((label, error)); print(f"FAILED: {label}: {error}")

    student = account_for("student")
    teacher = account_for("teacher")
    admin = account_for("admin")
    render("student Today", student, lambda: learning_experience.show_today(app.root, app))
    render("student Subject menu", student, app.subject_menu)
    render("student Curriculum Explorer", student, lambda: curriculum_ui.show_curriculum_explorer(app.root, app))
    render("student guided pathway", student, lambda: curriculum_ui.show_pathway(app.root, app, "catch_up_maths"))
    render("student Year group", student, app.difficulty_menu)
    render("student Progress", student, lambda: progress.show_progress_screen(app.root, app))
    render("student Rewards", student, lambda: app.open_shop())
    render("student Assignments", student, lambda: assignments.show_student_assignments(app.root, app))
    render("student Maths topics", student, lambda: maths.show_maths_topics(app.root, app))
    render("Year 8 Maths chapters", student, lambda: (setattr(app, "difficulty_value", 8), setattr(app, "difficulty_name", "Year 8"), maths.show_maths_topics(app.root, app))[-1])
    render("Year 8 Geometry units", student, lambda: maths.show_year8_chapter(app.root, app, "geometry"))
    render("interactive graph question", student, lambda: maths.show_maths_screen(app.root, app, "gradient"))
    render("Year 7 Maths chapters", student, lambda: (setattr(app, "difficulty_value", 7), maths.show_maths_topics(app.root, app))[-1])
    render("Year 10 English chapters", student, lambda: (setattr(app, "difficulty_value", 10), english.show_english_topics(app.root, app))[-1])
    render("Maths topic assessment", student, lambda: curriculum_ui.show_topic_assessment(app.root, app, 7, "Maths", "number", "starting"))
    render("student English topics", student, lambda: english.show_english_topics(app.root, app))
    render("student Revision", student, lambda: learning_experience.show_revision_planner(app.root, app))
    render("student Mini-Games", student, lambda: minigames.show_minigames_menu(app.root, app))
    render("student Safety", student, lambda: learning_experience.show_safety_centre(app.root, app))
    render("student Learning Toolkit", student, lambda: platform_features.show_student_toolkit(app.root, app))
    render("student Mock Exam Centre", student, lambda: platform_features.show_mock_exam_setup(app.root, app))
    render("student Portfolio", student, lambda: platform_features.show_portfolio(app.root, app))
    render("student Notifications", student, lambda: platform_features.show_notifications(app.root, app))
    render("student Mistake Notebook", student, lambda: platform_features.show_mistake_notebook(app.root, app))
    render("student Certificates", student, lambda: platform_features.show_certificates(app.root, app))
    render("student Wellbeing", student, lambda: platform_features.show_wellbeing(app.root, app))
    render("student Live Classroom", student, lambda: platform_features.show_student_activities(app.root, app))
    render("Teacher Hub", teacher, lambda: teacher_dashboard.show_teacher_hub(app.root, app))
    render("Teacher Curriculum Manager", teacher, lambda: curriculum_ui.show_curriculum_manager(app.root, app))
    render("Class Management", teacher, lambda: classes.show_class_management(app.root, app))
    render("Assignment Centre", teacher, lambda: assignments.show_teacher_assignments(app.root, app))
    render("Teacher Platform Studio", teacher, lambda: platform_features.show_teacher_studio(app.root, app))
    render("Teacher Question Builder", teacher, lambda: platform_features.show_question_builder(app.root, app))
    render("Teacher Writing Feedback", teacher, lambda: platform_features.show_writing_feedback(app.root, app))
    render("Teacher Live Classroom", teacher, lambda: platform_features.show_teacher_activities(app.root, app))
    render("Teacher Coverage Map", teacher, lambda: platform_features.show_coverage_map(app.root, app))
    render("admin Safety", admin, lambda: learning_experience.show_safety_centre(app.root, app))
    render("Admin Dashboard", admin, lambda: admin_dashboard.show_admin_dashboard(app.root, app))
    app.root.destroy()
    if failures:
        raise SystemExit(1)
    print("All available UI smoke screens rendered successfully.")


if __name__ == "__main__":
    run()
