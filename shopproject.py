import os
import sys
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Shop, CategoryItem, User
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

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "shop project"


# Connect to Database and create database session
engine = create_engine('sqlite:///shop.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
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
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
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
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Shop Information
@app.route('/shop/<int:shop_id>/category/JSON')
def shopCategoryJSON(shop_id):
    shop = session.query(Shop).filter_by(id=shop_id).one()
    items = session.query(CategoryItem).filter_by(
        shop_id=shop_id).all()
    return jsonify(CategoryItems=[i.serialize for i in items])


@app.route('/shop/<int:shop_id>/category/<int:category_id>/JSON')
def categoryItemJSON(shop_id, category_id):
    Category_Item = session.query(CategoryItem).filter_by(id=category_id).one()
    return jsonify(Category_Item=Category_Item.serialize)


@app.route('/shop/JSON')
def shopsJSON():
    shops = session.query(Shop).all()
    return jsonify(shops=[r.serialize for r in shops])


# Show all shops
@app.route('/')
@app.route('/shop/')
def showShops():
    shops = session.query(Shop).order_by(asc(Shop.name))
    if 'username' not in login_session:
        return render_template('publicshops.html', shops=shops)
    else:
        return render_template('shops.html', shops=shops)

# Create a new shop


@app.route('/shop/new/', methods=['GET', 'POST'])
def newShop():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newShop = Shop(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newShop)
        flash('New Shop %s Successfully Created' % newShop.name)
        session.commit()
        return redirect(url_for('showShops'))
    else:
        return render_template('newShop.html')

# Edit a shop


@app.route('/shop/<int:shop_id>/edit/', methods=['GET', 'POST'])
def editShop(shop_id):
    editedShop = session.query(
        Shop).filter_by(id=shop_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedShop.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedShop.name = request.form['name']
            flash('Shop Successfully Edited %s' % editedShop.name)
            return redirect(url_for('showShops'))
    else:
        return render_template('editShop.html', shop=editedShop)


# Delete a shop
@app.route('/shop/<int:shop_id>/delete/', methods=['GET', 'POST'])
def deleteShop(shop_id):
    shopToDelete = session.query(
        Shop).filter_by(id=shop_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if shopToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(shopToDelete)
        flash('%s Successfully Deleted' % shopToDelete.name)
        session.commit()
        return redirect(url_for('showShops', shop_id=shop_id))
    else:
        return render_template('deleteShop.html', shop=shopToDelete)

# Show a shop category


@app.route('/shop/<int:shop_id>/')
@app.route('/shop/<int:shop_id>/category/')
def showCategory(shop_id):
    shop = session.query(Shop).filter_by(id=shop_id).one()
    creator = getUserInfo(shop.user_id)
    items = session.query(CategoryItem).filter_by(
        shop_id=shop_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publiccategory.html', items=items, shop=shop, creator=creator)
    else:
        return render_template('category.html', items=items, shop=shop, creator=creator)


# Create a new category item
@app.route('/shop/<int:shop_id>/category/new/', methods=['GET', 'POST'])
def newCategoryItem(shop_id):
    if 'username' not in login_session:
        return redirect('/login')
    shop = session.query(Shop).filter_by(id=shop_id).one()
    if login_session['user_id'] != shop.user_id:
        return "<script>function myFunction() {alert('You are not authorized.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newItem = CategoryItem(name=request.form['name'], description=request.form['description'], price=request.form[
                           'price'], course=request.form['course'], shop_id=shop_id, user_id=shop.user_id)
        session.add(newItem)
        session.commit()
        flash('New Category %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showCategory', shop_id=shop_id))
    else:
        return render_template('newcategoryitem.html', shop_id=shop_id)

# Edit a category item


@app.route('/shop/<int:shop_id>/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategoryItem(shop_id, category_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(CategoryItem).filter_by(id=category_id).one()
    shop = session.query(Shop).filter_by(id=shop_id).one()
    if login_session['user_id'] != shop.user_id:
        return "<script>function myFunction() {alert('You are not authorized.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        session.add(editedItem)
        session.commit()
        flash('Category Item Successfully Edited')
        return redirect(url_for('showCategory', shop_id=shop_id))
    else:
        return render_template('editcategoryitem.html', shop_id=shop_id, category_id=category_id, item=editedItem)


# Delete a category item
@app.route('/shop/<int:shop_id>/category/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategoryItem(shop_id, category_id):
    if 'username' not in login_session:
        return redirect('/login')
    shop = session.query(Shop).filter_by(id=shop_id).one()
    itemToDelete = session.query(CategoryItem).filter_by(id=category_id).one()
    if login_session['user_id'] != shop.user_id:
        return "<script>function myFunction() {alert('You are not authorized.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Category Item Successfully Deleted')
        return redirect(url_for('showCategory', shop_id=shop_id))
    else:
        return render_template('deleteCategoryItem.html', item=itemToDelete)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showShops'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showShops'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
