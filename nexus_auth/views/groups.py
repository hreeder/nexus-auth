from nexus_auth import app, db, grouptools
from nexus_auth.models.eve import Corporation
from nexus_auth.models.groups import Group, GroupCategory, GroupMember, GroupParent, ApiCorpRule
from nexus_auth.models.groups import APPLICATION_PENDING, APPLICATION_ACCEPTED
from nexus_auth.models.forum import PhpBB
from nexus_auth.utils.decorators import admin_required
from nexus_auth.utils.eventlog import log_event

from flask import render_template, request, flash, redirect
from flask.ext.login import login_required, current_user

from sqlalchemy import asc


@app.route('/groups')
@app.route('/groups/list')
@login_required
def listGroups():
    categories = []
    groups = current_user.get_groups()

    for group in groups:
        if group.group.category not in categories:
            categories.append(group.group.category)

    categories = sorted(categories, key=lambda category: category.ordernumber)
    pending = GroupMember.query.filter_by(member_id=current_user.uid, app_status=0).all()
    return render_template("groups/list_user_groups.html", categories=categories, groups=groups, pending=pending)


@app.route('/groups/available')
@login_required
def listAvailableGroups():
    allcategories = GroupCategory.query.order_by(asc(GroupCategory.ordernumber)).all()
    categories = []

    for category in allcategories:
        show = False
        groups = []
        for group in category.groups.all():
            # if the group is a visible group and the group is visible to the current user
            if group.visible and group.visible_to(current_user):
                show = True
                groups.append(group)

        # If we're showing the category
        if show:
            categories.append({
                'name': category.name,
                'order': category.ordernumber,
                'groups': groups
            })

    return render_template('groups/list_available_groups.html', categories=categories)


@app.route('/groups/apply/<groupid>', methods=['GET', 'POST'])
@login_required
def applyToGroup(groupid):
    group = Group.query.filter_by(id=groupid).first_or_404()
    if group.open:
        return redirect('/groups/join/%s' % (groupid,))

    if not group.visible_to(current_user):
        flash('You are unable to apply to that group')
        return redirect('/groups/available')

    membership = GroupMember.query.filter_by(member_id=current_user.uid, group_id=group.id).first()
    if membership:
        flash('You are already a member of ' + group.name)
        return redirect('/groups/available')

    if request.method == "GET":
        return render_template('groups/apply.html', group=group)

    reason = request.form['reason']
    req = GroupMember(member_id=current_user.uid,
                      group_id=groupid,
                      group_admin=False,
                      app_status=APPLICATION_PENDING,
                      app_text=reason
    )
    db.session.add(req)
    db.session.commit()

    log_event('groups', 'apply', current_user, 'Applied to %s With Reason: %s' % (group.name, req.app_text))

    flash('Your group request has been submitted', 'success')
    return redirect('/groups')


@app.route('/groups/join/<groupid>')
@login_required
def joinGroup(groupid):
    group = Group.query.filter_by(id=groupid).first_or_404()

    if not group.open:
        return redirect('/groups/apply/%s' % (groupid,))

    if not group.visible_to(current_user):
        flash('You are unable to join that group')
        return redirect('/groups/available')

    membership = GroupMember.query.filter_by(member_id=current_user.uid, group_id=group.id).first()
    if membership:
        flash('You are already a member of ' + group.name)
        return redirect('/groups/available')

    grouptools.joinOpenGroup(current_user, group)

    log_event('groups', 'join', current_user, 'Joined %s' % (group.name,))

    flash('Joined %s' % (group.name,), 'success')
    return redirect('/groups')


@app.route('/groups/leave/<groupid>')
@login_required
def leaveGroup(groupid):
    membership = GroupMember.query.filter_by(member_id=current_user.uid, group_id=groupid).first_or_404()
    if not membership.group.leavable:
        flash('You may not leave that group')
        return ('/groups')

    name = str(membership.group.name)
    grouptools.removeUserFromGroup(membership.getUser(), membership.group)

    log_event('groups', 'leave', current_user, 'Left (or withdrew app for) %s' % (name,))

    flash('You have left %s' % (name,), 'success')
    return redirect('/groups')

# =======================
#    Groups Leadership
# =======================

@app.route('/groups/admin/<groupid>')
@login_required
def administerGroup(groupid):
    group = Group.query.filter_by(id=groupid).first_or_404()
    admin = GroupMember.query.filter_by(member_id=current_user.uid, group_id=groupid, group_admin=True).first()
    if not admin and not current_user.is_admin():
        flash('You are not able to administer that group', 'danger')
        return redirect('/groups')
    return render_template('groups/group_admin.html', group=group, pending=group.getPendingMembers(),
                           members=group.getMembers())

@app.route('/groups/admin/kick/<membershipid>')
@login_required
def kickFromGroup(membershipid):
    membership = GroupMember.query.filter_by(id=membershipid).first_or_404()
    admin = GroupMember.query.filter_by(member_id=current_user.uid, group_id=membership.group_id, group_admin=True).first()
    if not admin and not current_user.is_admin():
        flash('You are not able to administer that group', 'danger')
        return redirect('/groups')

    user = membership.getUser()
    group = membership.group

    groupid = group.id

    log_event('groups', 'kick', current_user, 'Kicked %s from %s' % (user.username, group.name))

    grouptools.removeUserFromGroup(user, group)

    flash('Removed user from group')
    return redirect('/groups/admin/%s' % (groupid,))

