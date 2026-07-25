import os
import tempfile
import unittest
import csv
from unittest.mock import patch

import classes
import save_system
from database import AccountDatabase


class ClassPermissionTests(unittest.TestCase):
    def setUp(self):
        self.data=save_system.ensure_data_schema({"users":{}})
        self.data["users"]["teacher"]=save_system.default_user("secret1","teacher")
        self.data["users"]["other"]=save_system.default_user("secret2","teacher")
        self.data["users"]["student"]=save_system.default_user("secret3","student")

    @patch("save_system.save_save",lambda data:None)
    def test_roles_ownership_and_join_codes(self):
        self.assertTrue(classes.create_class(self.data,"english-8","English 8",["teacher"],subject="English",year_group=8,actor="teacher"))
        cls=classes.get_class(self.data,"english-8")
        self.assertFalse(classes.add_student_to_class(self.data,cls["id"],"teacher"))
        self.assertFalse(classes.add_student_to_class(self.data,cls["id"],"student"))
        self.assertIsNotNone(classes.join_class(self.data,"student",cls["join_code"]))
        self.assertEqual(len(classes.get_classes(self.data,"teacher","teacher")),1)
        self.assertEqual(classes.get_classes(self.data,"other","teacher"),[])
        self.assertFalse(classes.remove_teacher_from_class(self.data,cls["id"],"teacher"))
        self.assertFalse(classes.create_class(self.data,"no-actor","No Actor",["teacher"]))

    @patch("save_system.save_save",lambda data:None)
    def test_managed_account_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            database=AccountDatabase(os.path.join(folder,"accounts.db"));database.create_tables()
            self.assertTrue(classes.create_school_account(self.data,"new_student","SecurePass1","student",9,database))
            self.assertFalse(classes.create_school_account(self.data,"new_student","SecurePass1","student",9,database))
            self.assertFalse(classes.create_school_account(self.data,"short","123","student",9,database))
            self.assertEqual(self.data["users"]["new_student"]["selected_year"],9)
            database.engine.dispose()

    def test_profile_only_account_creation_is_disabled(self):
        self.assertFalse(classes.create_school_account(self.data,"unsafe_user","SecurePass1","student",9))
        self.assertNotIn("unsafe_user",self.data["users"])

    def test_class_ids_are_generated_and_kept_unique(self):
        self.assertEqual(classes.generate_class_id(self.data,"English 8A"),"english-8a")
        self.assertTrue(classes.create_class(self.data,"english-8a","English 8A",["teacher"],actor="teacher"))
        self.assertEqual(classes.generate_class_id(self.data,"English 8A"),"english-8a-2")

    @patch("save_system.save_save",lambda data:None)
    def test_roster_import_creates_secure_accounts_and_reports_counts(self):
        self.assertTrue(classes.create_class(self.data,"roster","Roster",["teacher"],actor="teacher"))
        with tempfile.TemporaryDirectory() as folder:
            database=AccountDatabase(os.path.join(folder,"accounts.db"));database.create_tables()
            path=os.path.join(folder,"students.csv")
            with open(path,"w",newline="",encoding="utf-8") as file:
                writer=csv.writer(file);writer.writerow(["username","password","year_group"]);writer.writerow(["new_learner","SecurePass1","9"])
            created,added=classes.import_roster_from_csv(self.data,"roster",path,database,"teacher")
            self.assertEqual((created,added),(1,1))
            self.assertIsNotNone(database.get_account("new_learner"))
            self.assertIn("new_learner",classes.get_class(self.data,"roster")["student_usernames"])
            database.engine.dispose()

    @patch("save_system.save_save",lambda data:None)
    def test_student_cannot_manage_teacher_roster(self):
        self.assertTrue(classes.create_class(self.data,"secure-class","Secure Class",["teacher"],actor="teacher"))
        self.assertFalse(classes.add_teacher_to_class(self.data,"secure-class","other",actor="student"))
        self.assertTrue(classes.add_teacher_to_class(self.data,"secure-class","other",actor="teacher"))

    @patch("save_system.save_save",lambda data:None)
    def test_archiving_preserves_class_relationships(self):
        self.assertTrue(classes.create_class(self.data,"history","History",["teacher"],actor="teacher"))
        self.assertTrue(classes.delete_class(self.data,"history",actor="teacher"))
        self.assertTrue(classes.get_class(self.data,"history")["archived"])
        self.assertIsNone(next((item for item in classes.get_classes(self.data) if item["id"]=="history"),None))
        self.assertFalse(classes.restore_class(self.data,"history",actor="student"))
        self.assertTrue(classes.restore_class(self.data,"history",actor="teacher"))
        self.assertFalse(classes.get_class(self.data,"history")["archived"])


if __name__=="__main__":
    unittest.main()
