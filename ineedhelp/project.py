from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dbSetUp import Base, User, MenuCategory, MenuItem
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

engine = create_engine('sqlite:///restaurantmenu.db', connect_args={'check_same_thread': False})
# stack overflow user:4537947
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    '''
    creates a random state token for each GET request.
    '''
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None



# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    category = session.query(MenuCategory)
    #grabs first restaurant out of database
    items = session.query(MenuItem)
    #lists all menu items for selected restaurant
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'POST')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return (render_template('publicmenu.html', category=category, items=items))
    else:
        response = make_response(json.dumps('Failed to revoke token for given user. User token: '+access_token, 400))
        response.headers['Content-Type'] = 'application/json'
        return response



#Making an API Endpoint (GET Request)
@app.route('/menu/JSON/')
def restaurantMenuJSON(menu_category_id):
    menu = session.query(MenuCategory).filter_by(id = category_id).one()
    items = session.query(MenuItem).filter_by(category_id = category_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/aboutUs')
def restaurantAbout():
    return render_template('aboutUs.html')

@app.route('/contactUs')
def restaurantContact():
    return render_template('contactUs.html')

@app.route('/')
@app.route('/index')
def restaurantIndex():
    return render_template('index.html')

@app.route('/menu')
# URL with variable PATH/<type: variable name>/PATH
def restaurantMenu():
    #function that gets executed from root route
    #takes in menu category to specify which catgory you want to see
    category = session.query(MenuCategory)
    #grabs first restaurant out of database
    items = session.query(MenuItem)
    #lists all menu items for selected restaurant
    if 'username' not in login_session:
        return (render_template('publicmenu.html', category=category, items=items))
    else:
        return (render_template ('menu.html', category=category, items=items))
    #return template to browser

@app.route('/menu/<int:category_id>/new', methods=['GET', 'POST'])
def newMenuItem(category_id):
    if request.method == "POST":
        newItem = MenuItem(name=request.form['name'], price=request.form['price'], description=request.form['desc'],
                           category_id=category_id)
        # extract name field from newmenuitem form
        session.add(newItem)
        session.commit()
        flash("New menu item created!")
        return redirect(url_for("restaurantMenu"))
    else:
        return render_template("newmenuitem.html", category_id=category_id)
        # if POST request wasn't


# Task 2: Create route for editMenuItem function here


@app.route('/menu/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editMenuItem(category_id, item_id):
    editedItem = session.query(MenuItem).filter_by(id=item_id).one()
    if login_session['user_id'] != MenuItem.user_id:
        return "<script>function myFunction() {alert('You are not authorized to edit menu items to this restaurant. " \
               "Please create your own restaurant in order to edit items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['desc']:
            editedItem.description = request.form['desc']
        session.add(editedItem)
        session.commit()
        return redirect(url_for("restaurantMenu"))
    else:
        return render_template("editmenuitem.html", category_id=category_id, item_id=item_id, item=editedItem)


# Task 3: Create a route for deleteMenuItem function here


@app.route('/menu/<int:category_id>/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteMenuItem(category_id, item_id):
    itemToDelete=session.query(MenuItem).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Menu item deleted!")
        return redirect(url_for('restaurantMenu'))
    else:
        return render_template('deletemenuitem.html', item=itemToDelete)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    #server will restart if there is a change in code -- for development
    app.run(host='0.0.0.0', port=5000)
