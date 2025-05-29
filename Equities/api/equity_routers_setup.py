from Equities.api.corporate_action_crud_router import CorporateActionGenericRouter
from Equities.api.corporate_action_schema.cash_distribution.distribution_schema import DistributionRequest, \
    DistributionResponse
from Equities.api.corporate_action_schema.cash_distribution.dividend_schema import DividendRequest, DividendResponse
from Equities.api.corporate_action_schema.cash_distribution.return_of_capital_schema import ReturnOfCapitalRequest, \
    ReturnOfCapitalResponse
from Equities.api.corporate_action_schema.cash_distribution.special_dividend_schema import SpecialDividendRequest, \
    SpecialDividendResponse
from Equities.api.corporate_action_schema.corporate_restructuring.acquisition_schema import AcquisitionRequest, \
    AcquisitionResponse
from Equities.api.corporate_action_schema.corporate_restructuring.exchange_offer_schema import ExchangeOfferRequest, \
    ExchangeOfferResponse
from Equities.api.corporate_action_schema.corporate_restructuring.merger_schema import MergerRequest, MergerResponse
from Equities.api.corporate_action_schema.corporate_restructuring.tender_offer_schema import TenderOfferRequest, \
    TenderOfferResponse
from Equities.api.corporate_action_schema.delisting_and_reorganization.bankruptcy_schema import BankruptcyRequest, \
    BankruptcyResponse
from Equities.api.corporate_action_schema.delisting_and_reorganization.delisting_schema import DelistingRequest, \
    DelistingResponse
from Equities.api.corporate_action_schema.delisting_and_reorganization.liquidation_schema import LiquidationRequest, \
    LiquidationResponse
from Equities.api.corporate_action_schema.delisting_and_reorganization.reorganization_schema import \
    ReorganizationRequest, ReorganizationResponse
from Equities.api.corporate_action_schema.rights_and_warrants.rights_issue_schema import RightsIssueRequest, \
    RightsIssueResponse
from Equities.api.corporate_action_schema.rights_and_warrants.subscription_schema import SubscriptionRequest, \
    SubscriptionResponse
from Equities.api.corporate_action_schema.rights_and_warrants.warrent_exercise_schema import WarrantExerciseRequest, \
    WarrantExerciseResponse
from Equities.api.corporate_action_schema.stock_changes.reverse_split_schema import ReverseSplitRequest, \
    ReverseSplitResponse
from Equities.api.corporate_action_schema.stock_changes.spin_off_schema import SpinOffRequest, SpinOffResponse
from Equities.api.corporate_action_schema.stock_changes.stock_dividend_schema import StockDividendRequest, \
    StockDividendResponse
from Equities.api.corporate_action_schema.stock_changes.stock_split_schema import StockSplitRequest, StockSplitResponse
from Equities.api.equity_crud_router import EquityGenericRouter
from Equities.api.equity_schema.Equity_Schema import EquityRequest, EquityResponse
from Equities.corporate_actions.model.CorporateActionBase import CorporateActionBase
from Equities.corporate_actions.model.cash_distribution.Distribution import Distribution
from Equities.corporate_actions.model.cash_distribution.Dividend import Dividend
from Equities.corporate_actions.model.cash_distribution.ReturnOfCapital import ReturnOfCapital
from Equities.corporate_actions.model.cash_distribution.SpecialDividend import SpecialDividend
from Equities.corporate_actions.model.corporate_restructuring.Acquisition import Acquisition
from Equities.corporate_actions.model.corporate_restructuring.ExchangeOffer import ExchangeOffer
from Equities.corporate_actions.model.corporate_restructuring.Merger import Merger
from Equities.corporate_actions.model.corporate_restructuring.TenderOffer import TenderOffer
from Equities.corporate_actions.model.delisting_and_reorganization.Bankruptcy import Bankruptcy
from Equities.corporate_actions.model.delisting_and_reorganization.Delisting import Delisting
from Equities.corporate_actions.model.delisting_and_reorganization.Liquidation import Liquidation
from Equities.corporate_actions.model.delisting_and_reorganization.Reorganization import Reorganization
from Equities.corporate_actions.model.rights_and_warrants.RightsIssue import RightsIssue
from Equities.corporate_actions.model.rights_and_warrants.Subscription import Subscription
from Equities.corporate_actions.model.rights_and_warrants.WarrentExercise import WarrantExercise
from Equities.corporate_actions.model.stock_changes.ReverseSplit import ReverseSplit
from Equities.corporate_actions.model.stock_changes.SpinOff import SpinOff
from Equities.corporate_actions.model.stock_changes.StockDividend import StockDividend
from Equities.corporate_actions.model.stock_changes.StockSplit import StockSplit
from Equities.model.Equity import Equity

