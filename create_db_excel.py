import psycopg2
from psycopg2 import sql

import sqlalchemy
import pandas as pd
import sys
import pathlib

db_name = 'database_new'
db_user = 'postgres'
db_password = 'secret'
db_host = 'localhost'
db_port = '5432'

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} [file.xlsx]...")
    sys.exit()

for arg in sys.argv[1:]:
    if pathlib.Path(arg).suffix != '.xlsx':
        print("Wrong file extension. Expected .xlsx")
        sys.exit()

files = sys.argv[1:]

try:
    # connect to default database
    connection = psycopg2.connect(database="postgres", user="postgres", password="secret")
    connection.autocommit = True

    cursor = connection.cursor()

    # drop database if exists
    try:
        cursor.execute(sql.SQL('DROP DATABASE {};').format(sql.Identifier(db_name)))
    except psycopg2.Error as e:
        print(f'Failed to drop database: {e}')

    # create database with users and product tables
    cursor.execute(sql.SQL('CREATE DATABASE {};').format(sql.Identifier(db_name)))

    # close main postgres database connection
    cursor.close
    connection.close()
except psycopg2.Error as e:
    print(e)

# connect to new database
engine = sqlalchemy.create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')

# read excel files and convert them to sql
for file in files:
    excel: pathlib.Path = pathlib.Path(file)

    wb = pd.read_excel(excel)

    try:
        wb.to_sql(excel.stem, engine, index = False)
    except ValueError as e:
        print(e)
