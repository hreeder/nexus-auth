from nexus_auth import app, db
from nexus_auth.models.eve import Alliance, Corporation
from nexus_auth.utils.eveapi import MemcacheCache

import evelink
from time import sleep

cache = MemcacheCache(app.config)
api = evelink.api.API(cache=cache)
eve = evelink.eve.EVE(api=api)

alliances = eve.alliances().result

for id in alliances:
    # Let's find out if we already know about this alliance
    existing = Alliance.query.filter_by(id=id).first()

    # If we don't already know about it, let's add it
    if not existing:
        print "[Alliance] Adding %s" % (alliances[id]['name'],)
        newalliance = Alliance(id=id, name=alliances[id]['name'], ticker=alliances[id]['ticker'])
        db.session.add(newalliance)
        db.session.commit()
    else:
        print "[Alliance] Checking %s" % (alliances[id]['name'],)

    # Now we are gonna go through all the corporations in the alliance and make sure we know
    # about them all
    for corpid in alliances[id]['member_corps']:
        existing_corp = Corporation.query.filter_by(id=corpid).first()

        # If we already know them, and they aren't marked as being in this alliance, mark them
        if existing_corp and existing_corp.allianceId != id:
            print "[Corp] Updating %s to be in %s" % (existing_corp.name, alliances[id]['name'])
            existing_corp.allianceId = id
            db.session.add(existing_corp)
            db.session.commit()

        # Ok, let's now add the corp, if we don't know them
        elif not existing_corp:
            corp_api = evelink.corp.Corp(api=api)
            corp_sheet = corp_api.corporation_sheet(corp_id=corpid).result

            print "[Corp] Adding %s" % (corp_sheet['name'],)
            newcorp = Corporation(id=corpid, name=corp_sheet['name'], ticker=corp_sheet['ticker'], allianceId=id, memberCount=corp_sheet['members']['current'])
            db.session.add(newcorp)
            db.session.commit()

    # Now let's tidy up any corporations who are NOT in the alliance any more
    alliance = Alliance.query.filter_by(id=id).first()

    for corp in alliance.corps.all():
        if corp.id not in alliances[id]['member_corps']:
            print "[Corp] Remove %s from %s" % (corp.name, alliance.name)

    sleep(0.25)
