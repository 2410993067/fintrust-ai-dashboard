from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(32), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(32), nullable=False)
    mcc = db.Column(db.String(64), nullable=False, default="")
    original_description = db.Column(db.String(512), nullable=False)
    cleaned_description = db.Column(db.String(512), nullable=False)
    merchant = db.Column(db.String(256), nullable=False)
    merchant_group = db.Column(db.String(256), nullable=False)
    is_subscription = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Transaction {self.id} {self.amount} {self.merchant}>"
