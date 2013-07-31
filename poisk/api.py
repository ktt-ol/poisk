from flask import request, Blueprint, jsonify

from poisk.models import db, User, KeyTransaction

api = Blueprint('api', __name__)

@api.route('/v1/keyholder.json')
def keyholder():
    current_keyholder = User.query.join(User.keys).all()
    last_transaction = KeyTransaction.query.order_by(db.desc(KeyTransaction.start)).first()
    resp = jsonify(
        current_keyholder=[k.nick for k in current_keyholder if k.nick],
    )
    resp.date = last_transaction.start
    resp.add_etag()
    resp.make_conditional(request)
    return resp

