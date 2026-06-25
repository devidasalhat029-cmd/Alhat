import sqlite3
from flask import Flask,render_template,request,flash

app=Flask(__name__)
app.secret_key="Linkkiwi2026"

def get_db():
   """database connection"""

   conn =sqlite3.connect('my_project.db')
   cursor=conn.cursor()
   conn.row_factory=sqlite3.Row 
   return conn
def init_db():
#creating a table using database
   conn=get_db()
   cursor=conn.cursor()
   conn.execute
   ('''
        CREATE TABLE IF NOT EXISTS farmers
            (
                farmer_id INTEGER  PRAMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mobile TEXT,
                village TEXT,
                email TEXT
            ) ''' 
   )
   conn.Commit()
   conn.Close()    

   if __name__== "__main__":
      init_db()    #initlise the database
      app.run(deug=True)
 