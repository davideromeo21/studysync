import unittest
import os
import database
import matcher

class TestStudySync(unittest.TestCase):
    def setUp(self):
        # Set up an in-memory SQLite database for testing
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        database.engine = create_engine('sqlite:///:memory:', echo=False)
        database.SessionLocal = sessionmaker(bind=database.engine)
        database.init_db()

    def test_user_creation_and_auth(self):
        res = database.create_user("new_user", "password123")
        self.assertEqual(res, "ok")
        
        user = database.authenticate_user("new_user", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], "new_user")
        
        user_fail = database.authenticate_user("new_user", "wrongpassword")
        self.assertIsNone(user_fail)

    def test_profile_update(self):
        database.create_user("test_user", "password123")
        user = database.get_user_by_username("test_user")
        user_id = user['id']
        
        profile_data = {
            "name": "Test User",
            "course": "Computer Science",
            "degree_level": "Bachelor",
            "subjects": ["Math", "Physics"],
            "goals": ["Exam Prep"],
            "skill_levels": {"Math": 5, "Physics": 3},
            "study_styles": ["Discussion-based"]
        }
        res = database.update_user_profile(user_id, profile_data)
        self.assertTrue(res)
        
        updated = database.get_user_by_id(user_id)
        self.assertEqual(updated['name'], "Test User")
        self.assertEqual(updated['subjects'], ["Math", "Physics"])

    def test_matcher_logic(self):
        database.create_user("test_user", "password123")
        database.create_user("peer_user", "password123")
        
        user1 = database.get_user_by_username("test_user")
        peer = database.get_user_by_username("peer_user")
        
        user_profile = {
            "name": "Test User",
            "course": "Computer Science",
            "degree_level": "Bachelor",
            "subjects": ["Math", "Physics"],
            "goals": ["Exam Prep"],
            "skill_levels": {"Math": 5, "Physics": 3},
            "study_styles": ["Discussion-based"]
        }
        database.update_user_profile(user1['id'], user_profile)
        
        peer_profile = {
            "name": "Peer User",
            "course": "Computer Science",
            "degree_level": "Master",
            "subjects": ["Math", "Chemistry"],
            "goals": ["Exam Prep"],
            "skill_levels": {"Math": 2, "Chemistry": 4},
            "study_styles": ["Discussion-based"]
        }
        database.update_user_profile(peer['id'], peer_profile)
        
        database.set_user_availability(user1['id'], [("Monday", "Morning (8am-12pm)")])
        database.set_user_availability(peer['id'], [("Monday", "Morning (8am-12pm)")])
        
        # Need to fetch the updated user objects from DB, since subjects, goals etc are stored
        user1 = database.get_user_by_username("test_user")
        peer = database.get_user_by_username("peer_user")
        
        avail1 = set([("Monday", "Morning (8am-12pm)")])
        avail2 = set([("Monday", "Morning (8am-12pm)")])
        
        score, details, breakdown = matcher.MatcherService.calculate_compatibility(user1, peer, avail1, avail2)
        
        self.assertGreater(score, 0)
        self.assertIn("Subjects", breakdown)
        self.assertIn("Skill Match", breakdown)
        self.assertIn("Degree Level", breakdown)

        
if __name__ == '__main__':
    unittest.main()
