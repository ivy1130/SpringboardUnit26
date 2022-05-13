"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

        self.uid1 = self.testuser1.id
        self.uid2 = self.testuser2.id

        self.testmsg = Message(text="Test message",
                                user_id=self.testuser1.id
        )

        db.session.add(self.testmsg)
        db.session.commit()

        self.msgid = self.testmsg.id

    def tearDown(self):
        res = super().tearDown() #note to self: will need to look into what super().tearDown() means
        db.session.rollback()
        return res

    def test_add_message_user(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid1

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.get(2)
            self.assertEqual(msg.text, "Hello")

            resp_redirect = c.post("/messages/new", data={"text": "Hello2"}, follow_redirects=True)
            html = resp_redirect.get_data(as_text=True)

            self.assertEqual(resp_redirect.status_code, 200)
            self.assertIn("Hello", html)
            self.assertIn("Hello2", html)

    def test_add_message_anon(self):
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            resp_redirect = c.post(f'/messages/new', follow_redirects=True)
            html = resp_redirect.get_data(as_text=True)

            self.assertEqual(resp_redirect.status_code, 200)
            self.assertIn("Access unauthorized.", html)

    def test_delete_message_user(self):
         with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid1

            resp = c.post(f"/messages/{self.msgid}/delete")

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.get(2)
            self.assertIsNone(msg)
            
    def test_delete_message_anon(self):
        with self.client as c:
            resp_redirect = c.post(f"/messages/{self.msgid}/delete", follow_redirects=True)
            html = resp_redirect.get_data(as_text=True)

            self.assertEqual(resp_redirect.status_code, 200)
            self.assertIn("Access unauthorized.", html)
    
    def test_delete_message_alt_user(self):
         with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.uid2

            resp_redirect = c.post(f"/messages/{self.msgid}/delete", follow_redirects=True)
            html = resp_redirect.get_data(as_text=True)

            self.assertEqual(resp_redirect.status_code, 200)
            self.assertIn("Access unauthorized.", html)