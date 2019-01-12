from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Shop, Base, CategoryItem, User

engine = create_engine('sqlite:///shop.db')
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

# Create dummy user
User1 = User(name="Muteb", email="muteb.faleh@gmail.com", picture='https://wmpics.pics/di-L2Z5.png')
session.add(User1)
session.commit()


# items for Men's Fashion
shop1 = Shop(user_id=1, name="Men's Fashion")

session.add(shop1)
session.commit()

category_item1 = CategoryItem(user_id=1, name="Shirt", description="A cloth garment for the upper body.",
                     price="$20", item="Clothing", shop=shop1)

session.add(category_item1)
session.commit()


category_item2 = CategoryItem(user_id=1, name="Oxfords", description="an item of footwear intended to protect and comfort the foot.",
                     price="$160", item="Shoes", shop=shop1)

session.add(category_item2)
session.commit()

category_item3 = CategoryItem(user_id=1, name="Sunglasse", description="A glasses to protect the eyes from the sun.",
                     price="$50", item="Accessories", shop=shop1)

session.add(category_item3)
session.commit()


# items for Women's Fashion
shop2 = Shop(user_id=1, name="Women's Fashion")

session.add(shop2)
session.commit()

category_item1 = CategoryItem(user_id=1, name="Dresses", description="a piece of clothing for women or girls.",
                     price="$35", item="Clothing", shop=shop2)

session.add(category_item1)
session.commit()


category_item2 = CategoryItem(user_id=1, name="Pumps", description="Women's Low Heel shoes.",
                     price="$32", item="Shoes", shop=shop2)

session.add(category_item2)
session.commit()

category_item3 = CategoryItem(user_id=1, name="Handbag", description="Felt Purse Handbag.",
                     price="$21", item="Accessories", shop=shop2)

session.add(category_item3)
session.commit()


print ("added items!")
