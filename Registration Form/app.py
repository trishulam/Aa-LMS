import requests
import json
from flask import Flask, render_template, redirect, url_for, request, session
import hashlib
from datetime import datetime

current_date = datetime.today().strftime('%Y-%m-%d')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vvsecretkey' #TODO: Add Secret Key

@app.route('/')
def bio():
    return render_template('bio.html')

@app.route('/aadhaar_input', methods=['GET', 'POST'])
def aadhaar_input():
    if request.method == 'GET':
        return render_template('aadhaar_input.html')
    elif request.method == 'POST':
        aadhaar_no = request.form.get('aadhaar')
        hashed_id = hashlib.sha256(aadhaar_no.encode('utf-8')).hexdigest()
        url = 'https://fastapi-sih.herokuapp.com/find-phone/{hashed_id}'.format(hashed_id=hashed_id)
        res = requests.get(url)
        if res.json()['status']:
            phone = res.json()['phone']
            body = {
                'number': phone
            }
            url_otp = 'https://fastapi-sih.herokuapp.com/get-otp/{hashed_id}'.format(hashed_id=hashed_id)
            res_otp = requests.post(url_otp, json=body)
            return redirect('/otpform/{val}'.format(val=hashed_id))
        else:
            return render_template('invalid_aadhaar.html')

@app.route('/parent_aadhaar', methods=['GET', 'POST'])
def parent_aadhaar():
    if request.method == 'GET':
        return render_template('parent_aadhaar.html')
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

@app.route('/register/<val>', methods=['GET', 'POST'])
def register(val):
    if request.method == 'GET':
        return render_template('register_form_new.html')
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('number')
        institution_code = request.form.get('institution_code')
        birthdate = request.form.get('birthdate')
        gender = request.form.get('gender')
        course = request.form.get('opt')
        p_email = request.form.get('p_email')
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
            "parent_mail": str(p_email),
            "parent_approval": "None",
            "academic_details": [
                    {
                    "institution_name": "Z.P. SCHOOL DHANORA", #TODO Add insti name
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

# @app.route('/otpform/<val>', methods=['GET', 'POST'])
# def otpform(val):
#     if request.method == 'GET':
#         return render_template('otp_form.html', val=val)
#     elif request.method == 'POST':
#         otp = request.form.get('otp')
#         headers = {"Content-Type": "application/json"}
#         url = f'https://fastapi-sih.herokuapp.com/find-user-id/{val}'
#         res = requests.get(url, headers=headers)
#         res_content = res.json()
#         url_verify_otp = f'https://fastapi-sih.herokuapp.com/verify-otp/{val}/{otp}'
#         res_verify_otp = requests.put(url=url_verify_otp)
#         if res_verify_otp.json()['success'] == "ok":
#             if res_content['status'] == 'ok' and len(res_content['data']) > 0 and res_content['data'][0]['tc'] == True:
#                 print(res_content['data'][0])
#                 session['dict'] = res_content['data'][0]
#                 return redirect(url_for('update_register'))
#             elif len(res_content['data']) == 0:
#                 return redirect('/register/{val}'.format(val=val))
#             else:
#                 return render_template('registered.html')
#         elif res_verify_otp.json()['success'] == "not ok":
#             return render_template("success.html")
# <---------------------------------------NEW ------------------------------------->
@app.route('/otpform/<val>', methods=['GET', 'POST'])
async def otpform(val):
    if request.method == 'GET':
        return render_template('otp_input.html', val=val)
    elif request.method == 'POST':
        otp1 = request.form.get('id1')
        otp2 = request.form.get('id2')
        otp3 = request.form.get('id3')
        otp4 = request.form.get('id4')
        otp = otp1+otp2+otp3+otp4

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
                return redirect(url_for('update_register'))
            elif len(res_content['data']) == 0:
                return redirect('/register/{val}'.format(val=val))
            else:
                return render_template('registered.html')
        elif res_verify_otp.json()['success'] == "not ok":
            return render_template("invalid_otp.html")
# <-------------------------------------- END NEW ------------------------------------->
@app.route('/update-register', methods=['GET', 'POST'])
def update_register():
    data=session['dict']
    if request.method == 'GET':
        return render_template('update_register_new.html', data=data)
    
    if request.method == 'POST':
        institute_id= request.form.get('institution_code')
        gender = request.form.get('gender')
        course = request.form.get('course')
        college = request.form.get('college')

        body = {
            "course": course,
            "institution_name": college,
            "doj": current_date,
            "dol": "None" 
        }
        headers = {'Content-Type': "application/json", 'Accept': "application/json"}
        aid=data['aadhar']

        url= f'https://fastapi-sih.herokuapp.com/update-user-many/{aid}'
        url1= f'https://fastapi-sih.herokuapp.com/update-user-id/{aid}'
        url2 = f'https://fastapi-sih.herokuapp.com/update-user-tc-false/{aid}'
        udise_body = {
            "institute_id": institute_id
        }
        res1 = requests.put(url1, json=udise_body, headers=headers)
        res = requests.put(url, json=body, headers=headers)
        if (res.json()['status'] == "ok"):
            res2 = requests.put(url2)
            return render_template("success.html")
        return render_template('register2.html', data=data)



if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0', port=1000)