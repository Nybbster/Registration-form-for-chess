from flask_bcrypt import Bcrypt
from flask import *
import sqlite3,csv
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import *
from wtforms.validators import DataRequired, Length,Regexp
import string
import random
import os 
import io
import segno
import base64
import requests
from datetime import date


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = os.urandom(24)
app.config['SESSION_PERMENANT'] = True
app.config['PERMENANT_SESSION_LIFETIME'] = 3600
csrf = CSRFProtect(app)

class LoginForm(FlaskForm):
    username = StringField('username',[DataRequired(),Length(min=4),Regexp(r'^[A-Za-z0-9_\-\.]+$')])
    password  =PasswordField('password',[
        DataRequired(),
        Length(min=8),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[-.,_\@\$\!\%\*\?\&])[A-Za-z\-.,_d@$!%\*\?&]',
            message = "Password must be the lenght of 8 and contain uppercase, lowercase, number and a special character."   
            )
    ])


class Registration(FlaskForm):
    Firstname = StringField('Firstname',[DataRequired(), Regexp(r"^[A-Za-z]")])
    Lastname = StringField('Lastname',[DataRequired(),Regexp(r'^[A-Za-z]')])
    Ranking = IntegerField('Ranking',[validators.number_range(min=1400,max=3000)])
    FideID = IntegerField('FideID',[validators.number_range(min=1000000,max=999999999,message="cant start with 0 and must be 7 numbers")])

class CheckForm(FlaskForm):
    id = IntegerField("ID")
def DB_exist():
    try:
        with open("MySQL_database.sql","r") as sql_file:
            sql_file = sql_file.read()
        connect = sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()
        try:
            cursor.execute("SELECT * FROM registrations ")
            exist = cursor.fetchone()
            if exist is not None:
                return True
        except sqlite3.OperationalError:
            cursor.executescript(sql_file)
            connect.commit()
    except Exception as e:
        print(e)
    finally:
        connect.close()

def salt():
    SaltLenght = 8 
    Salt = ''.join(random.choices(string.ascii_letters+string.digits, k= SaltLenght)) 
    return Salt

def sanitize(name):
    allowed_chars = string.ascii_letters + string.digits + '_.-'
    return all(char in allowed_chars for char in name)

def DB_commit_reg(Firstname,Lastname,rank,id):
    if not sanitize(Firstname):
        print(f"invalid chareters in name:{Firstname,Lastname}")
        return False
    if not sanitize(Lastname):
        print(f"invalid chareters in name:{Firstname,Lastname}")
        return False
    try:
        connect = sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()
        
        #MAYBE WONT NEED THIS BC FIDEID IS PRIMARY KEY
        cursor.execute("SELECT Firstname FROM registrations WHERE FideID =?",(id,))
        exising_fideID = cursor.fetchall()
        if exising_fideID:
            print("existing FideID")
            return False
        cursor.execute("INSERT INTO registrations VALUES(?,?,?,?)",(Firstname,Lastname,rank,id,))
        connect.commit()
        connect.close()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    
def DB_commit_login(name,password):
    if not sanitize(name):
        print(f"invalid chareters in name:{name}")
        return False
    
    try:
        connect = sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()


        cursor.execute("SELECT COUNT(*) FROM login")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("Admin already exists")
            return False  
        
        Salt = salt()

        hashedPassword = bcrypt.generate_password_hash(password+Salt).decode("utf-8")

        cursor.execute("INSERT INTO login VALUES(?,?,?,?)",(0,name,hashedPassword,Salt,))
        connect.commit()
        connect.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    
def DB_read(name,password):
    if not sanitize(name):
        return False
    
    try:
        connect = sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()

        cursor.execute(
            "SELECT password, salt FROM login WHERE username = ?", 
            (name,)
        )

        Return_data= cursor.fetchone()
        
        if not Return_data:
            print(f"{name} not found")
            return None
        hashed_password ,salt = Return_data

        isValid = bcrypt.check_password_hash(hashed_password,password+salt)
        connect.close()
        if isValid:
            return True
        else:
            return False
    except sqlite3.Error as e:
        print(f"Databse Error reading: {e}")
        return None

def export_csv():
    try:
        connect = sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()
        cursor.execute("SELECT *FROM registrations")
        registrations = cursor.fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(['Firstname', 'Lastname', 'Rank', 'FideID'])
        

        for row in registrations:
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=registrations.csv'
        
        return response
    except sqlite3.InternalError as e:
        print(e)
    finally:
        connect.close()
       
def Show_entrys(ids=None):
    data=None
    try:
        connect =sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()
        if ids:
            all_data = []
            for i in ids:
                cursor.execute("SELECT * FROM registrations WHERE FideID = ?", (i,))
                data = cursor.fetchall()
                if data:
                    all_data.extend(data)  
            connect.close()
            return all_data
        else:
            cursor.execute("SELECT * FROM registrations")
            data = cursor.fetchall()
            return data
    except sqlite3.DatabaseError as e:
        print(f"Database Error {e}")
    return data

def drop_table():
    connect = sqlite3.connect("MySQL_database.db")
    cursor = connect.cursor()
    try:
        cursor.execute("DELETE FROM registrations")
        connect.commit()
        cursor.execute("SELECT * FROM registrations")
        confirm_del = cursor.fetchone()
        if confirm_del:
            print("Failed to delete registrations")
            return False
        else:
            print("Registrations Clear")
            return True

    except sqlite3.InternalError as e:
        print(f"Database Error Deleting table{e}")
    finally:
        connect.commit()
        connect.close()

