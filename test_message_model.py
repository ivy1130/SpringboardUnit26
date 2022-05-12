"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from uuid import uuid1
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User.signup(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD",
            image_url=None
        )

        db.session.commit()

        self.u1 = u1
        self.uid1 = u1.id

        msg = Message(
            text="Test Message",
            user_id=self.uid1
        )

        db.session.add(msg)
        db.session.commit()

        self.msg = msg
        self.msgid = msg.id

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown() #note to self: will need to look into what super().tearDown() means
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic model work?"""

        m = self.msg

        # User should have no messages & no followers
        self.assertEqual(m.text, "Test Message")
        self.assertEqual(m.user, self.u1)

    def test_message_text_limit(self):
        m = Message(
            text="Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec qu",
            user_id=self.uid1
        )

        db.session.add(m)
        with self.assertRaises(exc.DataError) as context:
         db.session.commit()


    def test_message_invalid_user(self):
        m = Message(
            text="Test Message",
            user_id=len(User.query.all())+1
        )

        db.session.add(m)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_message_user_relationship(self):
        """Does the repr method work as expected?"""

        self.assertEqual(self.u1.messages[0], self.msg)