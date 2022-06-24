from flask import Flask,render_template,redirect,url_for,send_file,send_from_directory,request,flash,Response,session
from flask_bcrypt import Bcrypt
from datetime import datetime
import cv2 as cv
from pyzbar.pyzbar import decode
import qrcode
import random
from flask_mail import Mail,Message
from apscheduler.schedulers.background import BackgroundScheduler
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv


  
app= Flask(__name__)
bcrypt=Bcrypt(app)
sched = BackgroundScheduler({'apscheduler.timezone': 'Asia/Calcutta'})
load_dotenv()
# app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///qrproject.db'
app.config['SQLALCHEMY_DATABASE_URI']='postgres://kjplzzmxegvbma:f0f55fa9db0311e620f0dd409763abff1b26f3f685c494fe1b6ff44ea559586c@ec2-54-165-184-219.compute-1.amazonaws.com:5432/d9pbap4tvvmhp2'


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME']='chaitanyaqrproject@gmail.com'
app.config['MAIL_PASSWORD']='orhjvyvkwgfcdvhr'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail=Mail(app)

app.config['SECRET_KEY']="thisisasecretkey"
app.secret_key="hello"
otp=random.randint(0000,9999)

db=SQLAlchemy(app)
migrate=Migrate(app,db)

class Admin(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(30),nullable=False)
    password=db.Column(db.String(100),nullable=False)

    # def __repr__(self):
    #     return '<Name %r>' % self.username