@app.route('/groups/admin/promote/<membershipid>')
@login_required
@admin_required
def promoteMemberToGroupAdmin(membershipid):
    membership = GroupMember.query.filter_by(id=membershipid).first_or_404()

    membership.group_admin = True
    db.session.add(membership)
    db.session.commit()

    log_event('groups', 'promote', current_user, 'Promoted %s to Admin of %s' % (membership.getUser().username, membership.group.name))

    flash('%s promoted to admin of %s' % (membership.getUser().username, membership.group.name), 'success')
    return redirect('/groups/admin/%s' % (membership.group_id,))

@app.route('/groups/admin/demote/<membershipid>')
@login_required
@admin_required
def demoteMemberFromGroupAdmin(membershipid):
    membership = GroupMember.query.filter_by(id=membershipid).first_or_404()

    membership.group_admin = False
    db.session.add(membership)
    db.session.commit()

    log_event('groups', 'demote', current_user, 'Demoted %s from Admin of %s' % (membership.getUser().username, membership.group.name))

    flash('%s demoted from admin of %s' % (membership.getUser().username, membership.group.name), 'success')
    return redirect('/groups/admin/%s' % (membership.group_id,))

@app.route('/groups/admin/accept/<appid>')
@login_required
def acceptApplication(appid):
    app = GroupMember.query.filter_by(id=appid).first_or_404()
    admin = GroupMember.query.filter_by(member_id=current_user.uid, group_id=app.group_id, group_admin=True).first()
    if not admin and not current_user.is_admin():
        flash('You are not able to administer that group', 'danger')
        return redirect('/groups')
    grouptools.acceptApplication(app)

    log_event('groups', 'accept', current_user, 'Accepted %s into %s' % (app.getUser().username, app.group.name))

    flash('User accepted', 'success')
    return redirect('/groups/admin/%s' % (app.group_id,))


@app.route('/groups/admin/reject/<appid>')
@login_required
def rejectApplication(appid):
    app = GroupMember.query.filter_by(id=appid).first_or_404()
    admin = GroupMember.query.filter_by(member_id=current_user.uid, group_id=app.group_id, group_admin=True).first()
    if not admin and not current_user.is_admin():
        flash('You are not able to administer that group', 'danger')
        return redirect('/groups')
    groupid = int(app.group.id)
    user = app.getUser().username
    groupname = app.group.name

    grouptools.rejectApplication(app)

    log_event('groups', 'reject', current_user, 'Rejected %s from %s' % (user, groupname))

    flash('User rejected', 'success')
    return redirect('/groups/admin/%s' % (groupid,))

# ================
# Groups Administration (IE FOR ADMINISTRATORS, NOT GROUP LEADERS)
# ================
@app.route('/admin/groups')
@login_required
@admin_required
def groupsAdmin():
    all = Group.query.all()
    return render_template("groups/admin_groups.html", groups=all)


@app.route('/admin/groups/new', methods=['GET', 'POST'])
@login_required
@admin_required
def groupsAdminNew():
    if request.method == "GET":
        forums = PhpBB(app)
        categories = GroupCategory.query.order_by(asc(GroupCategory.ordernumber)).all()
        parents = Group.query.all()
        return render_template('groups/admin_new_group.html', forumgroups=forums.getForumGroups(),
                               categories=categories, parents=parents)

    name = request.form['name']
    description = request.form['description']
    forumgroupid = int(request.form['forumgroup'])
    categoryid = int(request.form['category'])
    parentids = [int(x) for x in request.form.getlist('parents')]
    visible = bool(request.form.getlist('visible'))
    open = bool(request.form.getlist('open'))
    leavable = bool(request.form.getlist('leavable'))

    group = Group(name=name,
                  description=description,
                  category_id=categoryid,
                  forum_group_id=forumgroupid,
                  visible=visible,
                  open=open,
                  leavable=leavable
    )
    db.session.add(group)
    db.session.commit()

    for id in parentids:
        parent = GroupParent(group_id=group.id, parent_id=id)
        db.session.add(parent)

    db.session.commit()

    return redirect('/admin/groups')


@app.route('/admin/groupcategories')
@login_required
@admin_required
def groupCategoriesAdmin():
    all = GroupCategory.query.order_by(asc(GroupCategory.ordernumber)).all()
    return render_template('groups/admin_groupcategories.html', categories=all)


@app.route('/admin/groupcategories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def groupCategoriesAdminNew():
    if request.method == "GET":
        return render_template('groups/admin_new_category.html')

    name = request.form['name']
    order = request.form['order']

    category = GroupCategory(name=name, ordernumber=order)
    db.session.add(category)
    db.session.commit()

    return redirect('/admin/groupcategories')


@app.route('/admin/corpapirules')
@login_required
@admin_required
def corpApiRules():
    rules = ApiCorpRule.query.all()
    return render_template('admin_corp_api_rules.html', rules=rules)


@app.route('/admin/corpapirules/new', methods=['GET', 'POST'])
@login_required
@admin_required
def addNewCorpApiRule():
    if request.method == "GET":
        corps = Corporation.query.order_by(Corporation.name).all()
        groups = Group.query.all()
        return render_template('admin_new_corp_api_rule.html', corps=corps, groups=groups)

    corpid = request.form['corp']
    groupid = request.form['group']

    print corpid, groupid

    rule = ApiCorpRule(corp_id=request.form['corp'], group_id=request.form['group'])
    db.session.add(rule)
    db.session.commit()

    return redirect('/admin/corpapirules')


@app.route('/admin/pending')
@login_required
@admin_required
def allPendingApplications():
    apps = GroupMember.query.filter_by(app_status=APPLICATION_PENDING).all()
    return render_template('groups/admin_all_pending_apps.html', apps=apps)
