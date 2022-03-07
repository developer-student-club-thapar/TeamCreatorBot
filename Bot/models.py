import os
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.sqltypes import Boolean
from database import Base
from sqlalchemy.orm import relationship


class Team(Base):
    __tablename__ = "team"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    member = relationship("Member")
    def __init__(self, name):
        self.name = name

class Member(Base):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    # relationship with team table
    team_id = Column(Integer, ForeignKey('team.id'))
    
    def __init__(self, user_id, team_id):
        self.user_id = user_id
        self.team_id = team_id