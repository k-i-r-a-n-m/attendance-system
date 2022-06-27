# app.py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import sys

import psycopg2.extras
import os
from werkzeug.utils import secure_filename


import numpy as np
import face_recognition

from datetime import datetime
import psycopg2  # pip install psycopg2

from wtsAuto import runMsg
from preAbs import findPresentAbsent
#Import necessary libraries
from flask import Flask, render_template, Response, redirect, url_for, flash,request
from flask_executor import Executor
import cv2

app = Flask(__name__)
executor = Executor(app)
app.secret_key = "cairocoders-ednalan"

DB_HOST = "localhost"
DB_NAME = "demo"
DB_USER = "postgres"
DB_PASS = "123"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

UPLOAD_FOLDER = 'static/uploads/'

app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

path = 'static/uploads'
images=[]
classNames= []
myList = os.listdir(path)
period=[9,10,11,12,1]          #p1-9,p2-10,p3-11,p4-12,p5-1
now = datetime.now()
date = now.strftime("%d-%m-%Y")
# print(myList)


studentDetail={
    "roll":"",
    "name":"",
    "dept":"",
    "time":"",
    "marked":False,
    "date":"",
    "period":""
}   #roll,sname,dept,contact,image,time,True

for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])

# print(classNames)


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

        print("@@@@@@@@@@@@ marking attendance @@@@@@@@@@@@@@@@@@@@")
        if now.hour==period[0] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p1='P' WHERE roll = '{roll}' AND date = '{date}'"
            studentDetail["period"]="1st"

        elif now.hour==period[1] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p2='P' WHERE roll = '{roll}' AND date = '{date}'"
            studentDetail["period"] = "2nd"

        elif now.hour==period[2] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p3='P' WHERE roll = '{roll}' AND date = '{date}'"
            studentDetail["period"] = "3rd"

        elif now.hour==period[3] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p4='P' WHERE roll = '{roll}' AND date = '{date}'"
            studentDetail["period"] = "4th"

        elif now.hour==period[4] and now.minute<=10:
            updateAttSql = f"UPDATE attendance SET p5='P' WHERE roll = '{roll}' AND date = '{date}'"
            studentDetail["period"] = "5th"

        # if (now.hour == 1 and now.minute >= 30) or (now.hour == 2 and now.minute <= 30):
        #     findAbsent = f"COPY (SELECT roll FROM students EXCEPT SELECT roll FROM attendance WHERE date='{date}' ORDER by roll) "
        #     cur.execute(findAbsent)
        #     for row in cur.fetchall():
        #         insertSql = f"INSERT INTO attendance VALUES('{row[0]}','{date}')"
        #         cur.execute(insertSql)
        #         conn.commit()

        if updateAttSql!=None:
            cur.execute(updateAttSql)
            conn.commit()

        # if now.hour==12 and now.minute>=30:
        #     findPresentAbsent(cur,date)



# markAttendance('Elon')



encodeListKnown = findEncodings(images)
# print('Encoding Complete')

