# importing all the necessary python libraries for the application

from flask import Flask, render_template,request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sklearn.ensemble import RandomForestClassifier
import pickle
import requests,time
from datetime import datetime,timedelta
from googleplaces import GooglePlaces, types, lang
from geopy.geocoders import Nominatim


# WSGI application
app=Flask(__name__)

# configuring sqlite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

# instance of sqlalchemy class
db = SQLAlchemy(app)

# instance of bcrypt for hashing the password
bcrypt = Bcrypt(app)

app.secret_key = 'fghsshgshdh%$&*(^47853##$__^^((bns,kek'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    confirm_password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False,nullable=False)

    def __repr__(self):
        return f"User('{self.email}')"

model = pickle.load(open("model.pkl", "rb"))

@app.route('/')
def intropage():
    return render_template('intropage.html')

@app.route('/home', methods=['GET','POST'])
def home():
    output = None
    global result 
    if 'loggedin' in session:
        if session['is_admin'] == 0:
            userid = session['user_id']
            email = session['email']
            if request.method == 'POST':
                cough = request.form['cough']
                fever = request.form['fever']
                sore_throat = request.form['sore-throat']
                breathing = request.form['breathing']
                headache = request.form['headache']
                gender = request.form['gender']
                age = request.form['age']
                abroad = request.form['abroad']
                contact = request.form['contact']
                male = None
                female = None
                if gender == "Male":
                    male = 1
                    female = 0
                else:
                    male=0
                    female=1
                
                print(cough,
                    fever,
                    sore_throat,
                    breathing,
                    headache,
                    female,
                    male,
                    age,
                    abroad,
                    contact)
                output = model.predict([[
                    cough,
                    fever,
                    sore_throat,
                    breathing,
                    headache,
                    female,
                    male,
                    age,
                    abroad,
                    contact
                ]])
                print("Output : ",output)
                if output[0] == 1:
                    result = "Positive"
                else:
                    result = "Negative"
                print("Result : ",result)
                return redirect(url_for('result'))
            return render_template('home.html',email=email)
        else:
            return redirect(url_for('admin'))
    else:
        return redirect(url_for('signin.html'))
    
@app.route('/result')
def result():
    global result
    return render_template('result.html',result=result)

@app.route('/download')
def download_file():
    global result
    if result == "Positive":
        path = "covid19_positive_result.pdf"
    else:
        path = "covid19_negative_result.pdf"
	
    return send_file(path,as_attachment=True)


@app.route('/signup', methods=['GET','POST'])
def signup():
    message = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        users = User.query.all()
        existing_accounts = []
        for user in users:
            account = user.email
            existing_accounts.append(account)
        if email in existing_accounts:
            message="Account already exists...Try with different email address"
        elif password!=confirm_password:
            message="Your Password and Confirm Password not matched. Please type correct password..."
        else:
            # hashing the password and confirm password before storing it into the database.
            hash_password = bcrypt.generate_password_hash(password).decode('utf-8')
            hash_confirm_password = bcrypt.generate_password_hash(confirm_password).decode('utf-8')

            # add the values into the database
            user = User(email=email, password=hash_password, confirm_password = hash_confirm_password)

            db.session.add(user)
            db.session.commit()
            message = "Your account has been created! You are now able to log in', 'success'"
            return redirect(url_for('signin'))
    return render_template('signup.html', message=message)

@app.route('/signin',methods=['GET','POST'])
def signin():
    message=''
    if request.method =='POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password,password):
            session['user_id'] = user.id
            session['email'] = user.email
            session['is_admin'] = user.is_admin
            session['loggedin'] = True
            return redirect(url_for('home')) 
            
        else:
            message="Log in Unsuccessful. Please check username and password"
        
    
    return render_template("signin.html",message=message)

