# app.py
import os
from flask import Flask, jsonify, request, abort
from models import db, Bank, Branch


def create_app():
    app = Flask(__name__)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "data.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    @app.route("/")
    def index():
        return {
            "message": "Bank API running",
            "endpoints": ["/health", "/banks", "/branches"]
        }
    @app.route("/health")
    def health():
        return jsonify(status="ok")

    @app.route("/banks", methods=["GET"])
    def list_banks():
        limit = min(int(request.args.get("limit", 100)), 1000)
        offset = int(request.args.get("offset", 0))
        q = request.args.get("q")
        qry = db.session.query(Bank)
        if q:
            qry = qry.filter(Bank.name.ilike(f"%{q}%"))
        total = qry.count()
        banks = qry.order_by(Bank.name).offset(offset).limit(limit).all()
        data = [{"id": b.id, "name": b.name} for b in banks]
        return jsonify(total=total, offset=offset, limit=limit, banks=data)

    @app.route("/banks/<int:bank_id>/branches", methods=["GET"])
    def branches_for_bank(bank_id):
        limit = min(int(request.args.get("limit", 100)), 1000)
        offset = int(request.args.get("offset", 0))
        q = request.args.get("q")
        qry = db.session.query(Branch).filter(Branch.bank_id == bank_id)
        if q:
            qry = qry.filter(Branch.branch.ilike(f"%{q}%"))
        total = qry.count()
        rows = qry.order_by(Branch.branch).offset(offset).limit(limit).all()
        data = []
        for r in rows:
            data.append({
                "ifsc": r.ifsc,
                "branch": r.branch,
                "address": r.address,
                "city": r.city,
                "district": r.district,
                "state": r.state,
                "micr": r.micr
            })
        return jsonify(total=total, offset=offset, limit=limit, branches=data)

    @app.route("/branches/<ifsc>", methods=["GET"])
    def branch_by_ifsc(ifsc):
        row = db.session.query(Branch).filter(Branch.ifsc == ifsc).first()
        if not row:
            abort(404, description="IFSC not found")
        # fetch bank name
        bank = db.session.query(Bank).get(row.bank_id)
        return jsonify(
            ifsc=row.ifsc,
            branch=row.branch,
            bank={"id": bank.id, "name": bank.name},
            address=row.address,
            city=row.city,
            district=row.district,
            state=row.state,
            micr=row.micr
        )

    @app.route("/branches", methods=["GET"])
    def search_branches():
        # support: ?ifsc=..., ?bank_name=..., ?city=..., ?q=
        ifsc = request.args.get("ifsc")
        bank_name = request.args.get("bank_name")
        city = request.args.get("city")
        q = request.args.get("q")
        limit = min(int(request.args.get("limit", 50)), 1000)
        offset = int(request.args.get("offset", 0))

        qry = db.session.query(Branch)
        if ifsc:
            qry = qry.filter(Branch.ifsc == ifsc)
        if city:
            qry = qry.filter(Branch.city.ilike(f"%{city}%"))
        if bank_name:
            qry = qry.join(Bank).filter(Bank.name.ilike(f"%{bank_name}%"))
        if q:
            qry = qry.filter((Branch.branch.ilike(f"%{q}%")) | (
                Branch.address.ilike(f"%{q}%")))

        total = qry.count()
        rows = qry.order_by(Branch.branch).offset(offset).limit(limit).all()
        results = []
        for r in rows:
            bank = db.session.query(Bank).get(r.bank_id)
            results.append({
                "ifsc": r.ifsc,
                "branch": r.branch,
                "bank": bank.name if bank else None,
                "address": r.address,
                "city": r.city,
                "district": r.district,
                "state": r.state,
                "micr": r.micr
            })
        return jsonify(total=total, offset=offset, limit=limit, branches=results)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
