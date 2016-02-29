import evelink
from nexus_auth import app
from nexus_auth.utils.eveapi import MemcacheCache

key = (3510511, "j6UvtizFyr4RZDHHwdLsjPJq3F6BjLyOuI3V9mJJNRR0ifs04uOuRVMnYxGg9KQ7")
cache = MemcacheCache(app.config)
api = evelink.api.API(cache=cache, api_key=key)
eve = evelink.eve.EVE(api=api)
char = evelink.char.Char(char_id=92272928, api=api)

sheet = char.character_sheet().result
info = eve.character_info_from_id(char_id=92272928).result

print "Pilot: %s " % (sheet['name'],)
print "Current Ship: %s (%s)" % (info['ship']['type_name'],info['ship']['name'])
print info['ship']
