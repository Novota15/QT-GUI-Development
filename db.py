# database functions
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime
from sqlalchemy import Index
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy import create_engine, select

Base = declarative_base()

# Tables
class Temperature(Base):
    __tablename__ = 'temperature'
    id = Column(Integer, primary_key = True, autoincrement=True)
    value = Column(Float)
    time = Column(DateTime)

class Humidity(Base):
    __tablename__ = 'humidity'
    id = Column(Integer, primary_key = True, autoincrement=True)
    value = Column(Float)
    time = Column(DateTime)

# general db functions
def create(database):
    # an engine that the session will use for resources
    engine = create_engine(database)
    # create a configured session class
    Session = sessionmaker(bind=engine)
    # create a session
    session = Session()
    return engine, session

def result_dict(r):
    return dict(zip(r.keys(), r))

def result_dicts(rs):
    return list(map(result_dict, rs))

def database_dump(session):
    Database = [Temperature, Humidity]
    for table in Database:
        stmt = select('*').select_from(table)
        result = session.execute(stmt).fetchall()
        print(result_dicts(result))
    return

def create_tables(engine):
    Base.metadata.create_all(engine)
    return

def init_session():
    engine, session = create("sqlite:///db.sqlite3")
    create_tables(engine)
    return session

def close(conn):
    conn.close()
    return

def delete_obj(session, obj):
    session.delete(obj)
    session.commit()
    return

# add rows to tables
def add_temp(session, value, time):
    temp = Temperature(value=value, time=time)
    session.add(temp)
    session.commit()
    return

def add_humidity(session, value, time):
    humidity = Humidity(value=value, time=time)
    session.add(humidity)
    session.commit()
    return

# check if element exists in db
def check_host(session, name):
    host = session.query(Host).filter_by(name=name).scalar()
    if host == None:
        return False
    return True