def check_signed(id =None,unexpected =False, notsingedin=True):
    api = f"https://member.schack.se/public/api/v1/tournamentresults/table/id/{id}"
    get_fide = requests.get(api).json()
    API_data = [item["playerInfo"]["fideid"] for item in get_fide]
    name_data = [(item["playerInfo"]["firstName"], 
             item["playerInfo"]["lastName"],
             item["playerInfo"]["elo"]["rating"], 
             item["playerInfo"]["fideid"] 
                ) for item in get_fide]
    
    if unexpected==False:
        connect = sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()
        
        cursor.execute("SELECT FideID FROM registrations")
        db_fide_ids = [row[0] for row in cursor.fetchall()]
        if notsingedin:
            missing_players = [
                (firstname, lastname, rating, fideid) 
                for firstname, lastname, rating, fideid in name_data 
                if fideid not in db_fide_ids
            ]        
        
            connect.close()
            return missing_players
        else:
            Singedin_players = [
                (firstname, lastname, rating, fideid) 
                for firstname, lastname, rating, fideid in name_data 
                if fideid in db_fide_ids
            ]        
        
            connect.close()
            return Singedin_players
    elif unexpected:
        connect = sqlite3.connect("MySQL_database.db")
        cursor = connect.cursor()
        
        cursor.execute("SELECT FideID FROM registrations")
        db_fide_ids = [row[0] for row in cursor.fetchall()]


        OverflowingIDS = [fide_id for fide_id in db_fide_ids if fide_id not in API_data]
        
        print(f"Saknas i databasen: {OverflowingIDS}")
        
        connect.close()
        return OverflowingIDS

@app.route("/")
def def_index():
    return redirect(url_for("QR_index"))
@app.route("/QR")
def QR_index():
    registration_url = url_for('reg_index', _external=True)
    
    qr = segno.make(registration_url)
    buffer = io.BytesIO()
    qr.save(buffer, kind='png', scale=10)
    buffer.seek(0)
    
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    qr_data_url = f"data:image/png;base64,{qr_base64}"

    return render_template("QR.html", qr_image=f"data:image/png;base64,{qr_base64}",GenQR=qr_data_url)

@app.route("/Admin",methods =["GET","POST"])
@csrf.exempt
def admin_index():
    data=None
    if not session.get("logged_in"):
        return redirect(url_for("login_index"))
    session["Admin"] = True
    session.modified =True
    if request.method == "POST":
       
        if "QR" in request.form:
            return redirect(url_for("QR_index"))
        elif "CSV" in request.form:
            return export_csv()
        elif "ShowEntrys" in request.form:
            data=Show_entrys()
        elif "ShowNoneREG" in request.form:
            return redirect(url_for("check_index"))
        elif "DropTable" in request.form:
            drop_table()
            
    return render_template("Admin.html",data=data)

@app.route("/CheakEntrys", methods=["GET","POST"])
def check_index():
    data =None
    Unexpexted=None
    SingedUp=None
    notHere=None
    if not session.get("Admin"):
        return redirect(url_for("login_index"))
    check_form = CheckForm()
    if check_form.validate_on_submit():
        id = check_form.id.data
        
        if "NotSignedUp" in request.form:
            data= check_signed(id,False)
        elif "unexpected" in request.form:
            ID_data= check_signed(id,True)
            data=Show_entrys(ID_data)
        elif "SignedUp" in request.form:
            data = check_signed(id,False,False)
        elif "ShowEntrys" in request.form:
            ID_data= check_signed(id,True)
            Unexpexted=Show_entrys(ID_data)
            SingedUp = check_signed(id,False,False)
            notHere = check_signed(id,False)


    return render_template("Checking.html", form=check_form, Data=data,Unexpexted=Unexpexted,SingedUp=SingedUp,notHere=notHere)

@app.route("/Regitstarion", methods =["GET","POST"])
def reg_index():
    reg_form = Registration()

    if reg_form.validate_on_submit():
        firstname = reg_form.Firstname.data
        lastname = reg_form.Lastname.data
        rank = reg_form.Ranking.data
        id = reg_form.FideID.data

        Correct_data = DB_commit_reg(firstname,lastname,rank,id)
        if Correct_data:
            return"<h1>You are registerd</h1>"
        else:
            return"<h1>Incorrect data sent</h1>"
    else:
        return render_template("Registraion.html",form=reg_form)

@app.route("/Login",methods=["GET","POST"])
def login_index():
    log_form = LoginForm()
    
    if log_form.validate_on_submit():
        username = log_form.username.data
        password = log_form.password.data
        if "login" in request.form:
            valid = DB_read(username,password)
            if valid:
                session["logged_in"] = True
                session.modified =True
                return redirect(url_for("admin_index"))
            else:
                print("invalid")

                return "<h2> invalid user </h2>"
        elif "create" in request.form:
            commit =DB_commit_login(username,password)

            if not commit:
                print("exist")
                return "<h2> admin already exists</h2>"
            else:
                print("created")

                return"created"
        else:
            return render_template("Login.html",form=log_form)

    else:
        return render_template("Login.html",form=log_form)


if __name__=="__main__":
    DB_exist()
    app.run(debug=True)