from nexus_auth import app, db, jabbertools
from nexus_auth.permissions import view_temp_ops, create_temp_op, expire_temp_op
from nexus_auth.models.eve import Character
from nexus_auth.models.jabber import Prosody
from nexus_auth.models.mumble import MumbleAccount, MumbleOperation, TYPE_REGISTERED, TYPE_TEMPORARY
from nexus_auth.utils.decorators import services_access_required, admin_required
from nexus_auth.utils.eventlog import log_event

from flask import flash, redirect, render_template, request, abort
from flask.ext.login import login_required, current_user

from sqlalchemy import desc

import hashlib
import datetime
import uuid
import string
import random

@app.route('/services')
@login_required
@services_access_required
def services_home():
    character = Character.query.filter_by(owner=current_user.uid, name=current_user.username).first()
    if not character:
        flash("""You do not have an API key in for your main character. \
        If you registered with a username that is NOT your main character name, please contact an admin.""")
        return redirect('/eve/keys')

    if character.corp.allianceId == app.config['ALLIANCE_ID']:
        display_name = character.corp.ticker
    else:
        if character.corp.alliance:
            display_name = character.corp.alliance.ticker
        else:
            character.corp.ticker

    display_name += " - " + character.name

    mumbleservice = MumbleAccount.query.filter_by(id=current_user.uid).first()

    return render_template('services/list.html',
                           jabberservers=jabbertools.getVisibleServers(current_user),
                           safename=jabbertools.sanitize_username(current_user.username),
                           mumbleservice=mumbleservice,
                           mumblename=display_name
    )

@app.route('/services/jabber/create/<server>', methods=['GET', 'POST'])
@login_required
@services_access_required
def add_jabber_account(server):
    if server not in app.config['PROSODY']:
        flash('That jabber server does not exist.', 'danger')
        return redirect('/services')

    if not isinstance(app.config['PROSODY'][server], dict):
        flash('That jabber server does not exist.', 'danger')
        return redirect('/services')

    if app.config['PROSODY'][server]['required'] not  in current_user.get_group_ids():
        flash('You are unauthorized to make an account on that jabber service', 'danger')
        return redirect('/services')

    username = jabbertools.sanitize_username(current_user.username)

    if request.method == "GET":
        return render_template('services/new.html', servicename=server, username=username + "@" + server)

    # Create the account!
    password = request.form['password']

    service = Prosody(app, server)

    if "username" in service.add_user(username, password):
        flash('Account Created. You may now log in to Jabber.', 'success')
    else:
        flash('Unable to create account. If this problem repeats, contact an admin.', 'danger')

    return redirect('/services')

@app.route('/services/jabber/reset/<server>', methods=['GET', 'POST'])
@login_required
@services_access_required
def reset_jabber_password(server):
    if server not in app.config['PROSODY']:
        flash('That jabber server does not exist.', 'danger')
        return redirect('/services')

    if app.config['PROSODY'][server]['required'] not  in current_user.get_group_ids():
        flash('You are unauthorized to make an account on that jabber service', 'danger')
        return redirect('/services')

    if request.method == "GET":
        return render_template('services/reset.html', service=server)

    username = jabbertools.sanitize_username(current_user.username) + "@" + server
    password = request.form['password']
    service = Prosody(app, server)

    if service.reset_password(username, password):
        flash('Reset Succesful', 'success')
    else:
        flash('Something went wrong')

    return redirect('/services')

@app.route('/services/mumble/create', methods=['GET', 'POST'])
@login_required
@services_access_required
def add_mumble_account():
    character = Character.query.filter_by(owner=current_user.uid, name=current_user.username).first()
    if not character:
        flash("""You do not have an API key in for your main character.\
        If you registered with a username that is NOT your main character name, please contact an admin.""")
        return redirect('/eve/keys')

    existing = MumbleAccount.query.filter_by(id=current_user.uid).first()
    if existing:
        flash("""You already have an account on mumble. You may not create a second one""")
        return redirect("/services")

    if character.corp.allianceId == app.config['ALLIANCE_ID']:
        display_name = character.corp.ticker
    else:
        if character.corp.alliance:
            display_name = character.corp.alliance.ticker
        else:
            character.corp.ticker

    display_name += " - " + character.name

    if request.method == "GET":
        return render_template('services/new_mumble.html',
                               display=display_name)

    password = hashlib.sha1(request.form['password'] + current_user.username.lower().replace("'", "").encode('utf8'))

    account = MumbleAccount(id=current_user.uid,
                            username=current_user.get_mumblename(),
                            display=display_name,
                            password=password.hexdigest(),
                            account_type=TYPE_REGISTERED
    )

    db.session.add(account)
    db.session.commit()

    flash('Account Created. You may now log in to Mumble', 'success')
    return redirect('/services')

