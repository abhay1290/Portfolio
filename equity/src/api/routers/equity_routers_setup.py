from equity.src.api.corporate_action_schema.cash_distribution.distribution_schema import DistributionRequest, \
    DistributionResponse
from equity.src.api.corporate_action_schema.cash_distribution.dividend_schema import DividendRequest, DividendResponse
from equity.src.api.corporate_action_schema.cash_distribution.return_of_capital_schema import ReturnOfCapitalRequest, \
    ReturnOfCapitalResponse
from equity.src.api.corporate_action_schema.cash_distribution.special_dividend_schema import SpecialDividendRequest, \
    SpecialDividendResponse
from equity.src.api.corporate_action_schema.corporate_restructuring.acquisition_schema import AcquisitionRequest, \
    AcquisitionResponse
from equity.src.api.corporate_action_schema.corporate_restructuring.exchange_offer_schema import ExchangeOfferRequest, \
    ExchangeOfferResponse
from equity.src.api.corporate_action_schema.corporate_restructuring.merger_schema import MergerRequest, MergerResponse
from equity.src.api.corporate_action_schema.corporate_restructuring.tender_offer_schema import TenderOfferRequest, \
    TenderOfferResponse
from equity.src.api.corporate_action_schema.delisting_and_reorganization.bankruptcy_schema import BankruptcyRequest, \
    BankruptcyResponse
from equity.src.api.corporate_action_schema.delisting_and_reorganization.delisting_schema import DelistingRequest, \
    DelistingResponse
from equity.src.api.corporate_action_schema.delisting_and_reorganization.liquidation_schema import LiquidationRequest, \
    LiquidationResponse
from equity.src.api.corporate_action_schema.delisting_and_reorganization.reorganization_schema import \
    ReorganizationRequest, ReorganizationResponse
from equity.src.api.corporate_action_schema.rights_and_warrants.rights_issue_schema import RightsIssueRequest, \
    RightsIssueResponse
from equity.src.api.corporate_action_schema.rights_and_warrants.subscription_schema import SubscriptionRequest, \
    SubscriptionResponse
from equity.src.api.corporate_action_schema.rights_and_warrants.warrent_exercise_schema import WarrantExerciseRequest, \
    WarrantExerciseResponse
from equity.src.api.corporate_action_schema.stock_changes.reverse_split_schema import ReverseSplitRequest, \
    ReverseSplitResponse
from equity.src.api.corporate_action_schema.stock_changes.spin_off_schema import SpinOffRequest, SpinOffResponse
from equity.src.api.corporate_action_schema.stock_changes.stock_dividend_schema import StockDividendRequest, \
    StockDividendResponse
from equity.src.api.corporate_action_schema.stock_changes.stock_split_schema import StockSplitRequest, \
    StockSplitResponse
from equity.src.api.equity_schema.Equity_Schema import EquityRequest, EquityResponse
from equity.src.api.routers.corporate_action_crud_router import CorporateActionGenericRouter
from equity.src.api.routers.equity_crud_router import EquityGenericRouter
from equity.src.model.corporate_actions.model.CorporateActionBase import CorporateActionBase
from equity.src.model.corporate_actions.model.cash_distribution.Distribution import Distribution
from equity.src.model.corporate_actions.model.cash_distribution.Dividend import Dividend
from equity.src.model.corporate_actions.model.cash_distribution.ReturnOfCapital import ReturnOfCapital
from equity.src.model.corporate_actions.model.cash_distribution.SpecialDividend import SpecialDividend
from equity.src.model.corporate_actions.model.corporate_restructuring.Acquisition import Acquisition
from equity.src.model.corporate_actions.model.corporate_restructuring.ExchangeOffer import ExchangeOffer
from equity.src.model.corporate_actions.model.corporate_restructuring.Merger import Merger
from equity.src.model.corporate_actions.model.corporate_restructuring.TenderOffer import TenderOffer
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Bankruptcy import Bankruptcy
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Delisting import Delisting
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Liquidation import Liquidation
from equity.src.model.corporate_actions.model.delisting_and_reorganization.Reorganization import Reorganization
from equity.src.model.corporate_actions.model.rights_and_warrants.RightsIssue import RightsIssue
from equity.src.model.corporate_actions.model.rights_and_warrants.Subscription import Subscription
from equity.src.model.corporate_actions.model.rights_and_warrants.WarrentExercise import WarrantExercise
from equity.src.model.corporate_actions.model.stock_changes.ReverseSplit import ReverseSplit
from equity.src.model.corporate_actions.model.stock_changes.SpinOff import SpinOff
from equity.src.model.corporate_actions.model.stock_changes.StockDividend import StockDividend
from equity.src.model.corporate_actions.model.stock_changes.StockSplit import StockSplit
from equity.src.model.equity.Equity import Equity

