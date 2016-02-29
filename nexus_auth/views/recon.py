from nexus_auth import app, db
from nexus_auth.permissions import view_recon, create_pos, create_goo
from nexus_auth.models.eve import Region, Constellation, System, Celestial, EveItem, POS, Corporation, MoonGoo
from nexus_auth.utils.eventlog import log_event

from flask import render_template, abort, request, flash
from flask.ext.login import current_user

import datetime
import evepaste

@app.route('/recon')
@view_recon.require(403)
def recon_index():
    return render_template('recon/index.html')

@app.route('/recon/regions')
@view_recon.require(403)
def view_regions():
    regions = Region.get_all()
    return render_template('recon/regions.html', regions=regions)

@app.route('/recon/region/<regionid>')
@view_recon.require(403)
def view_region(regionid):
    region = Region.get(regionid)
    if not region:
        abort(404)
    constellations = region.get_constellations()
    return render_template('recon/region.html', region=region, constellations=constellations)

@app.route('/recon/constellation/<constellationid>')
@view_recon.require(403)
def view_constellation(constellationid):
    const = Constellation.get(constellationid)
    if not const:
        abort(404)
    return render_template('recon/constellation.html', constellation=const)

@app.route('/recon/system/<systemid>')
@view_recon.require(403)
def view_system(systemid):
    system = System.get(systemid)
    if not system:
        abort(404)
    return render_template('recon/system.html', system=system)

@app.route('/recon/moon/<moonid>')
@view_recon.require(403)
def view_moon(moonid):
    moon = Celestial.get(moonid)
    if not moon or not moon.groupID == 8:
        abort(404)
    return render_template('recon/moon.html', moon=moon)

@app.route('/recon/moon/<moonid>/pos', methods=['GET', 'POST'])
@view_recon.require(403)
def view_moon_pos(moonid):
    moon = Celestial.get(moonid)
    if not moon or not moon.groupID == 8:
        abort(404)

    pos_types = EveItem.get_by_market_group(478)
    if request.method == "POST":
        create_pos.test(403)
        pos = POS.query.filter_by(moonid=moonid).first()

        # If we don't already know of this pos, we're adding it
        if not pos:
            pos_type = EveItem.get(request.form['type'])
            if not pos_type:
                abort(500)
            pos = POS(moonid=moonid,
                      author=current_user.uid,
                      tower_typeid=pos_type.id
                     )

            corp = Corporation.query.filter_by(ticker=request.form['corp']).first()
            if corp:
                pos.corpid = corp.id
                owner_string = "%s [%s]" % (corp.name, corp.ticker)
                if corp.alliance:
                    owner_string += " %s <%s>" % (corp.alliance.name, corp.alliance.ticker)
            else:
                pos.corp_ticker = request.form['corp'].upper()
                owner_string = pos.corp_ticker

            db.session.add(pos)
            db.session.commit()

            log_event('recon_pos', 'create', current_user, 'Added new POS at %s, Owner: %s' % (moon.name, owner_string))

    return render_template('recon/pos.html', moon=moon, postypes=pos_types)

@app.route('/recon/moon/<moonid>/goo', methods=['GET', 'POST'])
@view_recon.require(403)
def view_moongoo(moonid):
    moon = Celestial.get(moonid)
    if not moon or not moon.groupID == 8:
        abort(404)

    goo = MoonGoo.query.filter_by(moonid=moon.id).first()
    goo_types = EveItem.get_by_market_group(501)
    existing=False

    if goo:
        existing = True
        existing_string = goo.goo_string()

    if request.method == "POST":
        create_goo.test(403)
        g1 = request.form['goo1']
        g2 = request.form['goo2']
        g3 = request.form['goo3']
        g4 = request.form['goo4']

        if not goo:
            goo = MoonGoo(moonid=moon.id, last_updated=datetime.datetime.utcnow(), last_editor=current_user.uid)

        if g1:
            goo.goo_1_typeid = g1

        if g2:
            goo.goo_2_typeid = g2

        if g3:
            goo.goo_3_typeid = g3

        if g4:
            goo.goo_4_typeid = g4

        db.session.add(goo)
        db.session.commit()
        moon = Celestial.get(moonid)

        if existing:
            log_event('recon_goo', 'modify', current_user, 'Changed %s from %s to %s' % (moon.name, existing_string, goo.goo_string()))
        else:
            log_event('recon_goo', 'create', current_user, 'Added Goo Data at %s - %s' % (moon.name, goo.goo_string()))

    return render_template('recon/goo.html', moon=moon, gootypes=goo_types)

@app.route('/recon/devtest', methods=['GET', 'POST'])
@view_recon.require(403)
def test_paster():
    if request.method == "GET":
        return render_template('recon/dscan_input.html')

    scan = evepaste.parse(request.form['scan'])

    print scan
    return render_template('recon/dscan_input.html')
