import json

from nexus_auth import app, db, jabbertools
from nexus_auth.models.groups import Group
from nexus_auth.models.ping import PingServer, PingTarget, TYPE_SERVER, TYPE_GROUP
from nexus_auth.utils.decorators import admin_required

from flask import request, render_template, redirect, flash
from flask.ext.login import login_required, current_user

from sqlalchemy import asc

@app.route('/ping', methods=['GET', 'POST'])
@login_required
def ping():
    if request.method == "GET":
        # Compile list of targets
        targets = {}
        if not current_user.is_admin():
            for group in current_user.get_groups():
                group_targets = PingTarget.query.filter_by(parent_group_id=group.group_id).all()
                for target in group_targets:
                    if target.type == TYPE_SERVER:
                        id = "svr-%s" % (target.target,)
                    elif target.type == TYPE_GROUP:
                        id = "grp-%s" % (target.target,)
                    targets[id] = {'id': id, 'name': target.get_target_name()}
        # If the user is an admin we've got to do things a little differently.
        else:
            servers = PingServer.query.all()
            for server in servers:
                targets["svr-%s" % (server.id,)] = {'id': "svr-%s" % (server.id,), 'name': server.display_name}
            groups = Group.query.all()
            for group in groups:
                targets["grp-%s" % (group.id,)] = {'id': "grp-%s" % (group.id,), 'name': group.name}

        targets = sorted(targets.iteritems(), key=lambda (x,y): y['name'])
        return render_template('ping/send.html', targets=targets)

    body = request.form['broadcastcontent']
    important = bool(request.form.getlist('important'))
    targets = request.form.getlist('target')

    fleetchecked = bool(request.form.getlist('fleet'))
    fleet=False

    if fleetchecked:
        fc = request.form['fc']
        fleetname = request.form['flt-name']
        formup = request.form['formup']
        doctrine = request.form['doctrine']
        mumble = request.form['mumble']

        fleet = "Fleet: %s || FC: %s || Formup: %s || Mumble: %s || %s" % (fleetname, fc, formup, mumble, doctrine)

    jabbertools.broadcast(targets, body, current_user, important=important, fleet=fleet)
    flash('Broadcast Sent', 'success')
    return redirect('/ping')

@app.route('/admin/pingtargets')
@login_required
@admin_required
def admin_pingtargets():
    targets = PingTarget.query.order_by(asc(PingTarget.parent_group_id)).all()
    return render_template('ping/admin_ping_targets.html', targets=targets)

@app.route('/admin/pingtargets/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_pingtargets_new():
    if request.method == "GET":
        groups = Group.query.all()
        servers = PingServer.query.all()
        return render_template('ping/admin_new_ping_target.html', groups=groups, servers=servers)

    group = Group.query.filter_by(id=request.form['parentgroup']).first_or_404()
    targetinput = request.form['canping']
    type, target = targetinput.split('-')
    
    if type == "svr":
        type = TYPE_SERVER
        target = PingServer.query.filter_by(id=target).first_or_404()
    elif type == "grp":
        type = TYPE_GROUP
        target = Group.query.filter_by(id=target).first_or_404()

    newtarget = PingTarget(parent_group_id=group.id, type=type, target=target.id)
    db.session.add(newtarget)
    db.session.commit()

    return redirect('/admin/pingtargets')

@app.route('/admin/pingservers')
@login_required
@admin_required
def admin_pingservers():
    servers = PingServer.query.all()
    return render_template('ping/admin_ping_servers.html', servers=servers)

@app.route('/admin/pingservers/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_pingservers_new():
    if request.method == "GET":
        servers = jabbertools.getHosts()
        return render_template('ping/admin_new_ping_server.html', servers=servers)

    display = request.form['name']
    servers = request.form.getlist('server')

    servers = json.dumps(servers)

    server = PingServer(servers=servers, display_name=display)

    db.session.add(server)
    db.session.commit()

    return redirect('/admin/pingservers')