equity_router = EquityGenericRouter(
    model=Equity,
    create_schema=EquityRequest,
    response_schema=EquityResponse,
    base_path=Equity.API_Path,

).router

dividend_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Dividend,
    create_schema=DividendRequest,
    response_schema=DividendResponse,
    base_path=Dividend.API_Path,

).router

special_dividend_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=SpecialDividend,
    create_schema=SpecialDividendRequest,
    response_schema=SpecialDividendResponse,
    base_path=SpecialDividend.API_Path,

).router

distribution_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Distribution,
    create_schema=DistributionRequest,
    response_schema=DistributionResponse,
    base_path=Distribution.API_Path,

).router

return_of_capital_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=ReturnOfCapital,
    create_schema=ReturnOfCapitalRequest,
    response_schema=ReturnOfCapitalResponse,
    base_path=ReturnOfCapital.API_Path,

).router

# Stock changes
stock_split_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=StockSplit,
    create_schema=StockSplitRequest,
    response_schema=StockSplitResponse,
    base_path=StockSplit.API_Path,

).router

stock_dividend_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=StockDividend,
    create_schema=StockDividendRequest,
    response_schema=StockDividendResponse,
    base_path=StockDividend.API_Path,

).router

reverse_split_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=ReverseSplit,
    create_schema=ReverseSplitRequest,
    response_schema=ReverseSplitResponse,
    base_path=ReverseSplit.API_Path,

).router

spin_off_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=SpinOff,
    create_schema=SpinOffRequest,
    response_schema=SpinOffResponse,
    base_path=SpinOff.API_Path,
).router

# Corporate restructuring
merger_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Merger,
    create_schema=MergerRequest,
    response_schema=MergerResponse,
    base_path=Merger.API_Path,

).router

acquisition_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Acquisition,
    create_schema=AcquisitionRequest,
    response_schema=AcquisitionResponse,
    base_path=Acquisition.API_Path,

).router

tender_offer_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=TenderOffer,
    create_schema=TenderOfferRequest,
    response_schema=TenderOfferResponse,
    base_path=TenderOffer.API_Path,

).router

exchange_offer_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=ExchangeOffer,
    create_schema=ExchangeOfferRequest,
    response_schema=ExchangeOfferResponse,
    base_path=ExchangeOffer.API_Path,

).router

# Rights and warrants
rights_issue_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=RightsIssue,
    create_schema=RightsIssueRequest,
    response_schema=RightsIssueResponse,
    base_path=RightsIssue.API_Path,

).router

warrant_exercise_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=WarrantExercise,
    create_schema=WarrantExerciseRequest,
    response_schema=WarrantExerciseResponse,
    base_path=WarrantExercise.API_Path,

).router

subscription_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Subscription,
    create_schema=SubscriptionRequest,
    response_schema=SubscriptionResponse,
    base_path=Subscription.API_Path,

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

).router

bankruptcy_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Bankruptcy,
    create_schema=BankruptcyRequest,
    response_schema=BankruptcyResponse,
    base_path=Bankruptcy.API_Path,

).router

liquidation_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Liquidation,
    create_schema=LiquidationRequest,
    response_schema=LiquidationResponse,
    base_path=Liquidation.API_Path,

).router

reorganization_router = CorporateActionGenericRouter(
    base_model=CorporateActionBase,
    model=Reorganization,
    create_schema=ReorganizationRequest,
    response_schema=ReorganizationResponse,
    base_path=Reorganization.API_Path,

).router
