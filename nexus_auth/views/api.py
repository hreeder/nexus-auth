from nexus_auth import app
from nexus_auth.models.eve import Corporation

from flask import request, abort, jsonify

@app.route('/api/v1/json/corp', methods=['POST'])
def getCorp():
    if "ticker" not in request.form:
        abort(400)

    corpticker = request.form['ticker']

    corp = Corporation.query.filter_by(ticker=corpticker).first_or_404()

    d_corp = {
        'name': corp.name,
        'id': corp.id,
        'ticker': corp.ticker
    }

    if corp.alliance:
        d_corp['alliance'] = {
            'name': corp.alliance.name,
            'id': corp.alliance.id,
            'ticker': corp.alliance.ticker
        }

    return jsonify(corp=d_corp)
