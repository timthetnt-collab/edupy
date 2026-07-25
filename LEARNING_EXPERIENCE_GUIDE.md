# EduPy learning experience guide

## Student journey

After signing in, students now arrive on **Today**. This page shows assignments,
revision tasks, recommended curriculum topics, and quick links without presenting
the entire platform at once.

Today also lets students continue their most recently opened lesson and shows a
friendly summary of their latest starting check. Recommendations can be opened
as a lesson or taken straight into practice.

Students who have not completed a starting check see **Take Starting Check**.
The check contains eight year-matched questions: four Maths and four English.
It is not a school grade. Results seed topic mastery and create the first
personalised learning path.

Every Maths and English topic now offers:

1. **Learn** — explanation, method, worked example, common mistake, vocabulary.
2. **Practise** — year-matched questions and feedback.
3. Updated mastery and a recommended next step.

Maths questions generate fresh numerical variations. English now contains three
main practice texts and at least seven varied built-in questions for every year,
plus topic-specific and diagnostic questions.
English lesson explanations are now specific to the skill being studied, from
retrieval and inference through GCSE assessment objectives and exam strategy.

## Revision planner

Students enter an assessment name and future date. EduPy creates ten spaced
sessions from their weakest or unseen topics. Sessions can be opened as lessons
and marked complete. A newly created plan replaces the previous plan.
Overdue, due-today, upcoming, and completed sessions are visually distinct, and
students can rebuild the plan when an assessment date changes.

## Teacher tools

Teacher Hub now includes:

- **Marking** — every unmarked submission in one inbox, including late indicators.
- **Assignment management** — edit existing work or duplicate it into a clean
  draft without copying student submissions.
- **Reusable templates** — uniquely select, apply, and delete saved templates.
- **Marking filters** — narrow the inbox by class or late status and open the
  exact student selected from the queue.
- **Student snapshots** — review submission totals, average marks, overdue work,
  recommendations, and the weakest recorded curriculum topics for each learner.
- **Insights** — evidence-based prompts about overdue work, low recent marks, and
  possible shared mastery gaps.

Insights are suggestions for professional review. They do not label students or
make automatic educational decisions.

Teachers can archive their own classes without deleting records and restore
them later. Restored classes keep their old assignments archived until a teacher
chooses to republish them.

## Safety, privacy and accessibility

Students and staff can open **Safety & Settings** to:

- reduce motion;
- use high contrast;
- change interface scaling;
- enable focus mode;
- record additional working-time needs;
- submit a safeguarding or content concern;
- request a data copy, correction, or deletion review.

Only administrator accounts can read or resolve safeguarding and privacy
requests. EduPy does not add unrestricted private messaging or public student
profiles.

## Progress and rewards

The Progress page now shows level progress, curriculum-topic confidence, recent
practice, and a clear next route into Maths or English. Rewards contain no money
or payment flow. The daily streak bonus unlocks only after a real learning
activity, and ordinary activity rewards remain capped to discourage grinding.

Mini-games are short optional brain breaks. Quick Maths respects the learner's
additional-time preference, Word Scramble uses year-group vocabulary, and game
rewards cannot be repeatedly claimed from one completed round.

## Starting EduPy

Double-click **Start EduPy.bat**. The launcher configures the local Tkinter
runtime before opening the application.

## Verification

Run all automated checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

To render the main screens as a local smoke check without signing in or
publishing anything:

```powershell
.\.venv\Scripts\python.exe smoke_ui.py
```