# passw="admin@123"
# hashed_password=bcrypt.generate_password_hash(passw)
# admin=Admin(username="chaitanyamc001@gmail.com",password=hashed_password)
# db.session.add(admin)
# db.session.commit()
class room(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    room_number=db.Column(db.String(10),nullable=False)
    available=db.Column(db.Integer,default=1)

class users(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(30),nullable=False)
    password=db.Column(db.String(100),nullable=False)
    first_name=db.Column(db.String(30),nullable=False)
    last_name=db.Column(db.String(30),nullable=False)
    department=db.Column(db.String(10),nullable=False)
    date=db.Column(db.String(30),nullable=False)
    inside=db.Column(db.Integer,default=0)

class user_details(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(30),nullable=False)
    first_name=db.Column(db.String(30),nullable=False)
    last_name=db.Column(db.String(30),nullable=False)
    department=db.Column(db.String(10),nullable=False)
    room_number=db.Column(db.String(10),nullable=False)
    in_t=db.Column(db.String(40),nullable=False)
    exit_t=db.Column(db.String(40),nullable=False)
    date=db.Column(db.String(30),nullable=False)



def job_fun():
    res=room.query.all()
    for x in res:
        x.available=1
    db.session.commit()

sched.add_job(job_fun,trigger='cron',hour="14",minute="50")
sched.start()

picFolder=os.path.join('static','pics')
app.config['UPLOAD_FOLDER']=picFolder

@app.route('/',methods=['POST','GET'])
def index_():
    admin=os.path.join(app.config['UPLOAD_FOLDER'], 'admin.jpg')
    user=os.path.join(app.config['UPLOAD_FOLDER'], 'user.jpg')
    return render_template("index.html", admin_img=admin, user_img=user)




@app.route('/download',methods=["GET","POST"])
def download_file():
    path="img1.png"
    return send_file(path,as_attachment=True)

@app.route('/userHome',methods=['GET','POST'])
def userHome():
    if "user" in session:
        return render_template('userHome.html')
    else:
        return redirect(url_for('userLogin'))


@app.route('/userLogin',methods=['GET','POST'])
def userLogin():
    if request.method=="POST":
        user=request.form["email"]
        passw=request.form["password"]
        try:
            result=users.query.filter_by(email=user).first()
            if result:
                if bcrypt.check_password_hash(result.password, passw):
                    session["user"]=user
                    return redirect(url_for('userHome')) 
                else:
                    flash("Wrong Password!!")
                    return redirect(url_for("userLogin"))
            else:
                flash("No such username exists...Please register yourself")
                return redirect(url_for('userLogin'))     
    
        except:
            flash("Failed to get record from MySQL table: ")
            return redirect(url_for("userLogin"))
    return render_template('login.html',text="userLogin") 



@app.route('/adminLogin',methods=['GET','POST'])
def adminLogin():
    if request.method=="POST":
        user=request.form["email"]
        passw=request.form["password"]
        res=Admin.query.filter_by(username=user).first()
        if res:
            if res.username==user:
                if bcrypt.check_password_hash(res.password, passw):
                    session["admin"]=True
                    return redirect(url_for('viewUsers')) 
                else:
                    flash("Wrong Password!!")
                    return redirect(url_for("adminLogin"))
        else:
            flash("No such username exists!!")
            return redirect(url_for('adminLogin'))     
    
    return render_template('login.html',text="adminLogin") 





    




@app.route('/register',methods=['GET','POST'])
def register():
    if "admin" in session:
        if request.method=="POST":
            useremail=request.form["Email"]
            password=request.form["password"]
            fname=request.form["Fname"]
            lname=request.form["Lname"]
            dept=request.form["dept"]
            hashed_password=bcrypt.generate_password_hash(password)
            curdate=datetime.now()
            res=users.query.filter_by(email=useremail).first()

            if res:
                flash("User already exists")
                return redirect(url_for("register"))
            else:
                user=users(email=useremail,password=hashed_password,first_name=fname,last_name=lname,department=dept,date=curdate)
                db.session.add(user)
                db.session.commit()
                
                flash("Registration successful")
                return redirect(url_for('viewUsers'))
        return render_template('register.html')  
    else:
        return redirect(url_for("adminLogin"))


@app.route("/qrGenerate",methods=["GET","POST"])
def qrGenerate():
    if "admin" in session:
        if request.method=="POST":
            num=request.form['RoomNumber']
            
            features=qrcode.QRCode(version=1,box_size=40,border=3)
            features.make(fit=True)
            features.add_data(num)
            generate_image=features.make_image(fill_color="black",back_color="white")
            a="roomno"+num+".png"
            generate_image.save('./static/'+a)
            res=room.query.filter_by(room_number=num).first()
            if res:
                pass
            else:
                print("added successfully")
                room1=room(room_number=num)
                db.session.add(room1)
                db.session.commit()
            # else:
            #     print("Already QRcode is generated for this particular Room Please give regenarate")
            return render_template('converted.html',image_path=a)
        return render_template('qrGenerate.html')
    else:
        return redirect(url_for("adminLogin"))
        

@app.route('/downloads', methods=['POST'])
def downloads():
    if "admin" in session:
        path=request.form["room_no"]
        return send_from_directory('./static',path,as_attachment=True)
    else:
        return redirect(url_for("adminLogin"))

room_no=[0]



def generate_frames():
    capture=cv.VideoCapture(0)
    while True:
        ret,frame=capture.read()
        frame1=frame
        if not ret:
            break
        else:
            ret1,buffer=  cv.imencode('.jpg',frame)
            frame=buffer.tobytes()
            decoded_data=decode(frame1)
            try:
                if decoded_data[0][0]:
                    capture.release()
                    cv.destroyAllWindows()
                    room=str(decoded_data[0][0], 'UTF-8')
                    global room_no
                    room_no[0]=room
                    break
            except:
                pass
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n'+frame+b'\r\n')
            
            

@app.route('/vedio')
def vedio():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace;boundary=frame')

@app.route('/enter',methods=["GET","POST"])
def enter():
    if "user" in session:
        if request.method=="POST":
            user=session.get("user")
            if(room_no[0]==0):
                flash("Please scan a QR code")
                return redirect(url_for("enter"))
            else:
                rno=room_no[0]
                room_no[0]=0
                res=room.query.filter_by(room_number=rno).first()
                curDt=datetime.now()
                time = curDt.strftime("%H:%M:%S")
                curdate = curDt.strftime("%d:%m:%Y")
                print("time:", time)
                
                if res:
                    if res.available==0:
                        flash("Sorry!!Classroom is already occupied, Head into view classroom page","info")
                        return redirect(url_for("userHome"))
                    else:
                        res1=users.query.filter_by(email=user).first()
                        
                        if res1 and res1.inside==1:
                            flash("You have to exit from previous classroom before entering new one","info")
                            return redirect(url_for('userHome'))
                        else:
                            user_det=user_details(email=user,first_name=res1.first_name,last_name=res1.last_name,department=res1.department,room_number=rno,in_t=time,exit_t="00:00:00",date=curdate)
                            db.session.add(user_det)
                            db.session.commit()
                            res3=room.query.filter_by(room_number=rno).first()
                            res3.available=0
                            db.session.commit()
                            res3=users.query.filter_by(email=user).first()
                            res3.inside=1
                            db.session.commit()
                            flash("Hurray!! You can enter to the class now","info")       
                            return redirect(url_for('userHome'))
                else:
                    flash("This is invalid QR Code,Please scan a valid one","info")
                    return redirect(url_for("enter"))
        else:
            return render_template("scan.html",text="enter")
    else:
        return redirect(url_for("userLogin"))


@app.route('/exit',methods=["GET","POST"])
def exit():
    if "user" in session:
        if request.method=="POST":
            user=session.get("user")
            
            if room_no[0]==0:
                flash("Please scan a QR code")
                return redirect(url_for("exit"))
            else:
                rno=room_no[0]
                room_no[0]=0
                res=room.query.filter_by(room_number=rno).first()
                curDt=datetime.now()
                time = curDt.strftime("%H:%M:%S")
                curdate = curDt.strftime("%d:%m:%Y")
                t="00:00:00"
                if res:
                    if res.available==0:
                        res1=user_details.query.filter_by(room_number=rno,exit_t=t,date=curdate).first()

                        if res1 and res1.email==user:
                            res1.exit_t=time
                            db.session.commit()
                            res2=room.query.filter_by(room_number=rno).first()
                            res2.available=1
                            db.session.commit()
                            res2=users.query.filter_by(email=user).first()
                            res2.inside=0
                            db.session.commit()
                            flash("Successfull","info")
                            return redirect(url_for('userHome'))
                        else:
                            flash("You can't exit the class being handled by other staff","info")
                            return redirect(url_for('userHome'))
                    else:
                        flash("You can't exit the class which is not handled by any staff","info")
                        return redirect(url_for('userHome'))
                        

                else:
                    flash("This is invalid QR Code,Please scan a valid one","info")
                    return redirect(url_for("exit"))
        else:
            return render_template("scan.html",text="exit")
    else:
        return redirect(url_for("userLogin"))
    

@app.route("/viewClass",methods=["GET","POST"])
def viewClass():
    if "user" in session:
        res=room.query.all()
        return render_template("classroom.html",room=res)

    else:
        return redirect(url_for("userLogin"))

@app.route("/viewStaff",methods=["GET","POST"])
def viewStaff():
    if "admin" in session:
        res=users.query.all()
        return render_template("staff.html",staff=res)
    else:
        return redirect(url_for("adminLogin"))

@app.route("/viewUsers",methods=["GET","POST"])
def viewUsers():
    if "admin" in session:
        res=user_details.query.all()
        return render_template("users.html",users=res)
    else:
        return redirect(url_for("adminLogin"))
    
@app.route("/index")
def index():
    return render_template("index.html")
    
@app.route("/changePass",methods=["GET","POST"])
def changePass():
    if "user" in session:
        if request.method=="POST":
            oldPass=request.form["oldPass"]
            newPass=request.form["newPass"]
            user=session["user"]
            
            res=users.query.filter_by(email=user).first()
            if res:
                if bcrypt.check_password_hash(res.password, oldPass):
                        hashed_password=bcrypt.generate_password_hash(newPass)
                        res.password=hashed_password
                        db.session.commit()
                        flash("Password changed successfully")
                        return redirect(url_for("userHome"))
                else:
                    flash("Incorrect Old password. Please enter appropriate password")
                    return redirect(url_for("changePass"))
            else:
                flash("Sorry for inconvinience, please try again")
                return redirect(url_for("changePass"))
        else:
            return render_template("changePass.html")
    else:
        return redirect(url_for("userLogin"))

@app.route("/usage",methods=["POST","GET"])
def usage():
    if "user" in session:
        user=session["user"]
        res=user_details.query.filter_by(email=user).all()
        if res:
            return render_template("usage.html",users=res)
    else:
        return redirect(url_for("userLogin"))

@app.route("/mail",methods=["GET","POST"])
def mail_verify():
    if request.method=="POST":
        email=request.form['mail']
        res=users.query.filter_by(email=email).first()
        if res:
            msg=Message('OTP',sender="chaitanyaqrproject@gmail.com",recipients=[email])
            msg.body=str(otp)
            mail.send(msg)
            return render_template("otp.html",mail=email)
        else:
            flash("No such username exists..Please enter valid username")
            return redirect(url_for("mail_verify"))
    else:
        return render_template("mail.html")

@app.route("/otp",methods=["POST","GET"])
def otp_verify():
    if request.method=="POST":
        new_otp=request.form['otp']
        mail=request.form['userId']
        if otp==int(new_otp):
            return render_template("forgotPass.html",mail=mail)
        else:
            flash("U have entered wrong OTP!!Please try again")
            return redirect(url_for("mail_verify"))


@app.route("/forgotPass",methods=["POST","GET"])
def forgotPass():
    if request.method=="POST":
        password=request.form["pass"]
        userId=request.form["userId"]

        hashed_password=bcrypt.generate_password_hash(password)
        res=users.query.filter_by(email=userId).first()
        res.password=hashed_password
        db.session.commit()
        return redirect(url_for("userLogin"))

@app.route("/adminclass")
def adminclass():
    if "admin" in session:
        res=room.query.all()
        if res:
            return render_template("adminclass.html",room=res)
        else:
            return render_template("adminclass.html",room=res)
    else:
        return redirect(url_for("index_"))

@app.route('/logout',methods=["POST","GET"])
def user_logout():
    session.pop("user",None)
    return redirect(url_for("userLogin"))

@app.route('/Admin_logout',methods=["POST","GET"])
def admin_logout():
    session.pop("admin",None)
    return redirect(url_for("index_"))




if __name__=='__main__':
    app.run(debug=True)
