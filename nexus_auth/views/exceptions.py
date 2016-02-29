from nexus_auth import app
from flask import render_template

@app.errorhandler(401)
def not_authorized(e):
	return render_template('exceptions/401.html'), 401

@app.errorhandler(403)
def forbidden(e):
    return render_template('exceptions/403.html', e=e), 403

@app.errorhandler(404)
def page_not_found(e):
	return render_template('exceptions/404.html'), 404

@app.errorhandler(500)
def server_error(e):
	return render_template('exceptions/500.html'), 500