@app.route('/logout')
def logout():
    """
    This function helps the user to logout from the application.
    
    This logout function helps the user to logout from the application by
    popping all the values stored in the session and redirects to the signin page.

    Returns
    -------
    TYPE
        html  : It returns the signin.html page.

    """
    session.pop('loggedin', None) 
    session.pop('user_id',None)
    session.pop('is_admin',None)
    session.pop('email',None)
    return redirect(url_for('signin'))


def findSlot(age,pin,data):
    flag = 'y'
    num_days =  2
    actual = datetime.today()
    list_format = [actual + timedelta(days=i) for i in range(num_days)]
    actual_dates = [i.strftime("%d-%m-%Y") for i in list_format]
      
    # print(actual_dates)
    while True:
        counter = 0
        for given_date in actual_dates:
            
            # cowin website Api for fetching the data
            URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByPin?pincode={}&date={}".format(pin, given_date)
            header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
               
            # Get the results in json format.
            result = requests.get(URL,headers = header)
            if(result.ok):
                response_json = result.json()
                if(response_json["centers"]):
                    
                    # Checking if centres available or not
                    if(flag.lower() == 'y'):
                        for center in response_json["centers"]:
                            
                            # For Storing all the centre and all parameters
                            for session in center["sessions"]:
                                
                                # Fetching the availability in particular session
                                datas = list()
                                  
                                # Adding the pincode of area in list
                                datas.append(pin)
                                  
                                # Adding the dates available in list
                                datas.append(given_date)
                                  
                                # Adding the centre name in list
                                datas.append(center["name"])
                                  
                                # Adding the block name in list
                                datas.append(center["block_name"])
                                  
                                # Adding the vaccine cost type whether it is
                                # free or chargable.
                                datas.append(center["fee_type"])
                                  
                                # Adding the available capacity or amount of 
                                # doses in list
                                datas.append(session["available_capacity"])
                                if(session["vaccine"]!=''):
                                    datas.append(session["vaccine"])
                                counter =counter + 1
                                  
                                # Add the data of particular centre in data list.
                                if(session["available_capacity"]>0):
                                    data.append(datas)
                                      
            else:
                print("No response")
        if counter == 0:
            return 0
        return 1


@app.route('/vaccine',methods=['GET','POST'])
def vaccine():
    global data
    if request.method == 'POST':
        pin = request.form['pincode']
        age = request.form['age']
        data = list()
        result = findSlot(age,pin,data)
        if(result == 0):
            return redirect(url_for('noavailable'))
        else:
            return redirect(url_for('slot'))
    return render_template("vaccine.html")


@app.route('/slot')
def slot():
    global data
    return render_template("slot.html",data = data)

@app.route('/noavailable')
def noavailable():
    return render_template("noavailable.html")

global hospitals_list
hospitals_list = []
@app.route('/hospitals',methods=['GET','POST'])
def hospitals():
    if request.method == 'POST':
        loc = request.form['place']
        geolocator  = Nominatim(user_agent = "covitest")
        location = geolocator.geocode(loc)
        lat  = location.latitude
        long = location.longitude
        print("Latitude and Longitude : ",(lat,long))
        API_KEY = "AIzaSyDPvAgTv_WwGVhoCl_RJgiXPCRgrP-Pj2I"
        google_places = GooglePlaces(API_KEY)

        query_result = google_places.nearby_search(
            lat_lng = {'lat':lat, 'lng':long},
            radius = 20000,
            types = [types.TYPE_HOSPITAL]
            )
        # If any attributions related
        # with search results print them
        if query_result.has_attributions:
            print (query_result.html_attributions)
        
        # Iterate over the search results
        for place in query_result.places:
            hospitals_list.append(place.name)
            print (place.name)
            print("Latitude", place.geo_location['lat'])
            print("Longitude", place.geo_location['lng'])
            print() 

    return render_template('hospitals.html', hospitals_list=hospitals_list )  

@app.route('/measures')
def measures():
    return render_template('measures.html')

@app.route('/foods')
def foods():
    return render_template('foods.html')


    




            
            
            



















if __name__=='__main__':
    app.run(debug=True,use_reloader=False)