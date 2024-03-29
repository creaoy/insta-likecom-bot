from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from modules.variables import *
import datetime

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

engine = None 

try:
    # Create the SQLAlchemy engine using the loaded credentials
    engine = create_engine(DB_URL)

    # Use the engine to establish a connection and perform database operations
    # Add your database operations here
except SQLAlchemyError as e:
    # Handle any SQLAlchemy errors that occur during the connection
    print(f"An error occurred: {e}")


Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)  # Specify the length (e.g., 255)
    private = Column(Boolean, default=False) #default
    stage = Column(Integer)
    thread_id = Column(String(255), default=False, unique=True)  # OpenAI assistant thread id
    last_contacted = Column(DateTime)
    parent_id = Column(Integer, ForeignKey('accounts.id'))
    target = relationship("Account", remote_side=[id], backref="accounts")

#Story stats class, stores story text, datetime, comment, account_id, action (0 -like, 1 - comment) 
class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True)
    orig_text = Column(Text)  # text might be longer than 255
    datetime = Column(DateTime)
    comment = Column(Text, default=None)  # comment might be longer than 255
    account_id = Column(Integer, ForeignKey('accounts.id'))
    action = Column(Integer)
    #action: 0 - story like, 1 - story comment emoji, 2 - story comment, 3 - story comment with ask
    #action: 100 - post link, 101 - post comment



class DbHelpers:
    # Initialize the session as a class-level variable
    session = sessionmaker(bind=engine)()

    #mark account as private in database
    def mark_account_as_private(self, account_name: str):
        session = DbHelpers.session
        session.query(Account).filter(Account.name == account_name).update({Account.private: True})
        session.commit()
    # get or create account in database
    def get_or_create_account(self, name):
        session = DbHelpers.session
        account = session.query(Account).filter_by(name=name).first()
        if not account:
            account = Account(name=name, private=False, stage=0, last_contacted=datetime.datetime.now())
            session.add(account)
            session.commit()
        return account
    # update account
    def save_to_db(self, account):
        session = DbHelpers.session
        session.add(account)
        session.commit()
    #save story stats to database
    def save_story_stats(self, target_id, action, story_text, comment):
        session = DbHelpers.session
        story = History(orig_text=story_text, datetime=datetime.datetime.now(), comment=comment, account_id=target_id, action=action)
        session.add(story)
        session.commit()
    #get followers of account
    def get_followers(self, target_id):
        session = DbHelpers.session
        followers = session.query(Account).filter(Account.parent_id == target_id, Account.private == False).all()
        return followers
    #save targets to database
    def save_targets_to_db(self, target_list, target_id):
        session = DbHelpers.session
        for target in target_list:
            # Add a check to see if the target is already in the database
            if not session.query(Account).filter_by(name=target).first():
                account = Account(name=target, private=False, stage=0, last_contacted=datetime.datetime.now(), parent_id=target_id)
                session.add(account)
        session.commit()

