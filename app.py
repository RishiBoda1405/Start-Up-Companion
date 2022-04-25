from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_pymongo import PyMongo
from functools import wraps
import random
import os
import pprint
import functools
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'some secret key'


# Connect to the database
app.config["MONGO_URI"] = "mongodb+srv://webtech:webtech@cluster0-pltxk.mongodb.net/test?retryWrites=true&w=majority"
mongo = PyMongo(app)


# security


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Please Login To Continue Login With Us", "msg")
            return redirect(url_for('login'))
    return wrap


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'signup' in request.form:
        if request.method == 'POST':
            name = request.form['name']
            mail = request.form['email']
            password = request.form['password']
            role = request.form['role']
            phone = request.form['phone']
            company = request.form['company']
            status = "pending"
            document = {
                "name": name,
                "mail": mail,
                "password": password,
                "role": role,
                "company": company,
                "phone": phone,
                "status": status
            }
            mongo.db.users.insert_one(document)
            flash('Succesfully Inserted', 'success')
            return render_template('login.html')
    if 'signin' in request.form:
        if request.method == 'POST':
            mail = request.form['email']
            password = request.form['password']
            result = mongo.db.users.find({"mail": mail})
            if(result.count() != 0 and result.count() == 1):
                for user in result:
                    c_pass = user['password']
                    role = user['role']
                    name = user['name']
                    status = user['status']
                    user_id = user['_id']
                if(c_pass == password):
                    session['logged_in'] = True
                    session['email'] = mail
                    session['name'] = name
                    session['role'] = role
                    session['id'] = str(user_id)
                    print(str(user_id))
                    if(role == "user") and status == "approve":
                        flash("Succesfully Logged In", "success")
                        return redirect(url_for('userdashboard'))
                    elif(role == "sponser") and status == "approve":
                        flash("Succesfully Logged In", "success")
                        return redirect(url_for('sponserdashboard'))
                    elif(role == "admin"):
                        flash("Succesfully Logged In", "success")
                        return redirect(url_for('admin'))
                    else:
                        flash("You are not Authorized to Access. Possible your account is rejected.", "error")
                        return redirect(url_for('login'))
                else:
                    flash("Password Not Matched", "error")
                    return redirect(url_for('login'))
            else:
                flash("No User Exsists", "error")
                return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/')
def index():
    return render_template('normal/index.html')


@app.route('/about')
def about():
    return render_template('normal/about.html')




# =================================== Admin Actions ================================
@app.route('/admin')
@is_logged_in
def admin():
    users = mongo.db.users.find()
    return render_template('normal/admindashboard.html', users=users)

@app.route('/approve/<user>')
@is_logged_in
def approve(user=None):
    if(user != None):
        status = "approve"
        test = mongo.db.users.update_one({"_id" : ObjectId(user)},{"$set":{"status": status}})
        return redirect(url_for('admin'))


@app.route('/reject/<user>')
@is_logged_in
def reject(user=None):
    if(user != None):
        status = "reject"
        test = mongo.db.users.update_one({"_id" : ObjectId(user)},{"$set":{"status": status}})
        return redirect(url_for('admin'))

@app.route('/agreements')
def agreements():
    requests = mongo.db.startup_themes.find()
    return render_template('normal/agreements.html', requests = requests)

@app.route('/approve_idea/<ideaid>')
@is_logged_in
def approveadmin(ideaid=None):
    if(ideaid != None):
        status = session['id']+"approve"
        test = mongo.db.startup_themes.update_one({"_id" : ObjectId(ideaid)},{"$set":{"admin_status": status}})
        flash("Approved Successfully","success")
        return redirect(url_for('agreements'))

# ================================== END ============================================
# ================================== Client Programs ================================

@app.route('/userdashboard')
@is_logged_in
def userdashboard():
    return render_template('client/clientdashboard.html')

@app.route('/receviedsponserships')
@is_logged_in
def receviedsponserships():
    if(session['role'] == "user"):
        user_id = session['id']
        requests = mongo.db.startup_themes.find({"user_id":user_id})
        return render_template('client/receviedsponserships.html', requests = requests)
    else:
        flash("Not Authorized to View",'error')
        return redirect(url_for('userdashboard'))

@app.route('/sendrequestclient', methods=['GET', 'POST'])
@is_logged_in
def sendrequestclient():
    if(session['role'] == "user"):
        if request.method == 'POST':
            idea = request.form['startup_name']
            abstract = request.form['abstract']
            share = request.form['share']
            amount = request.form['amount']
            goals = request.form['goals']
            user_status = "approved"
            sponser_status = "pending"
            admin_status = "pending"
            user_id = session['id']
            document = {
                "user_id":user_id,
                "idea":idea,
                "abstract":abstract,
                "share":share,
                "amount":amount,
                "goals":goals,
                "user_status":user_status,
                "sponser_status":sponser_status,
                "admin_status":admin_status
            }
            mongo.db.startup_themes.insert_one(document)
            flash('Succesfully Posted Request', 'success')
            return redirect(url_for('sendrequestclient'))

        return render_template('client/sendrequest.html')
    else:
        flash("Not Authorized to View",'error')
        return redirect(url_for('userdashboard'))


@app.route('/myrequests')
@is_logged_in
def myrequests():
    requests = mongo.db.startup_themes.find({"user_id":session['id']})
    print(requests)
    return render_template('client/myrequests.html', requests = requests)

@app.route('/reqdelete/<reqid>')
@is_logged_in
def requestdelete(reqid=None):
    if(request != None):
        mongo.db.startup_themes.remove({"_id":ObjectId(reqid)})
        flash("Request Deleted Successfully",'error')
        return redirect(url_for('myrequests'))
# ================================== END ============================================

# ================================= Sponser Programs ================================

@app.route('/sponserdashboard')
@is_logged_in
def sponserdashboard():
    requests = mongo.db.startup_themes.find({"sponser_status": "pending"})
    return render_template('sponser/sponser-dashboard.html', requests = requests)

@app.route('/reqapprv/<reqid>')
@is_logged_in
def requestapprove(reqid=None):
    if(request != None):
        status = session['id']+"approve"
        mongo.db.startup_themes.update({"_id":ObjectId(reqid)},{"$set":{"sponser_status": status}})
        flash("Request Accepte Successfully, Waiting for Admin Approval",'success')
        return redirect(url_for('sponserdashboard'))
@app.route('/sponsering')
def sponsering():
    status = session['id']+"approve"
    # context = {}
    # sponserings = mongo.db.startup_themes.find({"sponser_status": status})
    # for idea in sponserings:
    #     print(idea)
    #     user_id = str(idea['_id'])
    #     user_details = mongo.db.users.find({"_id":ObjectId(user_id)}) 
    #     for user in user_details:
    #         context[str(idea['_id'])] = {
    #             "company": user['company'],
    #             "user": user['name'],
    #             "phone":user['phone']
    #         }
    requests = mongo.db.startup_themes.find({"sponser_status": status})
    return render_template('sponser/sponsering.html', requests = requests)
# ================================= END =============================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = 'some secret key'
    app.run(debug=True)