@app.route('/services/mumble/reset', methods=['GET', 'POST'])
@login_required
@services_access_required
def reset_mumble_password():
    if request.method == "GET":
        return render_template('services/reset.html', service="SIGH.Mumble")

    character = Character.query.filter_by(owner=current_user.uid, name=current_user.username).first()
    account = MumbleAccount.query.filter_by(id=current_user.uid).first_or_404()
    password = request.form['password']
    password = hashlib.sha1(request.form['password'] + current_user.username.lower().replace("'", "").encode('utf8'))

    if character.corp.allianceId == app.config['ALLIANCE_ID']:
        display_name = character.corp.ticker
    else:
        if character.corp.alliance:
            display_name = character.corp.alliance.ticker
        else:
            character.corp.ticker

    display_name += " - " + character.name

    account.display=display_name
    account.password=password.hexdigest()
    db.session.add(account)
    db.session.commit()

    flash('Reset Succesful', 'success')
    return redirect('/services')


@app.route('/services/mumble/ops')
@login_required
@view_temp_ops.require(403)
def mumble_ops():
    ops = MumbleOperation.query.order_by(desc(MumbleOperation.started)).limit(25).all()
    return render_template('services/mumble_op_list.html', ops=ops)


@app.route('/services/mumble/ops/new', methods=['GET', 'POST'])
@login_required
@create_temp_op.require(403)
def mumble_new_tempop():
    if request.method == "GET":
        return render_template('services/mumble_op_new.html')

    name = request.form['name']
    expiry = request.form['expiry']

    if not name or not expiry:
        flash('One or more values were not input, please try again')
        return redirect('/services/mumble/ops/new')

    expires = datetime.datetime.strptime(expiry, "%Y/%m/%d %H:%M")

    if not expires:
        flash('Something went wrong parsing that date/time. Please try again')
        return redirect('/services/mumble/ops/new')

    url_uuid = uuid.uuid4()
    segment = hashlib.sha1(str(url_uuid) + current_user.username + name)

    op = MumbleOperation(owner=current_user.uid,
                         name=name,
                         expires=expires,
                         started=datetime.datetime.utcnow(),
                         url_segment=segment.hexdigest()
    )

    db.session.add(op)
    db.session.commit()

    log_event('mumble_tempops', 'create', current_user, 'New Op (%s) - Expires %s.' % (name, expires))
    flash('Success! New op link show in the list below.', 'success')
    return redirect('/services/mumble/ops')


@app.route('/services/mumble/ops/expire/<opid>')
@login_required
@expire_temp_op.require(403)
def expire_mumble_tempop(opid):
    op = MumbleOperation.query.filter_by(id=opid).first_or_404()

    op.expires = datetime.datetime.utcnow()
    db.session.add(op)
    db.session.commit()

    users = op.get_registered_users()
    count = len(users)

    for user in users:
        db.session.delete(user)
    db.session.commit()

    log_event('mumble_tempops', 'expire', current_user, 'Expired Op %s (Owner: %s). Access removed for %s user(s)' % (op.name, op.get_owner().username, count))
    flash('Op expired, %d users removed' % count, 'success')
    return redirect('/services/mumble/ops')


@app.route('/services/mumble/op/<opkey>', methods=['GET', 'POST'])
def register_for_operation(opkey):
    op = MumbleOperation.query.filter_by(url_segment=opkey).first_or_404()

    if op.expires < datetime.datetime.utcnow():
        flash('That operation has already expired. Please ask the FC for a new link.', 'danger')
        abort(401)

    if request.method == "GET":
        return render_template('services/mumble_op_register.html', op=op)

    inp_ticker = request.form['ticker']
    inp_character = request.form['name']

    ticker = ""
    character = ""

    for char in inp_ticker:
        if char in string.ascii_letters or char in string.digits or char in ['.', '-', ' ']:
            ticker += char

    for char in inp_character:
        if char in string.ascii_letters or char in string.digits or char == " ":
            character += char


    display_name = "TEMP - " + ticker.upper() + " - " + character
    username = str(uuid.uuid4())[:8]
    password = hashlib.sha1(str(uuid.uuid4()) + opkey).hexdigest()

    hashedpass = hashlib.sha1(password + username.lower().replace("'", "").encode('utf8')).hexdigest()

    id=100000 + random.randint(1, 10000)
    existing = MumbleAccount.query.filter_by(id=id).first()
    while existing:
        id=100000 + random.randint(1, 10000)
        existing = MumbleAccount.query.filter_by(id=id).first()

    account = MumbleAccount(id=id, username=username, display=display_name, password=hashedpass, account_type=TYPE_TEMPORARY, op_id=op.id)
    db.session.add(account)
    db.session.commit()

    return render_template('services/mumble_op_registered.html', op=op, account=account, password=password)


#==========================
# Jabber Admin Panel Stuff
#==========================

@app.route('/admin/jabber')
@admin_required
def list_jabber_servers():
    servers = jabbertools.getAllServers()

    return render_template('services/admin_jabber_servers.html', servers=servers)

@app.route('/admin/jabber/<server>/online')
@admin_required
def list_online_jabber_users(server):
    if server not in app.config['PROSODY'] or not isinstance(app.config['PROSODY'][server], dict):
        flash('That is not a valid server', 'danger')
        return redirect('/admin/jabber')

    jserver = Prosody(app, server)

    online_users = jserver.get_all_online_users()['users']

    return render_template('services/admin_jabber_server_online_users.html', online=online_users, server=server)
