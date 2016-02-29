from nexus_auth import app, db
from nexus_auth.permissions import view_timers, create_timer, edit_timer
from nexus_auth.models.timers import Timer
from nexus_auth.utils.eventlog import log_event

from flask import render_template, request, redirect, abort
from flask.ext.login import current_user

import datetime
import json
import re

regionmap = {}
with open("/opt/web/nexus/system2region.csv", "r") as regionfile:
    for line in regionfile:
        k, v = line.split(",")
        regionmap[k] = v.strip()


@app.route('/timers')
@view_timers.require(403)
def timers():
    timers = Timer.query.order_by(Timer.time).all()
    return render_template('timers.html', timers=timers)


systemlist = []
with open("/opt/web/nexus/systems.json", "r") as systemsfile:
    systemlist = json.loads(systemsfile.read())


@app.route('/timers/systems')
@view_timers.require(403)
def systems():
    term = request.args.get('term')
    results = filter(lambda x: x.lower().startswith(term.lower()), systemlist)
    return json.dumps(results)

@app.route('/timers/new', methods=['POST', ])
@create_timer.require(403)
def add_timer():
    try:
        results = map(lambda x: request.form[x], ["system", "planet", "moon", "owner", "time", "notes"])
        if results[4]:
            results[4] = datetime.datetime.strptime(results[4], '%Y/%m/%d %H:%M')
        if ("reltime" in request.form) and request.form["reltime"]:
            reltime = request.form["reltime"].lower()
            kwargs = {
                "days": "(\d+)d",
                "hours": "(\d+)h",
                "minutes": "(\d+)m",
                "seconds": "(\d+)s"
            }
            for key, value in kwargs.items():
                kwargs[key] = re.search(value, reltime)
                if kwargs[key]:
                    kwargs[key] = int(kwargs[key].groups()[0])
                else:
                    del kwargs[key]
            results[4] = datetime.datetime.utcnow() + datetime.timedelta(**kwargs)
        t = Timer(*results, author=current_user.uid)
        db.session.add(t)
        db.session.commit()

        log_event('timers', 'create', current_user, 'Created Timer: %s P%s-M%s, Owner: %s, Desc: %s, Time Expires: %s' % (t.system, t.planet, t.moon, t.owner, t.notes, t.time))
        return redirect('/timers')
    except Exception as e:
        print e
        abort(500)

@app.route('/timers/delete/<id>', methods=['GET', ])
@edit_timer.require(403)
def delete(id):
    t = Timer.query.filter(Timer.id == id).first_or_404()
    log_event('timers', 'delete', current_user,  'Deleted Timer: %s P%s-M%s, Owner: %s, Desc: %s, Timer: %s' % (t.system, t.planet, t.moon, t.owner, t.notes, t.time))
    db.session.delete(t)
    db.session.commit()
    return redirect('/timers')
