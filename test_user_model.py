"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
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

class UserModelTestCase(TestCase):
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

        u2 = User.signup(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD",
            image_url=None
        )

        db.session.commit()

        self.u1 = u1
        self.uid1 = u1.id

        self.u2 = u2
        self.uid2 = u2.id

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown() #note to self: will need to look into what super().tearDown() means
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = self.u1
        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(u.username, 'testuser1')
        self.assertEqual(u.email, 'test1@test.com')
    
    def test_user_model_repr(self):
        """Does the repr method work as expected?"""

        u = self.u1

        self.assertEqual(str(u), f"<User #{self.uid1}: testuser1, test1@test.com>")

    def test_user_model_following(self):

        u1 = self.u1
        u2 = self.u2

        u1.following.append(u2)
        db.session.commit()

        self.assertEqual(u1.is_following(u2), True)
        self.assertEqual(u1.is_followed_by(u2), False)
        self.assertEqual(u2.is_following(u1), False)
        self.assertEqual(u2.is_followed_by(u1), True)
    
    def test_user_model_sign_up_success(self):
        u = User.signup(
            username="testuser",
            password="HASHED_PASSWORD",
            email="test@test.com",
            image_url=None
        )
        db.session.commit()

        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(u.image_url, "/static/images/default-pic.png")
        self.assertTrue(u.password.startswith("$2b$"))
    
    def test_user_model_sign_up_username_fail(self):
        u = User.signup(
            username=None,
            password="HASHED_PASSWORD",
            email="test@test.com",
            image_url=None
        )
       
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_user_model_sign_up_password_fail(self):
        with self.assertRaises(ValueError) as context:
            u = User.signup(
                username="testuser",
                password=None,
                email="test@test.com",
                image_url=None
            )
    
    def test_valid_authentication(self):
        u = User.authenticate("testuser1", "HASHED_PASSWORD")
        self.assertIsNotNone(u)
        self.assertEqual(u, self.u1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("invalidusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate("testuser1", "invalidpassword"))


