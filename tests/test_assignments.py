import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

import assignments
import classes
import save_system


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.data = save_system.ensure_data_schema({"users": {}})
        self.data["users"]["teacher"] = save_system.default_user("secret1", "teacher")
        self.data["users"]["student"] = save_system.default_user("secret2", "student")
        with patch("save_system.save_save", lambda data: None):
            classes.create_class(self.data,"maths-10","Maths 10",["teacher"],["student"],"Maths",10,actor="teacher")

    @patch("save_system.save_save", lambda data: None)
    def test_scheduling_late_rules_extensions_and_reports(self):
        tomorrow=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
        future_due=(datetime.date.today()+datetime.timedelta(days=3)).isoformat()
        yesterday=(datetime.date.today()-datetime.timedelta(days=1)).isoformat()
        aid=assignments.create_assignment(self.data,"Scheduled","maths-10",created_by="teacher",status="scheduled",publish_at=tomorrow,due_date=future_due,allow_late=False,resubmissions_allowed=False,rubric=[{"name":"Method","marks":5}],max_marks=5)
        item=self.data["assignments"][aid]
        self.assertFalse(assignments.assignment_is_available(item))
        item["publish_at"]=yesterday; item["due_date"]=yesterday
        self.assertTrue(assignments.assignment_is_available(item))
        self.assertFalse(assignments.submit_assignment(self.data,aid,"student","answer"))
        extension=(datetime.date.today()+datetime.timedelta(days=3)).isoformat()
        self.assertTrue(assignments.set_extension(self.data,aid,"student",extension,"teacher"))
        self.assertTrue(assignments.submit_assignment(self.data,aid,"student","answer"))
        self.assertFalse(assignments.submit_assignment(self.data,aid,"student","second"))
        self.assertTrue(assignments.add_private_comment(self.data,aid,"student","Internal note","teacher"))
        with tempfile.TemporaryDirectory() as folder:
            path=os.path.join(folder,"report.csv")
            self.assertTrue(assignments.export_assignment_report(self.data,aid,path))
            self.assertTrue(os.path.exists(path))

    @patch("save_system.save_save", lambda data: None)
    def test_invalid_schedule_and_rubric_are_rejected(self):
        tomorrow=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
        self.assertIsNone(assignments.create_assignment(self.data,"Bad schedule","maths-10",created_by="teacher",status="scheduled"))
        self.assertIsNone(assignments.create_assignment(self.data,"Bad order","maths-10",created_by="teacher",status="scheduled",publish_at=tomorrow,due_date=datetime.date.today().isoformat()))
        self.assertIsNone(assignments.create_assignment(self.data,"Bad rubric","maths-10",created_by="teacher",max_marks=10,rubric=[{"name":"Method","marks":4}]))

    @patch("save_system.save_save", lambda data: None)
    def test_templates_and_bulk_marking(self):
        template_id=assignments.save_template(self.data,"Weekly quiz",{"title":"Quiz","max_marks":10},"teacher")
        self.assertTrue(template_id); self.assertEqual(len(assignments.templates_for(self.data,"teacher")),1)
        aid=assignments.create_assignment(self.data,"Quiz","maths-10",created_by="teacher",status="published",max_marks=10)
        assignments.submit_assignment(self.data,aid,"student","work")
        count=assignments.bulk_mark(self.data,aid,{"student":8},"Good","teacher")
        self.assertEqual(count,1); self.assertEqual(self.data["assignments"][aid]["submissions"]["student"]["grade"],8)
        self.assertFalse(assignments.delete_template(self.data,template_id,"student"))
        self.assertTrue(assignments.delete_template(self.data,template_id,"teacher"))
        self.assertEqual(assignments.templates_for(self.data,"teacher"),[])

    @patch("save_system.save_save", lambda data: None)
    def test_marking_inbox_tracks_only_unmarked_submissions(self):
        aid=assignments.create_assignment(self.data,"Inbox task","maths-10",created_by="teacher",status="published",max_marks=10)
        self.assertTrue(assignments.submit_assignment(self.data,aid,"student","my work"))
        queue=assignments.awaiting_marking(self.data,"teacher","teacher")
        self.assertEqual(len(queue),1); self.assertEqual(queue[0]["student"],"student")
        self.assertTrue(assignments.grade_submission(self.data,aid,"student",7,"Good","teacher"))
        self.assertEqual(assignments.awaiting_marking(self.data,"teacher","teacher"),[])

    @patch("save_system.save_save", lambda data: None)
    def test_assignment_can_be_edited_and_duplicated_without_student_work(self):
        aid=assignments.create_assignment(self.data,"Original","maths-10",created_by="teacher",status="published",max_marks=10)
        self.assertTrue(assignments.submit_assignment(self.data,aid,"student","work"))
        tomorrow=(datetime.date.today()+datetime.timedelta(days=1)).isoformat()
        self.assertTrue(assignments.update_assignment_details(self.data,aid,"teacher",title="Improved",due_date=tomorrow,max_marks=20,reward_tokens=99))
        self.assertEqual(self.data["assignments"][aid]["title"],"Improved")
        self.assertEqual(self.data["assignments"][aid]["reward_tokens"],15)
        copied=assignments.duplicate_assignment(self.data,aid,"teacher")
        self.assertIsNotNone(copied)
        self.assertEqual(self.data["assignments"][copied]["status"],"draft")
        self.assertEqual(self.data["assignments"][copied]["submissions"],{})
        self.assertFalse(assignments.update_assignment_details(self.data,aid,"student",title="Not allowed"))
        self.assertTrue(assignments.grade_submission(self.data,aid,"student",18,"Strong","teacher"))
        self.assertFalse(assignments.update_assignment_details(self.data,aid,"teacher",max_marks=10))

    @patch("save_system.save_save", lambda data: None)
    def test_marking_inbox_filters_late_work_and_class(self):
        aid=assignments.create_assignment(self.data,"Late task","maths-10",created_by="teacher",status="published")
        self.assertTrue(assignments.submit_assignment(self.data,aid,"student","work"))
        self.data["assignments"][aid]["submissions"]["student"]["late"]=True
        self.assertEqual(len(assignments.awaiting_marking(self.data,"teacher",late_only=True)),1)
        self.assertEqual(assignments.awaiting_marking(self.data,"teacher",class_id="another-class"),[])

    def test_deadline_labels_include_extensions_and_urgency(self):
        today=datetime.date(2026,7,14)
        item={"due_date":"2026-07-20","extensions":{"student":"2026-07-15"}}
        self.assertEqual(assignments.deadline_label(item,"student",today),"Due tomorrow")
        self.assertEqual(assignments.deadline_label(item,"other",today),"Due in 6 days")
        self.assertEqual(assignments.deadline_label({"due_date":"2026-07-12"},"student",today),"Overdue by 2 days")


if __name__ == "__main__":
    unittest.main()
