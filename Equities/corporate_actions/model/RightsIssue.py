from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from Database.database import Base

class RightsIssue(Base):
    __tablename__ = 'rights_issue'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # corporate_action_id = Column(Integer, ForeignKey('corporate_action.id'), unique=True)

    announcement_date = Column(DateTime, nullable=False)
    offer_price = Column(Float, nullable=False)
    offer_ratio = Column(Float, nullable=False)
    record_date = Column(DateTime, nullable=False)
    subscription_start_date = Column(DateTime, nullable=False)
    subscription_end_date = Column(DateTime, nullable=False)
    total_shares_offered = Column(Float, nullable=False)
    use_of_proceeds = Column(String, nullable=True)

    # Relationship back reference
    # corporate_action = relationship("CorporateAction", backref="rights_issue")
    #

    def __init__(self, announcement_date: datetime, offer_price: float, offer_ratio: float,
                 record_date: datetime, subscription_start_date: datetime, subscription_end_date: datetime,
                 total_shares_offered: float, use_of_proceeds=None):
        self.announcement_date = announcement_date
        self.offer_price = offer_price
        self.offer_ratio = offer_ratio
        self.record_date = record_date
        self.subscription_start_date = subscription_start_date
        self.subscription_end_date = subscription_end_date
        self.total_shares_offered = total_shares_offered
        self.use_of_proceeds = use_of_proceeds

    def __repr__(self):
        return (f"RightsIssue(id={self.id}, announcement_date={self.announcement_date}, offer_price={self.offer_price}, "
                f"offer_ratio={self.offer_ratio}, record_date={self.record_date}, "
                f"subscription_start_date={self.subscription_start_date}, subscription_end_date={self.subscription_end_date}, "
                f"total_shares_offered={self.total_shares_offered}, use_of_proceeds={self.use_of_proceeds})")

