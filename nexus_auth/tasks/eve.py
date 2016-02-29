import evelink, datetime

from nexus_auth import app, celery, db, users, grouptools
from nexus_auth.models.eve import ApiKey, Character, Corporation, Alliance, KeyCharacters
from nexus_auth.models.eve import TYPE_CORP, STATUS_OK, STATUS_ERROR, STATUS_ACC_EXPIRED, STATUS_KEY_EXPIRED, STATUS_KEY_INVALID
from nexus_auth.models.groups import GroupMember, ApiCorpRule, APPLICATION_ACCEPTED
from nexus_auth.utils.eveapi import MemcacheCache

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@celery.task()
def updateKeyInfo(keyid):
    logger.debug('Beginning update of key %s' % (keyid,))
    key = ApiKey.query.filter_by(id=keyid).first()
    cache = MemcacheCache(app.config)

    api = evelink.api.API(cache=cache, api_key=(key.id, key.vcode))
    logger.debug('Evelink API instantiated')

    acc = evelink.account.Account(api)

    key.lastUpdated = datetime.datetime.now()
    logger.debug('Key %s last updated: %r' % (key.id, key.lastUpdated))
    db.session.add(key)
    db.session.commit()
    logger.debug('Added and commited to db')

    try:
        characters = acc.characters().result
        logger.debug('Got characters from key: %s' % (characters,))
    except evelink.api.APIError, e:
        logger.warn('Key Error: ' + e.code)
        if str(e.code) == "222":
            key.status = STATUS_KEY_EXPIRED
        db.session.add(key)
        db.session.commit()
        return

    if characters:
        key.status = STATUS_OK
        db.session.add(key)
        db.session.commit()

    if key.type == TYPE_CORP:
        return

    for character in characters:
        # Check for association in key<>character map
        mapping = KeyCharacters.query.filter_by(key_id=keyid, character_id=character).first()

        char = Character.query.filter_by(id=character).first()
        if not char:
            char = Character(id=character, name=characters[character]['name'], owner=key.owner)
            db.session.add(char)
            db.session.commit()

            newmap = KeyCharacters(key_id=key.id, character_id=char.id)
            db.session.add(newmap)
            db.session.commit()

        if not mapping:
            mapping = KeyCharacters.query.filter_by(key_id=keyid, character_id=character).first()

        # We already know the character but not the mapping
        if char and not mapping:
            newmap = KeyCharacters(key_id=key.id, character_id=char.id)
            db.session.add(newmap)
            db.session.commit()

        updateCharacter.delay(character)


@celery.task()
def updateCharacter(charid):
    cache = MemcacheCache(app.config)
    character = Character.query.filter_by(id=charid).first()
    # Find a Key
    key = character.get_valid_api_key()
    if key:
        if key.status == STATUS_OK:
            # We have a valid key, let's update the character!
            api = evelink.api.API(cache=cache, api_key=(key.id, key.vcode))
            char = evelink.char.Char(char_id=character.id, api=api)
            eve = evelink.eve.EVE(api=api)
            sheet = char.character_sheet().result
            info = eve.character_info_from_id(char_id=character.id).result

            corp = Corporation.query.filter_by(id=sheet['corp']['id']).first()
            if not corp:
                # We need to add this corp to our db
                corp = Corporation(id=sheet['corp']['id'], name=sheet['corp']['name'])
                db.session.add(corp)
                db.session.commit()

                # We should fire an update of that corp now too
                updateCorpInfo.delay(corp.id)

            character.corpId = sheet['corp']['id']
            if "ship" in info and info['ship']['type_id']:
                character.lastKnownShip = info['ship']['type_id']
            db.session.add(character)
            db.session.commit()

            if sheet['alliance']['id']:
                # Character is in an alliance, let's see if we know about that alliance already!
                alliance = Alliance.query.filter_by(id=sheet['alliance']['id']).first()

                # We don't already know the alliance, so create it
                if not alliance:
                    alliance = Alliance(id=sheet['alliance']['id'], name=sheet['alliance']['name'])
                    db.session.add(alliance)
                    db.session.commit()

                    # We're going to fire an update of the alliance here
                    updateAllianceInfo.delay(alliance.id)

                # And let's update the corp's alliance affiliation at the same time
                corp.allianceId = alliance.id
                db.session.add(corp)
                db.session.commit()

            user = users.getUser(userid=character.owner)

            # Next, let's check if this person is a member of SIGH., and if so, let's give them the API group.
            if sheet['alliance']['id'] == app.config['ALLIANCE_ID']:

                # Check to see if the user is already in the group
                membership = GroupMember.query.filter_by(member_id=user.uid, app_status=APPLICATION_ACCEPTED,
                                                         group_id=app.config['ALLIANCE_API_GROUP_ID']).first()
                if not membership:
                    # Need to add
                    membership = GroupMember(member_id=user.uid, group_id=app.config['ALLIANCE_API_GROUP_ID'],
                                             app_status=APPLICATION_ACCEPTED)
                    db.session.add(membership)
                    db.session.commit()
                    logger.debug('Adding %s to SIGH.API' % (user.username,))

            # Let's check if we've set any rules for their corp id
            rules = ApiCorpRule.query.filter_by(corp_id=corp.id).all()
            if rules:
                for rule in rules:
                    if not rule.group_id in user.get_group_ids():
                        # They aren't already in the group, let's add them
                        grouptools.addUserToGroup(user, rule.get_group())

            return

    # If we're at this point, the key we tried wasn't valid. Oh dear...
    return

@celery.task()
def updateCorpInfo(corpid):
        corp = Corporation.query.filter_by(id=corpid).first()
        if corp:
            cache = MemcacheCache(app.config)
            api = evelink.api.API(cache=cache)
            corpapi = evelink.corp.Corp(api=api)
            sheet = corpapi.corporation_sheet(corp_id=corp.id).result

            # Update corp info now
            corp.ticker = sheet['ticker']
            corp.memberCount = sheet['members']['current']
            if sheet['alliance']['id']:
                corp.allianceId = sheet['alliance']['id']
            else:
                corp.allianceId = None

            # And save
            db.session.add(corp)
            db.session.commit()

@celery.task()
def updateAllianceInfo(allianceid):
    alliance = Alliance.query.filter_by(id=allianceid).first()
    if alliance:
        cache = MemcacheCache(app.config)
        api = evelink.api.API(cache=cache)
        eve = evelink.eve.EVE(api=api)
        alliances = eve.alliances().result

        alliance.ticker = alliances[alliance.id]['ticker']

        db.session.add(alliance)
        db.session.commit()
