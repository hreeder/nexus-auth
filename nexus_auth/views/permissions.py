from nexus_auth import app, db
from nexus_auth.permissions import ACTIVE_ROLES
from nexus_auth.models.groups import Group, GroupPermission
from nexus_auth.utils.decorators import admin_required

from flask import render_template, request, flash, redirect
from flask.ext.login import login_required

@app.route('/admin/permissions')
@login_required
@admin_required
def admin_permissions():
    permissions = GroupPermission.query.all()
    return render_template('admin_permissions.html', permissions=permissions)

@app.route('/admin/permissions/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_permission():
    if request.method == "GET":
        groups = Group.query.all()
        return render_template('admin_new_permission.html', groups=groups, roles=ACTIVE_ROLES)

    group = Group.query.filter_by(id=request.form['group']).first_or_404()
    if request.form['role'] not in ACTIVE_ROLES:
        flash('That is an invalid role', 'danger')
        return redirect('/admin/permissions/new')

    role = request.form['role']

    perm = GroupPermission(group_id=group.id, permission=role)
    db.session.add(perm)
    db.session.commit()

    return redirect('/admin/permissions')

@app.route('/admin/permissions/delete/<id>')
@login_required
@admin_required
def delete_permission(id):
    perm = GroupPermission.query.filter_by(id=id).first_or_404()
    permname = perm.permission
    permgroupname = perm.group.name

    db.session.delete(perm)
    db.session.commit()

    flash('Permission %s deleted from %s' % (permname, permgroupname), 'success')

    return redirect('/admin/permissions')
