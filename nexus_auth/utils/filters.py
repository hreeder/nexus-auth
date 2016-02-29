from nexus_auth import app
from nexus_auth.models.eve import EveItem
import re

from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@app.template_filter('display_pos')
def display_pos(itemid):
    pos = EveItem.get(itemid)

    if not pos:
        return False

    words = pos.name.split(" ")
    output = words[0] + " "
    
    if words[1] != "Control":
        output += words[1] + " "

    if words[-1] == "Tower":
        output += "Large"
    else:
        output += words[-1]

    return output

@app.template_filter('itemid2name')
def itemid_to_name(itemid):
    if type(itemid) != long:
        return itemid

    item = EveItem.get(itemid)

    if not item:
        return "Unrecognised ID"

    return item.name
