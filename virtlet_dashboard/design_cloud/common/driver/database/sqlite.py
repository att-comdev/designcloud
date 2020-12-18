import sqlite3, hashlib

class Sqlite(object):

    def __init__(self, **kwargs):
        db_file = kwargs['db_file']
        self.conn = None
        self.cursor = None
        self.getConnection(db_file)
    
    def getConnection(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def create_user(self, **kwargs):
        username = kwargs['username']
        password = hashlib.md5(username.encode('utf-8')).hexdigest()
        usertype = 'user'
        query = "INSERT INTO users  VALUES ('{0}', '{1}', '{2}')".format(username, password, usertype)
        self.cursor.execute(query)
        self.conn.commit()

        return username

    def get_user(self, **kwargs):
        username = kwargs['username']
        query = "SELECT * FROM users where username='{0}'".format(username)
        res = self.cursor.execute(query)
        user = res.fetchone()
        if user:
            return user
        else:
            return None

    def get_resource(self, username):
        query = "SELECT * FROM resources where username='{0}'".format(username)
        res = self.cursor.execute(query)
        resource = res.fetchone()
        if resource:
            return resource
        else:
            return None
    
    def update_resource(self,username,ram,vcpu,disk,operation):
        resource = self.get_resource(username)

        if operation == "add":
            ram = str(int(ram) + int(resource[1]))
            vcpu = str(int(vcpu) + int(resource[2]))
            disk = str(int(disk) + int(resource[3]))
        else:
            ram = str(int(resource[1]) - int(ram))
            vcpu = str(int(resource[2]) - int(vcpu))
            disk = str(int(resource[3]) - int(disk))

        query = "UPDATE resources SET ram='{0}', vcpu='{1}', disk ='{2}' WHERE username='{3}'".format(ram,vcpu, disk, username)
        res = self.cursor.execute(query)
        self.conn.commit()

    def add_user_to_resource_table(self, username):
        ram = '0'
        vcpu = '0'
        disk = '0'
        query = "INSERT INTO resources  VALUES ('{0}', '{1}', '{2}', '{3}')".format(username, ram, vcpu, disk)
        self.cursor.execute(query)
        self.conn.commit()

