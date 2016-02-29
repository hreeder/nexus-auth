import evelink

from nexus_auth import app, db, keytools
from nexus_auth.models.eve import ApiKey, Character, EveItem, Alliance, Corporation
from nexus_auth.models.eve import STATUS_PENDING
from nexus_auth.tasks.eve import updateKeyInfo
from nexus_auth.permissions import view_supers

from flask import render_template, request, redirect, flash
from flask.ext.login import login_required, current_user
from sqlalchemy.exc import IntegrityError


@app.route('/eve/keys')
@login_required
def manage_keys():
    keys = ApiKey.query.filter_by(owner=current_user.uid).all()
    return render_template("eve/manage_keys.html", keys=keys)

@app.route('/eve/keys/refresh/<keyid>')
@login_required
def refresh_key(keyid):
    key = ApiKey.query.filter_by(id=keyid).first_or_404()
    if key.owner != current_user.uid and not current_user.is_admin():
        flash('That key does not belong to you, you may not refresh it')
        return redirect('/eve/keys')
    updateKeyInfo.delay(keyid)
    flash('Update job sumitted', 'success')
    return redirect('/eve/keys')

@app.route('/eve/keys/add', methods=['POST'])
@login_required
def add_key():
    userid = request.form['userid']
    vcode = request.form['vcode']
    desc = request.form['description']

    if not userid or not vcode:
        flash('You must input a UserID and VCode', 'danger')
        return redirect('/eve/keys')

    try:
        info = keytools.validateKey(userid, vcode)
        if info['type'] == "char":
            flash('You must input an account key. Character keys are not valid')
            return redirect('/eve/keys')

        otheruser = False
        for charid in info['charids']:
            char = Character.query.filter_by(id=charid).first()
            if char and char.owner != current_user.uid:
                otheruser = True

        if otheruser:
            flash("""One of the characters on that key is already registered to another user. \
            It has not been added to your account""")
            return redirect('/eve/keys')
    except evelink.api.APIError, e:
        print e, e.code
        if e.code == "203":
            flash('That key is not valid. Please enter a valid key', 'danger')
        else:
            flash(
                """Something is wrong with that key. Please check it is valid and try again.\
                If you experience this error repeatedly, contact an admin.""",
                "danger")
        return redirect('/eve/keys')

    key = ApiKey(id=userid,
                 vcode=vcode,
                 desc=desc,
                 owner=current_user.uid,
                 type=info['type'],
                 status=STATUS_PENDING,
                 accessMask=info['access_mask'],
                 expiry=info['expiry'])

    try:
        db.session.add(key)
        db.session.commit()
    except IntegrityError, e:
        flash(
            """Unable to add that key to your account. It is already on someone else's account. \
            If you believe this to be in error, please contact an admin.""",
            'danger')
        return redirect('/eve/keys')

    updateKeyInfo.delay(userid)

    return redirect('/eve/keys')

@app.route('/eve/keys/delete/<keyid>')
@login_required
def delete_key(keyid):
    flash("""This function is still being worked on. \
    Please contact an administrator to remove your keys for the time being.""", 'info')
    return redirect('/eve/keys')

@app.route('/eve/characters')
@login_required
def show_characters():
    toons = Character.query.filter_by(owner=current_user.uid).all()
    chars = []
    for toon in toons:
        if toon.corpId:
            chars.append(toon)
    return render_template('eve/characters.html', characters=chars)

@app.route('/eve/supers')
@view_supers.require(403)
def show_supers():
    titans = EveItem.get_by_group(30)
    supercapitals = EveItem.get_by_group(659)

    types = [item.id for item in titans]
    types.extend([item.id for item in supercapitals])

    supers = Character.query.filter(Character.lastKnownShip.in_(types)).all()
    return render_template('eve/supers.html', supers=supers)

@app.route('/eve/alliance/<allianceid>')
@login_required
def view_alliance(allianceid):
    alliance = Alliance.query.filter_by(id=allianceid).first_or_404()
    return render_template('eve/alliance.html', alliance=alliance)

@app.route('/eve/corp/<corpid>')
@login_required
def view_corp(corpid):
    corp = Corporation.query.filter_by(id=corpid).first_or_404()
    return render_template('eve/corp.html', corp=corp)
