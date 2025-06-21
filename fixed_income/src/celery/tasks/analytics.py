from datetime import date

from fixed_income.src.celery.app import celery_app
from fixed_income.src.database import SessionLocal
from fixed_income.src.model.analytics.BondAnalyticsFactory import bond_analytics_factory
from fixed_income.src.model.analytics.model.BaseAnalyticsModel import BondAnalyticsModel
from fixed_income.src.utils.helpers import to_string
from fixed_income.src.utils.model_mappers import bond_model_factory


def process_bond_analytics(bond, db_session):
    if bond.maturity_date < date.today():
        return  # Skip expired bond

    analytics = bond_analytics_factory(bond)
    summary = analytics.summary()

    record = BondAnalyticsModel(
        bond_id=bond.id,
        analytics_date=date.today(),
        bond_type=bond.bond_type,

        clean_price=analytics.clean_price(),
        dirty_price=analytics.dirty_price(),
        accrued_interest=analytics.accrued_interest(),

        ytm=analytics.yield_to_maturity(),
        ytw=analytics.yield_to_worst(),

        duration_mod=analytics.modified_duration(),
        duration_mac=analytics.macaulay_duration(),
        duration_simple=analytics.simple_duration(),

        convexity=analytics.convexity(),
        dv01=analytics.dv01(),

        summary=to_string(summary)
    )
    db_session.merge(record)
    db_session.commit()


# celery -A celery_app.celery_app worker --loglevel=info
@celery_app.task(name="FixedIncome.tasks.analytics.compute_bond_analytics")
def compute_bond_analytics(bond_id: int, bond_type: str):
    # create this function to return model class
    db = SessionLocal()
    try:
        bond_model = bond_model_factory(bond_type)
        bond = db.query(bond_model).get(bond_id)
        if bond:
            process_bond_analytics(bond, db)
    finally:
        db.close()

# TODO auto update all bond analytics
# celery -A celery_app.celery_app beat --loglevel=info

# @celery_app.task
# def update_all_bonds(db: get_db()):
#     bonds = db.query(BondModel).all()
#     for bond in bonds:
#         process_bond_analytics(bond, db)
#     db.close()
