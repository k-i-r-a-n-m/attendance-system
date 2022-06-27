import sys

import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime
import psycopg2  # pip install psycopg2
import psycopg2.extras

from preAbs import findPresentAbsent


DB_HOST = "localhost"
DB_NAME = "demo"
DB_USER = "postgres"
DB_PASS = "123"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

path = 'static/uploads'
images=[]
classNames= []
myList = os.listdir(path)
period=[9,10,11,12,1]          #p1-9,p2-10,p3-11,p4-12,p5-1
now = datetime.now()
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
date = now.strftime("%d-%m-%Y")
print(myList)

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

print(classNames)


def findCurrentTime():
    return datetime.now()


def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList


# mark attendance

def markAttendance(roll,now):

        # check wheather the attendance already exist
        fetchRoll = f"SELECT * FROM attendance WHERE roll='{roll}' AND date='{date}'"
        updateAttSql=None
        cur.execute(fetchRoll)
        row = cur.fetchone()
        if row == None:
           insertSql= f"INSERT INTO attendance VALUES('{roll}','{date}')"
           cur.execute(insertSql)
           conn.commit()

        print(now)
        if now.hour==period[0] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p1='P' WHERE roll = '{roll}' AND date = '{date}'"

        elif now.hour==period[1] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p2='P' WHERE roll = '{roll}' AND date = '{date}'"

        elif now.hour==period[2] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p3='P' WHERE roll = '{roll}' AND date = '{date}'"

        elif now.hour==period[3] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p4='P' WHERE roll = '{roll}' AND date = '{date}'"

        elif now.hour==period[4] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p5='P' WHERE roll = '{roll}' AND date = '{date}'"

        if (now.hour == 1 and now.minute >= 30) or (now.hour == 2 and now.minute <= 30):
            findAbsent = f"COPY (SELECT roll FROM students EXCEPT SELECT roll FROM attendance WHERE date='{date}' ORDER by roll) "
            cur.execute(findAbsent)
            for row in cur.fetchall():
                insertSql = f"INSERT INTO attendance VALUES('{row[0]}','{date}')"
                cur.execute(insertSql)
                conn.commit()

        if updateAttSql!=None:
            cur.execute(updateAttSql)
            conn.commit()

        # if now.hour==12 and now.minute>=30:
        #     findPresentAbsent(cur,date)



# markAttendance('Elon')



encodeListKnown = findEncodings(images)
print('Encoding Complete')

# find match between our encodings
# images will be coming from web camera

cap =  cv2.VideoCapture(0)

while True:
    # get images frame by frame
    #  reduce the images size for speeding up the process
    now=findCurrentTime()
    if (now.hour==1 and now.minute>=30) or (now.hour==2 and now.minute<=30):
        findAbsent = f"SELECT roll FROM students EXCEPT SELECT roll FROM attendance WHERE date='{date}' ORDER by roll"
        cur.execute(findAbsent)
        for row in cur.fetchall():
            insertSql = f"INSERT INTO attendance VALUES('{row[0]}','{date}')"
            cur.execute(insertSql)
            conn.commit()

        findPresentAbsent(cur, date)
        import wtsAuto
        sys.exit()
    else:
        success, img = cap.read()
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

        for encodeFace, faceLoc in zip(encodeCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            print(faceDis)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classNames[matchIndex].upper()
                print(name)
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

                markAttendance(name,findCurrentTime())

        cv2.imshow('Webcam',img)
        cv2.waitKey(1)