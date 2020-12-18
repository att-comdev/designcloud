import sqlite3
#conn = sqlite3.connect('resource.db')
conn = sqlite3.connect('credentials.db')
c = conn.cursor()
#for name in li:
#    c.execute("INSERT INTO resources  VALUES ('{0}','1800','375','8000')".format(name))
#conn.commit()
#for row in  c.execute('SELECT * FROM users'):
#    print(row)   
#conn.close()

#c.execute("SELECT * FROM users where username = 'admin'")
#user = c.fetchone()

#if user:
#  print(user)

for row in  c.execute('SELECT * FROM users'):
    print(row)   
conn.close()
