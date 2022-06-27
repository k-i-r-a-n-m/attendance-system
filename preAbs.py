# import psycopg2.extras
# from datetime import datetime
# DB_HOST = "localhost"
# DB_NAME = "demo"
# DB_USER = "postgres"
# DB_PASS = "123"
#
# conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
# cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#
# now = datetime.now()
# date = now.strftime("%d-%m-%Y")

def findPresentAbsent(cur,date):
    attendance = f"COPY (SELECT roll,p1,p2,p3,p4,p5 from attendance Where date='{date}' order by roll) TO STDOUT WITH CSV "
    # findAbsent = f"COPY (SELECT roll FROM students EXCEPT SELECT roll FROM attendance WHERE date='{date}' ORDER by roll) TO STDOUT WITH CSV "
    # Set up a variable to store our file path and name.

    with open(f'attendance-{date}.csv', 'w') as f_output:
        cur.copy_expert(attendance, f_output)

    print("file ready------------------")
    # with open('absent.csv','w') as f_output:
    #     cur.copy_expert(findAbsent,f_output)

# findPresentAbsent(cur,date)

# 'SELECT roll FROM students EXCEPT SELECT roll FROM attendance WHERE date='08-06-2022' ORDER by roll '