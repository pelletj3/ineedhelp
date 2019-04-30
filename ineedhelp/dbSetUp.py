'''
CONFIGURATION CODE - import necessary modules and creates instance of declarative base.
'''
import sys
# provides necessary functions and modules to manipulate python environment
from sqlalchemy import Column, ForeignKey, Integer, String
# helpful when running mapper code
from sqlalchemy import create_engine
# for configuration code at end of ORM file
from sqlalchemy.ext.declarative import declarative_base
# for configuration and class code
from sqlalchemy.orm import relationship
# create foreign key relations used in mapper

Base = declarative_base()
# make instance of declarative base class, which lets SQLalchemy know that classes are SQLalchemy classes, which in turn
# correspond to tables in database

'''
CLASS CODE - extends base class and will provide foundation for table and mapper code
'''
class User(Base):
# represent User table as a python class
    '''
    TABLE REPRESENTATION __tablename__ = 'some_table'
    '''
    __tablename__ = 'user'
    '''
    MAPPER CODE - maps python objects to columns in our database
    '''
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), index=False)
    picture = Column(String(250))

class MenuCategory(Base):
# represent Menu Category table as a python class
    '''
    TABLE REPRESENTATION __tablename__ = 'some_table'
    '''
    __tablename__ = 'category'
    '''
    MAPPER CODE - maps python objects to columns in our database
    '''
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class MenuItem(Base):
# represent Menu Items table as a python class
    '''
    TABLE REPRESENTATION __tablename__ = 'some_table'
    '''
    __tablename__ = 'menu'
    '''
    MAPPER CODE - maps python objects to columns in our database
    '''
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    price = Column(String(8))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(MenuCategory)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
        }



'''
CONFIGURATION CODE - creates and connects to database and adds tables and columns
'''
engine = create_engine('sqlite:///restaurantmenu.db')
# create instance of engine and point to db that we will use. this will create a new file that will act similar to psql
# database.
Base.metadata.create_all(engine)
# adds classes to database as new tables.
