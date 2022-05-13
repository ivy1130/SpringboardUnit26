"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="testuser1",
                                    image_url=None)
        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)

        db.session.commit()

        self.testuser1.following.append(self.testuser2)
        db.session.commit()

        self.uid1 = self.testuser1.id
        self.uid2 = self.testuser2.id

        self.testmsg = Message(text="Test message",
                                user_id=self.testuser1.id
        )

        db.session.add(self.testmsg)
        db.session.commit()

    def tearDown(self):
        res = super().tearDown() #note to self: will need to look into what super().tearDown() means
        db.session.rollback()
        return res
    
    def test_home_page_anon(self):
        with self.client as c:
            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Sign up now to get your own personalized timeline!", html)

    def test_home_page_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid1

            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test message", html)
    
    def test_user_following_anon(self):
        with self.client as c:
            resp = c.get(f'/users/{self.uid1}/following')

            self.assertEqual(resp.status_code, 302)

            resp_redirect = c.get(f'/users/{self.uid1}/following', follow_redirects=True)
            html = resp_redirect.get_data(as_text=True)

            self.assertEqual(resp_redirect.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_user_following_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid1

            resp = c.get(f'/users/{self.uid1}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser2", html)
    
    def test_user_followers_anon(self):
        with self.client as c:
            resp = c.get(f'/users/{self.uid1}/followers')

            self.assertEqual(resp.status_code, 302)

            resp_redirect = c.get(f'/users/{self.uid1}/followers', follow_redirects=True)
            html = resp_redirect.get_data(as_text=True)

            self.assertEqual(resp_redirect.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_user_followers_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid1
                
            resp = c.get(f'/users/{self.uid2}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1", html)