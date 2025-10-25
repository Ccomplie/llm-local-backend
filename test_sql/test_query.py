from test_sql.test_sqlite import TestDatabaseCreator

if __name__ == "__main__":

    db_creator = TestDatabaseCreator("test_sql/test_database.db")
    
    db_creator.cursor.execute()
    