equity_router = EquityGenericRouter(
    model=Equity,
    create_schema=EquityRequest,
    response_schema=EquityResponse,
    base_path=Equity.API_Path,
    tags=["Equity"]
).router

dividend_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Dividend,
    create_schema=DividendRequest,
    response_schema=DividendResponse,
    base_path=Dividend.API_Path,
    tags=["Dividend"]
).router

special_dividend_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=SpecialDividend,
    create_schema=SpecialDividendRequest,
    response_schema=SpecialDividendResponse,
    base_path=SpecialDividend.API_Path,
    tags=["Special Dividend"]
).router

distribution_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Distribution,
    create_schema=DistributionRequest,
    response_schema=DistributionResponse,
    base_path=Distribution.API_Path,
    tags=["Distribution"]
).router

return_of_capital_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=ReturnOfCapital,
    create_schema=ReturnOfCapitalRequest,
    response_schema=ReturnOfCapitalResponse,
    base_path=ReturnOfCapital.API_Path,
    tags=["Return of Capital"]
).router

# Stock changes
stock_split_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=StockSplit,
    create_schema=StockSplitRequest,
    response_schema=StockSplitResponse,
    base_path=StockSplit.API_Path,
    tags=["Stock Split"]
).router

stock_dividend_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=StockDividend,
    create_schema=StockDividendRequest,
    response_schema=StockDividendResponse,
    base_path=StockDividend.API_Path,
    tags=["Stock Dividend"]
).router

reverse_split_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=ReverseSplit,
    create_schema=ReverseSplitRequest,
    response_schema=ReverseSplitResponse,
    base_path=ReverseSplit.API_Path,
    tags=["Reverse Split"]
).router

spin_off_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=SpinOff,
    create_schema=SpinOffRequest,
    response_schema=SpinOffResponse,
    base_path=SpinOff.API_Path,
    tags=["Spin-Off"]
).router

# Corporate restructuring
merger_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Merger,
    create_schema=MergerRequest,
    response_schema=MergerResponse,
    base_path=Merger.API_Path,
    tags=["Merger"]
).router

acquisition_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Acquisition,
    create_schema=AcquisitionRequest,
    response_schema=AcquisitionResponse,
    base_path=Acquisition.API_Path,
    tags=["Acquisition"]
).router

tender_offer_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=TenderOffer,
    create_schema=TenderOfferRequest,
    response_schema=TenderOfferResponse,
    base_path=TenderOffer.API_Path,
    tags=["Tender Offer"]
).router

exchange_offer_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=ExchangeOffer,
    create_schema=ExchangeOfferRequest,
    response_schema=ExchangeOfferResponse,
    base_path=ExchangeOffer.API_Path,
    tags=["Exchange Offer"]
).router

# Rights and warrants
rights_issue_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=RightsIssue,
    create_schema=RightsIssueRequest,
    response_schema=RightsIssueResponse,
    base_path=RightsIssue.API_Path,
    tags=["Rights Issue"]
).router

warrant_exercise_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=WarrantExercise,
    create_schema=WarrantExerciseRequest,
    response_schema=WarrantExerciseResponse,
    base_path=WarrantExercise.API_Path,
    tags=["Warrant Exercise"]
).router

subscription_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Subscription,
    create_schema=SubscriptionRequest,
    response_schema=SubscriptionResponse,
    base_path=Subscription.API_Path,
    tags=["Subscription"]
).router

# # Symbol changes
# identifier_change_router = CorporateActionGenericRouter(
#     base_model=CorporateActionBase,
#     model=IdentifierChange,
#     create_schema=IdentifierChangeRequest,
#     response_schema=IdentifierChangeResponse,
#     base_path=IdentifierChange.API_Path,
#     tags=["Identifier Change"]
# ).router

# Delistings and reorganizations
delisting_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Delisting,
    create_schema=DelistingRequest,
    response_schema=DelistingResponse,
    base_path=Delisting.API_Path,
    tags=["Delisting"]
).router

bankruptcy_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Bankruptcy,
    create_schema=BankruptcyRequest,
    response_schema=BankruptcyResponse,
    base_path=Bankruptcy.API_Path,
    tags=["Bankruptcy"]
).router

liquidation_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Liquidation,
    create_schema=LiquidationRequest,
    response_schema=LiquidationResponse,
    base_path=Liquidation.API_Path,
    tags=["Liquidation"]
).router

reorganization_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Reorganization,
    create_schema=ReorganizationRequest,
    response_schema=ReorganizationResponse,
    base_path=Reorganization.API_Path,
    tags=["Reorganization"]
).router
