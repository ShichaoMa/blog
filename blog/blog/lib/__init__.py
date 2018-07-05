class Sqlite(object):

    def __init__(self, cur, conn):
        self.cur = cur
        self.conn = conn

    def __enter__(self):
        return self.cur

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        return exc_type is None
