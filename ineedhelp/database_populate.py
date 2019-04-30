from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from dbSetUp import Base, User, MenuCategory, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Menu for UrbanBurger
category1 = MenuCategory(name="Tacos")

session.add(category1)
session.commit()

category2 = MenuCategory(name="Burritos")

session.add(category2)
session.commit()


category3 = MenuCategory(name="Tortas")

session.add(category3)
session.commit()


category4 = MenuCategory(name="Quesadillas")

session.add(category4)
session.commit()


category5 = MenuCategory(name="Huaraches")

session.add(category5)
session.commit()


category6 = MenuCategory(name="Sides")

session.add(category6)
session.commit()


category7 = MenuCategory(name="Beverages")

session.add(category7)
session.commit()





print "added menu items!"
