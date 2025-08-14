from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
from dotenv import load_dotenv
import os



load_dotenv()


db_engine =  create_engine(os.getenv("DATABASE_URL"))

SessionLocal =  sessionmaker(bind=db_engine,autoflush=False,autocommit = False)

Base  = declarative_base()



def get_db():
    db =  SessionLocal()
    try:
        yield db
    finally:
        db.close()
