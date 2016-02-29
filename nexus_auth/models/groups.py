from nexus_auth import app, db
from nexus_auth.permissions import ACTIVE_ROLES

APPLICATION_PENDING = 0
APPLICATION_ACCEPTED = 1


class GroupCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    ordernumber = db.Column(db.Integer)
    groups = db.relationship('Group', backref='category', lazy='dynamic')


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('group_category.id'))
    forum_group_id = db.Column(db.Integer)
    visible = db.Column(db.Boolean)
    open = db.Column(db.Boolean)
    members = db.relationship('GroupMember', backref='group', lazy='dynamic')
    permissions = db.relationship('GroupPermission', backref='group', lazy='dynamic')
    leavable = db.Column(db.Boolean, default=True)

    def getMembers(self):
        return GroupMember.query.filter_by(group_id=self.id, app_status=APPLICATION_ACCEPTED).all()

    def getPendingMembers(self):
        return GroupMember.query.filter_by(group_id=self.id, app_status=APPLICATION_PENDING).all()

    def visible_to(self, user):
        # Get all valid parents for self
        parents = GroupParent.query.filter_by(group_id=self.id).all()

        # If no parents exist, then this is a top-level visible group
        if not parents:
            return True

        # Get the user's groups
        parentgroups = [int(parent.parent_id) for parent in parents]
        usergroups = [int(group.group_id) for group in user.get_groups()]

        parent_ids = set(parentgroups)
        user_group_ids = set(usergroups)

        # If there is an intersection, return true, else return false
        return bool(parent_ids & user_group_ids)

    def getChildren(self):
        children = GroupParent.query.filter_by(parent_id=self.id).all()
        output = []
        if children:
            output = [Group.query.filter_by(id=child.group_id).first() for child in children]
        return output


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    group_admin = db.Column(db.Boolean)
    app_status = db.Column(db.SmallInteger)
    app_text = db.Column(db.Text)

    def getUser(self):
        from nexus_auth import users

        return users.getUser(userid=self.member_id)


class GroupParent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    parent_id = db.Column(db.Integer, db.ForeignKey('group.id'))


class GroupTools(object):
    def __init__(self):
        from nexus_auth.models.forum import PhpBB

        self.forum = PhpBB(app)

    def acceptApplication(self, application):
        application.app_status = APPLICATION_ACCEPTED

        db.session.add(application)
        db.session.commit()

        self.forum.addUserToGroup(application.getUser().uid, application.group.forum_group_id)

    def rejectApplication(self, application):
        db.session.delete(application)
        db.session.commit()

    def joinOpenGroup(self, user, group):
        membership = GroupMember(member_id=user.uid, group_id=group.id, app_status=APPLICATION_ACCEPTED)
        self.addUserToGroup(user, group)
        db.session.add(membership)
        db.session.commit()

    def addUserToGroup(self, user, group):
        existing = GroupMember.query.filter_by(member_id=user.uid, group_id=group.id).first()
        if not existing:
            membership = GroupMember(member_id=user.uid, group_id=group.id, app_status=APPLICATION_ACCEPTED)
            db.session.add(membership)
            db.session.commit()
        self.forum.addUserToGroup(user.uid, group.forum_group_id)

    def removeUserFromGroup(self, user, group):
        membership = GroupMember.query.filter_by(member_id=user.uid, group_id=group.id).first()
        if membership:
            print "Attempt - Remove %s from %s. Get Children First" % (user.username, group.name)
            for child in group.getChildren():
                self.removeUserFromGroup(user, child)

            self.forum.removeUserFromGroup(user.uid, group.forum_group_id)

            print "Ok, remove %s from %s" % (user.username, group.name)

            db.session.delete(membership)
            db.session.commit()

class ApiCorpRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    corp_id = db.Column(db.Integer, db.ForeignKey('corporation.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    def get_corp(self):
        from nexus_auth.models.eve import Corporation
        return Corporation.query.filter_by(id=self.corp_id).first()

    def get_group(self):
        return Group.query.filter_by(id=self.group_id).first()

class GroupPermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    permission = db.Column(db.String(32))

    def is_active(self):
        if self.permission in ACTIVE_ROLES:
            return True
        return False
