from datetime import datetime


from CorporateActions.CorporateAction import CorporateAction
from CorporateActions.CorporateActionEnum import CorporateActionEnum
from CorporateActions.Definitions.SpecialDividend import SpecialDividend
from CorporateActions.Definitions.StockDividend import StockDividend
from CorporateActions.Definitions.StockSplit import StockSplit
from CorporateActions.Definitions.RightsIssue import RightsIssue
from CorporateActions.StatusEnum import StatusEnum
from Currency.CurrencyEnum import CurrencyEnum
from Equities.Equity import Equity
from Identifier.AssetClassEnum import AssetClassEnum
from Identifier.IdentifierTypeEnum import IdentifierTypeEnum
from Identifier.SecurityIdentifier import SecurityIdentifier
from Identifier.TaxTypeEnum import TaxTypeEnum
from Identifier.WeightingMethodologyEnum import WeightingMethodologyEnum
from Portfolios.Portfolio import Portfolio

from database2 import Database, Base
from CorporateActions.Definitions.CashDividend import CashDividend

# Database connection string
DATABASE_URL = "postgresql+psycopg2://postgres:HippO1290@localhost:4200/postgres"

# Initialize the database
db = Database(DATABASE_URL, echo=True)

# Debug after creation
print("Registered tables after creation:", Base.metadata.tables.keys())

# Adding a record
session = db.get_session()
portfolio = Portfolio(
    symbol = "Portfolio7",
    currency = CurrencyEnum.USD,
    asset_class = AssetClassEnum.EQUITY,
    tax_type = TaxTypeEnum.GROSS,
    weighting_methodology = WeightingMethodologyEnum.PRICE
)
session.add(portfolio)
session.commit()

#Adding a record
session = db.get_session()
equity = Equity(
    symbol=SecurityIdentifier(IdentifierTypeEnum.RIC, "REC"),
    company_name="Apple Inc.",
    price=145.30,
    volume=100000,
    sector="Technology",
    industry="Consumer Electronics",
    currency=CurrencyEnum.USD
)
session.add(equity)
session.commit()

session = db.get_session()
ca = CorporateAction("Apple",
                     CorporateActionEnum.CASH_DIVIDEND,
                     datetime(2025, 1, 20),
                     datetime(2025, 2, 1),
                     CurrencyEnum.USD,
                     StatusEnum.OPEN,
                     "d")
ca.equity = equity
session.add(ca)
session.commit()

session = db.get_session()
new_dividend = CashDividend(
    dividend_amount=3.5,
    declaration_date=datetime(2025, 1, 15),
    ex_dividend_date=datetime(2025, 1, 18),
    record_date=datetime(2025, 1, 20),
    payment_date=datetime(2025, 2, 1),
)
new_dividend.corporate_action = ca
session.add(new_dividend)
session.commit()

session = db.get_session()
ca1 = CorporateAction("IBM",
                     CorporateActionEnum.SPECIAL_DIVIDEND,
                     datetime(2025, 1, 20),
                     datetime(2025, 2, 1),
                     CurrencyEnum.EUR,
                     StatusEnum.OPEN,
                     "d")

ca1.equity = equity
session.add(ca1)
session.commit()

session = db.get_session()
new_dividend1 = SpecialDividend(
    dividend_amount=3.5,
    declaration_date=datetime(2025, 1, 15),
    ex_dividend_date=datetime(2025, 1, 18),
    record_date=datetime(2025, 1, 20),
    payment_date=datetime(2025, 2, 1),
)
new_dividend1.corporate_action = ca1
session.add(new_dividend1)
session.commit()

session = db.get_session()
ca1 = CorporateAction("TESLA",
                     CorporateActionEnum.STOCK_DIVIDEND,
                     datetime(2025, 1, 20),
                     datetime(2025, 2, 1),
                     CurrencyEnum.EUR,
                     StatusEnum.OPEN,
                     "d")
ca1.equity = equity
session.add(ca1)
session.commit()

session = db.get_session()
new_dividend1 = StockDividend(
    dividend_rate=0.4,
    declaration_date=datetime(2025, 1, 15),
    ex_dividend_date=datetime(2025, 1, 18),
    record_date=datetime(2025, 1, 20),
    payment_date=datetime(2025, 2, 1),
)
new_dividend1.corporate_action = ca1
session.add(new_dividend1)
session.commit()

session = db.get_session()
ca1 = CorporateAction("NVIDIA",
                     CorporateActionEnum.STOCK_SPLIT,
                     datetime(2025, 1, 20),
                     datetime(2025, 2, 1),
                     CurrencyEnum.EUR,
                     StatusEnum.OPEN,
                     "d")
ca1.equity = equity
session.add(ca1)
session.commit()

session = db.get_session()
new_dividend1 = StockSplit(
    split_rate=0.4,
    declaration_date=datetime(2025, 1, 15),
    ex_dividend_date=datetime(2025, 1, 18),
    record_date=datetime(2025, 1, 20),
    payment_date=datetime(2025, 2, 1),
)
new_dividend1.corporate_action = ca1
session.add(new_dividend1)
session.commit()

session = db.get_session()
ca1 = CorporateAction("ENRON",
                     CorporateActionEnum.RIGHTS_ISSUE,
                     datetime(2025, 1, 20),
                     datetime(2025, 2, 1),
                     CurrencyEnum.EUR,
                     StatusEnum.OPEN,
                     "d")
ca1.equity = equity
session.add(ca1)
session.commit()

session = db.get_session()
rights_issue_example = RightsIssue(
    announcement_date=datetime(2025, 1, 19),
    offer_price=100.50,
    offer_ratio=0.25,
    record_date=datetime(2025, 2, 1),
    subscription_start_date=datetime(2025, 2, 5),
    subscription_end_date=datetime(2025, 2, 15),
    total_shares_offered=1000000.0,
    use_of_proceeds="Expansion of operations"
)

rights_issue_example.corporate_action = ca1
session.add(rights_issue_example)
session.commit()


# Query the database
# dividends = session.query(CashDividend).all()
# for dividend in dividends:
#     print(dividend)