# find match between our encodings
# images will be coming from web camera
cap = cv2.VideoCapture(0)
capFlag = False
# cap =  None
def generate():
    global  capFlag
    global cap
    if capFlag==False:
        cap=cv2.VideoCapture(0)

    while True:
        # get images frame by frame
        #  reduce the images size for speeding up the process
        now=findCurrentTime()
            # time = f"{now.hour-12}:{now.minute}"

        time = now.strftime("%I:%M:%S")
        date = now.strftime("%d-%m-%Y")
        print(now.hour,now.minute)
        if (now.hour==13 and now.minute>=30) or (now.hour==14 and now.minute<=30):
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
            capFlag=True
            try:
                imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
            except:
                break
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
                    cur.execute(f"SELECT * FROM students WHERE roll='{name}'")
                    val = cur.fetchone()
                    studentDetail["roll"]=val[0]
                    studentDetail["name"] = val[1]
                    studentDetail["dept"] = val[2]
                    studentDetail["time"] = time
                    studentDetail["marked"] = True
                    studentDetail["date"] = date

                    markAttendance(name,findCurrentTime())

        ret, buffer = cv2.imencode('.jpg', img)
        img = buffer.tobytes()
        yield (b'--frame\r\n' 
               b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')  # concat frame one by one and show result


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def Index():
    global capFlag
    if capFlag ==True:
        cap.release()
        capFlag=False
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM students order by roll ASC"
    cur.execute(s)  # Execute the SQL
    list_users = cur.fetchall()
    return render_template('index.html', list_users=list_users)





@app.route('/add_student', methods=['POST'])
def add_student():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
            roll = request.form['rollNo'].upper()
            sname = request.form['sname'].upper()
            dept = request.form['dept'].upper()
            contact = request.form['contact']
            file = request.files['file']

            # normalize the file name
            filename = roll+'.'+secure_filename(file.filename).split('.')[1]

            # check for validation
            cur.execute(f"SELECT * FROM students where roll='{roll}'")
            if cur.fetchone() != None:
                flash("Roll no already exist!")

            if filename.split(".")[1] not in ALLOWED_EXTENSIONS:
                    flash("Image formate allowed - png,jpg,jpeg")
            else:
                # Find encoding of the current image and find existance of that image
                img = cv2.imdecode(np.frombuffer(request.files['file'].read(), np.uint8), cv2.IMREAD_UNCHANGED)
                imgCvt = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                encode = face_recognition.face_encodings(imgCvt)[0]



                encodeListKnown = findEncodings(images)
                matches = face_recognition.compare_faces(encodeListKnown, encode)
                faceDis = face_recognition.face_distance(encodeListKnown, encode)
                matchIndex = np.argmin(faceDis)
                print("^^^^^^^^^^^^^^^^^^^^^^^^^^^ uploaded image checking for existance ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

                if matches[matchIndex]:
                    flash("Image already exist")
                else:
                        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                        cv2.imwrite(f"{path}/{filename}", img)
                        cur.execute("INSERT INTO students (roll, sname, dept,contact,image) VALUES (%s,%s,%s,%s,%s)",(roll, sname, dept, contact, filename))
                        conn.commit()
                        flash('Detils successfully uploaded!')


            return redirect(url_for('Index'))

    # return redirect(url_for('Index'))



# def upload_image():
    # try:
    #
    #     cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    #
    #     if 'file' not in request.files:
    #         flash('No file part')
    #         return redirect(request.url)
    #     file = request.files['file']
    #     if file.filename == '':
    #         flash('No image selected for uploading')
    #         return redirect(request.url)
    #     if file and allowed_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    #         # print('upload_image filename: ' + filename)
    #
    #         cursor.execute("INSERT INTO upload (title) VALUES (%s)", (filename,))
    #         conn.commit()
    #
    #         flash('Image successfully uploaded and displayed below')
    #         return render_template('student.html', filename=filename)
    #     else:
    #         flash('Allowed image types are - png, jpg, jpeg, gif')
    #         return redirect(request.url)
    # except Exception as e:
    #     flash("Roll.no already exist")
    #     return render_template('student.html', filename=filename)


@app.route('/edit/<roll>', methods=['POST', 'GET'])
def get_employee(roll):
    # print(type(roll))
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    sql = "SELECT * FROM students WHERE roll = '%s' "%roll
    # cur.execute('SELECT * FROM students WHERE roll = %s',(str(roll)))
    cur.execute(sql)

    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit.html', student=data[0])


@app.route('/update/<roll>', methods=['POST'])
def update_student(roll):
    if request.method == 'POST':
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        roll = request.form['rollNo'].upper()
        sname = request.form['sname'].upper()
        dept = request.form['dept'].upper()
        contact = request.form['contact']
        path = 'C:/Users/kiran/Desktop/clg-prj/crud-2/static/uploads/'
        file = request.files['file']
        # filename = secure_filename(file.filename)
        # normalize the file name
        filename = roll + '.' + secure_filename(file.filename).split('.')[1]

        cur.execute(f"SELECT image from students where roll='{roll}'")
        oldImage = cur.fetchone()[0]
        os.remove(path+oldImage)


        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            UPDATE students
            SET sname = %s,
                dept = %s,
                contact = %s,
                image = %s
            WHERE roll = %s
        """, (sname, dept, contact,filename,roll))
        flash('Student Updated Successfully')
        conn.commit()
        return redirect(url_for('Index'))


@app.route('/delete/<string:roll>', methods=['POST', 'GET'])
def delete_student(roll):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    path = 'C:/Users/kiran/Desktop/clg-prj/crud-2/static/uploads/'

    cur.execute(f"SELECT image from students where roll='{roll}'")
    oldImage = cur.fetchone()[0]
    os.remove(path + oldImage)


    cur.execute("DELETE FROM students WHERE roll = '{0}' ".format(roll))
    conn.commit()
    flash('Student Removed Successfully')
    return redirect(url_for('Index'))



@app.route('/student')
def student():
    global capFlag
    if capFlag ==True:
        cap.release()
        capFlag=False

    return render_template('student.html')


@app.route('/summary',methods=['POST','GET'])
def summary():
    if request.method == 'POST':
        roll = request.form['roll'].upper()


        cur.execute(f"SELECT COUNT(*) FROM students where roll='{roll}'")
        if cur.fetchone()[0] == 0:
            outputStr = "Invalid Roll no.!"
            return render_template('student.html',outputStr=outputStr)
        else:
            outputStr=""

            cur.execute(f"select count(distinct date) from attendance")
            totalWorkingDays = cur.fetchone()[0]

            cur.execute(f"select count(*) from attendance where roll='{roll}'  and(p1='P' or p2='P' or p3='P' or p4='P' or p5='P')")
            noOfdaysPresentAtleast1 = cur.fetchone()[0]

            present = noOfdaysPresentAtleast1
            absent = totalWorkingDays - present

            cur.execute(f"SELECT sname FROM students where roll='{roll}'")
            name = cur.fetchone()[0]

            cur.execute(f"SELECT image from students where roll='{roll}'")
            img = cur.fetchone()[0]
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], img)
            print(img)


            p = []
            X = ['1st', '2nd', '3rd', '4th', '5th']


            for i in range(5):
                cur.execute(f"select count(*)  from attendance where roll='{roll}' and p{i + 1}='P'")
                daysPresent = cur.fetchone()[0];
                p.append(daysPresent)

            fig = plt.figure()
            plt.bar(X, p, color='b')
            plt.xlabel("Period")
            plt.title(f"{roll}'s Present status")
            plt.ylabel("Days present per period")

            tmpfile = BytesIO()
            fig.savefig(tmpfile, format='png')
            encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')


        #line chart------------------------------------------------------------------------------------------------
            X = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
            Y = []

            for i in range(1, 13):
                if i <= 9:
                    cur.execute(
                        f"select count(*) from attendance where roll='{roll}' and date like '__-0{i}-____' and(p1='P' or p2='P' or p3='P' or p4='P' or p5='P')")
                if i >= 10:
                    cur.execute(
                        f"select count(*) from attendance where roll='{roll}' and date like '__-{i}-____' and(p1='P' or p2='P' or p3='P' or p4='P' or p5='P')")

                Y.append(cur.fetchone()[0])


            fig = plt.figure()
            plt.plot(X, Y, color='r')
            plt.xlabel("Months")
            plt.title(f"{roll}'s Attendance status")
            plt.ylabel("No.of days present(atleast 1 period)")

            tmpfile = BytesIO()
            fig.savefig(tmpfile, format='png')
            encoded2 = base64.b64encode(tmpfile.getvalue()).decode('utf-8')



    #         pie-chart------------------------------------------------------------------------------------------------------------>
            periodPresent=[]
            periodAbsent=[]
            periodChart=[]

            for i in range(1,6):
                cur.execute(f"select count(*) from attendance where roll='{roll}' and p{i}='P'")

                curPeriodPresent = cur.fetchone()[0]
                periodPresent.append(curPeriodPresent)
                periodAbsent.append(totalWorkingDays-curPeriodPresent)

                fig = plt.figure()
                plt.pie([periodPresent[i-1],periodAbsent[i-1]],labels=["Present","Absent"],colors=["#36AE7C","#FF1818"])
                plt.title(f"Period {i} percentage:{(curPeriodPresent/totalWorkingDays)*100:.2f}%")
                plt.legend()
                tmpfile = BytesIO()
                fig.savefig(tmpfile, format='png')
                periodChart.append(base64.b64encode(tmpfile.getvalue()).decode('utf-8'))

            print(periodPresent)
            print(periodAbsent)

    return render_template('summary.html',data=[encoded,encoded2,periodChart],outputStr=outputStr,roll=roll,img=full_filename,detail=[name,roll,present,absent])



@app.route('/video')
def video():
    now = findCurrentTime()
    if now.hour in period and now.minute<=10:
        # return redirect(url_for('closed.html'))
        print("$$$$$$$$$$$$$$$$$$ video capturing started $$$$$$$$$$$$$$$$$$$$$$$$$")
        return render_template('video.html')

    else:
        # return redirect(url_for('video.html'))
        return render_template('closed.html')



@app.route('/video_feed')
def video_feed():

    # cap=cv2.VideoCapture(0)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/detail')
def detail():
    now = findCurrentTime()
    if now.hour in period and now.minute <= 10:
        att_detail = studentDetail.copy()
        studentDetail["roll"] = ""
        studentDetail["name"] = ""
        studentDetail["dept"] = ""
        studentDetail["time"] = ""
        studentDetail["marked"] = False
        studentDetail["date"] = ""
        studentDetail["period"]=""
        return render_template('detail.html',att_detail=att_detail)
    else:
        global capFlag
        if capFlag == True:
            cap.release()
            capFlag = False
        return render_template('closed.html')



@app.route('/automsg')
def automsg():
        global capFlag
        if capFlag == True:
            cap.release()
            capFlag = False
        now = findCurrentTime()
        if now.hour>=13:
            print("##################### whatsapp started #####################")
            executor.submit(whatsapp)
            return render_template('ack.html')
        else:
            return  render_template('automsg.html')


@app.route('/ack')
def ack():
    return render_template('ack.html')




def whatsapp():

    if now.hour >= 13:
        findAbsent = f"SELECT roll FROM students EXCEPT SELECT roll FROM attendance WHERE date='{date}' ORDER by roll"
        cur.execute(findAbsent)

        for row in cur.fetchall():
            insertSql = f"INSERT INTO attendance VALUES('{row[0]}','{date}')"
            cur.execute(insertSql)
            conn.commit()

        findPresentAbsent(cur, date)
        print("##################### whatsapp started #####################")
        runMsg()




if __name__ == "__main__":
    app.run(debug=True)

# </string:id></id></id>