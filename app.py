
from email.message import Message
import json

from flask import Flask
from flask import render_template, request, redirect, url_for, session
import requests
from datetime import datetime
from pypdf import generate_tc
import hashlib

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

current_date = datetime.today().strftime('%Y-%m-%d')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vvsecretkey'

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('stud_login_page.html')
    if request.method == 'POST':
        udise = request.form.get('udise')
        password = request.form.get('password')
        session['username'] = udise
        session['password'] = password

        data = {
            "udise": udise,
            "password": password
        }

        headers = {"Content-Type": "application/json"}
        url = "https://fastapi-sih.herokuapp.com/log-in"

        res = requests.get(url, headers=headers, json=data)
        if res.json()["success"] == True:
            school_name = res.json()['data']["school_name"]
            udise = res.json()['data']["udise"]
            session['school_name'] = school_name
            session['udise'] = udise
            return redirect('/index/{code}'.format(code=udise))

        elif res.json()['success'] == False:
            return render_template('stud_login_page.html')

@app.route('/index/<code>')
def index(code):
    username = session.get('username')
    password = session.get('password')
    if username == None and password == None:
        return redirect(url_for('login'))
    else:
        school_name = session.get('school_name')
        return render_template('index.html', school=school_name, code=code)

# <---------------------------------------- NEW ------------------------------------>
@app.route('/student-registration', methods=['GET', 'POST'])
def about():
    udise = session.get('udise')
    if request.method == 'GET':
        return render_template('student_registration.html', code=udise)
    
    elif request.method == 'POST':
        aadhaar_no = request.form.get('aadhaar')
        hashed_id = hashlib.sha256(aadhaar_no.encode('utf-8')).hexdigest()
        url = 'https://fastapi-sih.herokuapp.com/find-phone/{hashed_id}'.format(hashed_id=hashed_id)
        res = requests.get(url)
        phone = res.json()['phone']
        body = {
            'number': phone
        }
        url_otp = 'https://fastapi-sih.herokuapp.com/get-otp/{hashed_id}'.format(hashed_id=hashed_id)
        res_otp = requests.post(url_otp, json=body)
    
        return redirect('/otpform/{val}'.format(val=hashed_id))

@app.route('/otpform/<val>', methods=['GET', 'POST'])
def otpform(val):
    if request.method == 'GET':
        return render_template('student_registration_otp.html', val=val)
    elif request.method == 'POST':
        otp = request.form.get('otp')
        headers = {"Content-Type": "application/json"}
        url = f'https://fastapi-sih.herokuapp.com/find-user-id/{val}'
        res = requests.get(url, headers=headers)
        res_content = res.json()
        url_verify_otp = f'https://fastapi-sih.herokuapp.com/verify-otp/{val}/{otp}'
        res_verify_otp = requests.put(url=url_verify_otp)
        if res_verify_otp.json()['success'] == "ok":
            if res_content['status'] == 'ok' and len(res_content['data']) > 0 and res_content['data'][0]['tc'] == True:
                print(res_content['data'][0])
                session['dict'] = res_content['data'][0]
                return redirect(url_for('update_register')) #TODO add url
            elif len(res_content['data']) == 0:
                return redirect('/register/{val}'.format(val=val))
            else:
                return render_template('registered.html')
        elif res_verify_otp.json()['success'] == "not ok":
            return render_template("success.html")

@app.route('/register/<val>', methods=['GET', 'POST'])
def register(val):
    if request.method == 'GET':
        return render_template('student_registration_form.html')
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('number')
        institution_code = request.form.get('institution_code')
        birthdate = request.form.get('birthdate')
        college = request.form.get('college')
        admission = request.form.get('year_of_ad')
        gender = request.form.get('gender')
        course = request.form.get('course')
        aadhaar_no = val

        headers = {"Content-Type": "application/json"}

        user_data = {
            "aadhar_no": str(aadhaar_no),
            "institute_id": str(institution_code),
            "tc": False,
            "name": str(name),
            "gender": str(gender),
            "phone": str(phone),
            "birthdate": str(birthdate),
            "email": str(email),
            "academic_details": [
                    {
                    "institution_name": str(college),
                    "course": str(course),
                    "doj": str(current_date),
                    "dol": "None"
                    }
                ]
            }
        url_ekyc = f'https://fastapi-sih.herokuapp.com/ekyc/{val}'.format(val=val)
        res_ekyc = requests.get(url_ekyc)
        res_ekyc_content = res_ekyc.json()['data']
        name_ekyc = res_ekyc_content['name']
        phone_ekyc = res_ekyc_content['phone']

        if name==name_ekyc and phone==phone_ekyc:
            url = 'https://fastapi-sih.herokuapp.com/create-user'
            res = requests.post(url, headers=headers, json=user_data)
            res_content = res.json()
            phone = res_content['data'][0]['phone']
            #return redirect('ekyc')
            return render_template("success.html")
        else:
            return render_template('reg_form_new.html')

# <-------------------------------- END NEW ----------------------------------------------->

