from nexus_auth import app, users, jabbertools
from nexus_auth.permissions import view_user_profile
from nexus_auth.models.mumble import MumbleAccount

from flask import render_template, abort

@app.route('/profile/<userid>')
@view_user_profile.require(403)
def view_profile(userid):
    user = users.getUser(userid=userid)
    if not user:
        abort(404)

    groups = user.get_groups()
    groups = [group.group.name for group in groups]

    jabber_accounts = []
    for server in jabbertools.getVisibleServers(user):
        jid = jabbertools.sanitize_username(user.username)
        jabber_accounts.append({
            'jid': jid + "@%s" % (server.server,),
            'status': server.check_user(jid),
        })

    mumble_account = MumbleAccount.query.filter_by(id=user.uid).first()

    return render_template('hr/profile.html', user=user, groups=groups, jids=jabber_accounts, mumble=mumble_account)
