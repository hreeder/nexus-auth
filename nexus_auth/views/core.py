from nexus_auth import app, users
from nexus_auth.utils.decorators import admin_required
from flask import render_template, request, redirect, flash, current_app, session
from flask.ext.login import login_user, logout_user, login_required, current_user
from flask.ext.principal import identity_changed, Identity, AnonymousIdentity

@app.route('/')
def index():
	if current_user.is_anonymous():
		return render_template('index.html')
	return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == "GET":
		return render_template('login.html')

	username = request.form['username']
	password = request.form['password']
	next_page = request.form['next_page']

	credentialsCorrect = users.checkCredentials(username, password)

	if credentialsCorrect:
		user = users.getUser(username=username)
		login_user(user, remember=True)
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.uid))
		if next_page and next_page != "None":
			return redirect(next_page)
		else:
			return redirect("/")
	else:
		flash('Unable to log you in. You maybe entered incorrect credentials', 'danger')
		return redirect("/login")

@app.route('/logout')
def logout():
	logout_user()
        for key in ('identity.name', 'identity.auth_type'):
            session.pop(key, None)
        identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
	return redirect("/")

@app.route('/admin')
@login_required
@admin_required
def admin():
	return render_template('adminhome.html')