def send_mail(TO, FROM, BODY):
    # Create message container - the correct MIME type is multipart/alternative here!
    MESSAGE = MIMEMultipart('alternative')
    MESSAGE['subject'] = "SUBJECT"
    MESSAGE['To'] = TO
    MESSAGE['From'] = FROM
    MESSAGE.preamble = """
    Your mail reader does not support the report format.
    Please visit us online!"""

    # Record the MIME type text/html.
    HTML_BODY = MIMEText(BODY, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    MESSAGE.attach(HTML_BODY)

    # The actual sending of the e-mail
    server = smtplib.SMTP('smtp.gmail.com:587')

    lessSecure = "nqnpcslfkrljtsov"

    server.starttls()
    server.login(FROM,lessSecure)
    server.sendmail(FROM, [TO], MESSAGE.as_string())
    server.quit()

    return True

@app.route('/services', methods=['GET', 'POST'])
def services():
    username = session.get('username')
    password = session.get('password')
    if username == None and password == None:
        return redirect(url_for('login'))
    else:
        if request.method == 'GET':
            udise = session.get('udise')
            url = f'https://fastapi-sih.herokuapp.com/find-user-udise/{udise}'.format(udise=udise)
            res = requests.get(url)
            data = res.json()['data']
            if len(data) > 0:
                return render_template('services.html', code=udise, users=data)
            else:
                return render_template('services.html', code=udise) #TODO add no students in institute page

@app.route('/update_approval/<aid>/<pmail>')
def update_approval(aid, pmail):
    if request.method == 'GET':
        TO = pmail
        FROM = "noreply.aalms@gmail.com"

        BODY = '<div style="margin: auto; text-align: center"><h1>Respected Parent,</h1>\n' \
                '<h2>Transfer Certificate Request Verification</h2>\n' \
                '<h4>This is an intimation mail to inform that your child has applied for a Transfer Certificate.</h4>\n' \
                '<h4>Please verify that this request is valid to further move the process to</h4>\n' \
                '<h4>generate a Transfer Certificate for your child</h4>\n' \
                '<a style="text-decoration: none" href="https://fastapi-sih.herokuapp.com/set-parent-approval/'+ aid +'/approve"><button style="background-color: green; border: none; border-radius: 10px; height: 50px; width: 120px; box-shadow: 0px 0px 2px 2px rgb(177, 30, 30); color: white; font-weight: bolder; font-size: medium;">APPROVE</button></a>\n' \
                '<a style="text-decoration: none" href="https://fastapi-sih.herokuapp.com/set-parent-approval/'+ aid +'/deny"><button style="background-color: #FF0000; border: none; border-radius: 10px; height: 50px; width: 120px; box-shadow: 0px 0px 2px 2px rgb(177, 30, 30); color: white; font-weight: bolder; font-size: medium;">DENY</button></a>\n' \
                '<h3>Generated Using Aa-LMS</h3></div>\n' \
        

        res = send_mail(TO, FROM, BODY)
        if res == True:
            url_set_approval = 'https://fastapi-sih.herokuapp.com/await-approval/{aid}'.format(aid=aid)
            res_set_approval = requests.put(url_set_approval)
            return redirect(url_for('services'))
        return redirect("/services")

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#<--------------------------------------------------------->

@app.route('/tc-details', methods=['GET', 'POST'])
def tc_details():
    if request.method == 'GET':
        url = 'https://fastapi-sih.herokuapp.com/get-tc-approved-user'
        res = requests.get(url)
        data = res.json()['data']
        return render_template('services.html', users=data)

@app.route('/update_tc/<aid>')
def update_tc(aid):
    if request.method == 'GET':
        url_get_user = f'https://fastapi-sih.herokuapp.com/find-user-id/{aid}'.format(aid=aid)
        url_update_tc = 'https://fastapi-sih.herokuapp.com/update-user-tc/{aid}'.format(aid=aid)
        res_get_user = requests.get(url_get_user)
        dol = current_date
        doj = res_get_user.json()['data'][0]['academic_details'][-1]['doj']
        print(res_get_user.json())
        dob = res_get_user.json()['data'][0]['dob']

        url_dol_update = f'https://fastapi-sih.herokuapp.com/last/{aid}/{doj}/{dol}'.format(aid=aid, doj=doj, dol=current_date)
        res_update_dol = requests.put(url_dol_update)

        res = requests.put(url_update_tc)
        name = res.json()['data'][0]['name']
        dob = dob
        gender = "male"
        institution_name = res.json()['data'][0]['academic_details'][-1]['institution_name']

        generate_tc(name, dob, gender, institution_name)
        return redirect('/services')

#<--------------------------------------------------------->

""" @app.route('/student-tc/<id>')
def student_tc(id):
    url = f'https://fastapi-sih.herokuapp.com/find-user-id/{id}'.format(id=id)
    res = requests.get(url)
    name = res.json()['data'][0]['name']
    return redirect('/confirmation/{name}/{id}'.format(name=name, id=id))

@app.route('/confirmation/<name>/<id>', methods=['GET', 'POST'])
def confirmation(name, id):
    if request.method=='GET':
        return render_template('confirm.html', name=name)

    if request.method=='POST':
        val = request.form.get('confirm')
        if val == 'confirm':
            headers = {'Content-Type': "application/json", 'Accept': "application/json"}
            url_get_user = f'https://fastapi-sih.herokuapp.com/find-user-id/{id}'.format(id=id)
            url = f'https://fastapi-sih.herokuapp.com/update-user-tc/{id}'.format(id=id)

            res_get_user = requests.get(url_get_user)
            dol = current_date
            doj = res_get_user.json()['data'][0]['academic_details'][-1]['doj']
            print(res_get_user.json())
            dob = res_get_user.json()['data'][0]['dob']
            print(dob)

            url_dol_update = f'https://fastapi-sih.herokuapp.com/last/{id}/{doj}/{dol}'.format(id=id, doj=doj, dol=current_date)
            res_update_dol = requests.put(url_dol_update)

            res = requests.put(url)
            name = res.json()['data'][0]['name']
            dob = dob
            gender = "male"
            institution_name = res.json()['data'][0]['academic_details'][-1]['institution_name']

            generate_tc(name, dob, gender, institution_name)
        
            return redirect(url_for('success'))
        else:
            return render_template('confirm.html') """

@app.route('/success')
def success():
    return render_template('success.html')

if __name__ == '__main__':
    app.run(debug = True, port=5000)