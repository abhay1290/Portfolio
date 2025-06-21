import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Type

from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, status
from fastapi.security import OAuth2PasswordBearer
from fixed_income.src.api.bond_schema.BondPriceSchema import (
    BondPriceRequest,
    BondPriceResponse
)
from pydantic import BaseModel

# Import all bond schemas using your existing imports
from fixed_income.src.api.bond_schema.CallableBondSchema import CallableBondRequest, CallableBondResponse
from fixed_income.src.api.bond_schema.FixedRateBondSchema import FixedRateBondRequest, FixedRateBondResponse
from fixed_income.src.api.bond_schema.FloatingRateBondSchema import FloatingRateBondRequest, FloatingRateBondResponse
from fixed_income.src.api.bond_schema.PutableBondSchema import PutableBondRequest, PutableBondResponse
from fixed_income.src.api.bond_schema.SinkingFundBondSchema import SinkingFundBondRequest, SinkingFundBondResponse
from fixed_income.src.api.bond_schema.ZeroCouponBondSchema import ZeroCouponBondRequest, ZeroCouponBondResponse
from fixed_income.src.controller.fixed_income_controller import FixedIncomeController, get_fixed_income_controller
from fixed_income.src.model.bonds import CallableBondModel, FixedRateBondModel, FloatingRateBondModel, PutableBondModel, \
    SinkingFundBondModel, ZeroCouponBondModel

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create the fixed income router
fixed_income_router = FastAPI(
    title="Dynamic Fixed Income Service with Controller",
    version="2.0.0",
    description="Microservice for bond and fixed income instrument management with dynamic schema loading",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)


# === Factory Functions (using your existing implementation) ===
def bond_schema_factory(bond_type: str):
    """Factory function to get the appropriate schema classes for a bond type"""
    schema_mapping = {
        'FIXED_COUPON': {
            'request': FixedRateBondRequest,
            'response': FixedRateBondResponse
        },
        'ZERO_COUPON': {
            'request': ZeroCouponBondRequest,
            'response': ZeroCouponBondResponse
        },
        'CALLABLE': {
            'request': CallableBondRequest,
            'response': CallableBondResponse
        },
        'PUTABLE': {
            'request': PutableBondRequest,
            'response': PutableBondResponse
        },
        'FLOATING': {
            'request': FloatingRateBondRequest,
            'response': FloatingRateBondResponse
        },
        'SINKING_FUND': {
            'request': SinkingFundBondRequest,
            'response': SinkingFundBondResponse
        }
    }

    if bond_type not in schema_mapping:
        raise ValueError(f"Unsupported bond_type: {bond_type}")

    return schema_mapping[bond_type]


def bond_model_factory(bond_type: str):
    """Factory function to get the appropriate bond model class"""
    mapping = {
        'FIXED_COUPON': FixedRateBondModel,
        'ZERO_COUPON': ZeroCouponBondModel,
        'CALLABLE': CallableBondModel,
        'PUTABLE': PutableBondModel,
        'FLOATING': FloatingRateBondModel,
        'SINKING_FUND': SinkingFundBondModel
    }
    try:
        return mapping[bond_type]
    except KeyError:
        raise ValueError(f"Unsupported bond_type: {bond_type}")


# === Helper Functions ===
SUPPORTED_BOND_TYPES = ['FIXED_COUPON', 'ZERO_COUPON', 'CALLABLE', 'PUTABLE', 'FLOATING', 'SINKING_FUND']


def validate_bond_type(bond_type: str) -> str:
    """Validate and return bond type"""
    bond_type_upper = bond_type.upper()
    if bond_type_upper not in SUPPORTED_BOND_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported bond type: {bond_type}. Supported types: {SUPPORTED_BOND_TYPES}"
        )
    return bond_type_upper


def get_bond_schemas(bond_type: str) -> Dict[str, Type[BaseModel]]:
    """Get request and response schemas for a bond type using factory"""
    bond_type = validate_bond_type(bond_type)
    try:
        return bond_schema_factory(bond_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


def get_request_schema(bond_type: str) -> Type[BaseModel]:
    """Get request schema for a bond type"""
    return get_bond_schemas(bond_type)["request"]


def get_response_schema(bond_type: str) -> Type[BaseModel]:
    """Get response schema for a bond type"""
    return get_bond_schemas(bond_type)["response"]


def get_bond_model(bond_type: str):
    """Get bond model class for a bond type"""
    bond_type = validate_bond_type(bond_type)
    try:
        return bond_model_factory(bond_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# === Bond Type Management ===
@fixed_income_router.get("/bond-types", response_model=List[str])
async def get_supported_bond_types(
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get list of supported bond types."""
    return SUPPORTED_BOND_TYPES


@fixed_income_router.get("/bond-types/summary", response_model=Dict[str, Any])
async def get_all_bond_types_summary(
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get summary statistics for all bond types."""
    return await controller.get_all_bond_types_summary()


@fixed_income_router.get("/bond-types/{bond_type}/schema")
async def get_bond_type_schema(
        bond_type: str = Path(..., description="Bond type"),
        token: str = Depends(oauth2_scheme)
):
    """Get schema information for a specific bond type."""
    bond_type = validate_bond_type(bond_type)
    schemas = get_bond_schemas(bond_type)
    model_class = get_bond_model(bond_type)

    return {
        "bond_type": bond_type,
        "request_schema": schemas["request"].model_json_schema(),
        "response_schema": schemas["response"].model_json_schema(),
        "model_class": model_class.__name__,
        "schema_title": f"{bond_type} Bond Schema"
    }


@fixed_income_router.get("/bond-types/{bond_type}/model-info")
async def get_bond_type_model_info(
        bond_type: str = Path(..., description="Bond type"),
        token: str = Depends(oauth2_scheme)
):
    """Get model information for a specific bond type."""
    bond_type = validate_bond_type(bond_type)
    model_class = get_bond_model(bond_type)

    return {
        "bond_type": bond_type,
        "model_class": model_class.__name__,
        "model_module": model_class.__module__,
        "model_fields": list(model_class.__annotations__.keys()) if hasattr(model_class, '__annotations__') else [],
        "table_name": getattr(model_class, '__tablename__', 'N/A')
    }


# === Core Bond CRUD Operations with Dynamic Schemas ===
@fixed_income_router.post("/{bond_type}/bonds", status_code=status.HTTP_201_CREATED)
async def create_bond_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        request: Dict[str, Any] = Body(..., description="Bond data"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Create a new bond instrument of specified type with dynamic schema validation."""
    bond_type = validate_bond_type(bond_type)

    # Get the appropriate schema and validate the request
    request_schema = get_request_schema(bond_type)

    try:
        # Validate request data against the appropriate schema
        validated_request = request_schema(**request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {bond_type} bond data: {str(e)}"
        )

    result = await controller.create_bond(
        bond_data=validated_request,
        bond_type=bond_type,
        user_token=token
    )

    return result


@fixed_income_router.get("/{bond_type}/bonds/{bond_id}")
async def get_bond_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_id: int = Path(..., description="Bond ID"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get a single bond instrument by ID and type with dynamic response schema."""
    bond_type = validate_bond_type(bond_type)

    bond = await controller.get_bond_by_id(bond_id, bond_type)
    if not bond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{bond_type} bond {bond_id} not found"
        )

    return bond


@fixed_income_router.get("/{bond_type}/bonds/symbol/{symbol}")
async def get_bond_by_symbol_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        symbol: str = Path(..., description="Bond symbol"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get bond instrument by symbol and type with dynamic response schema."""
    bond_type = validate_bond_type(bond_type)

    bond = await controller.get_bond_by_symbol(symbol, bond_type)
    if not bond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{bond_type} bond with symbol {symbol} not found"
        )

    return bond


@fixed_income_router.put("/{bond_type}/bonds/{bond_id}")
async def update_bond_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_id: int = Path(..., description="Bond ID"),
        request: Dict[str, Any] = Body(..., description="Bond data"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Update an existing bond instrument with dynamic schema validation."""
    bond_type = validate_bond_type(bond_type)

    # Get the appropriate schema and validate the request
    request_schema = get_request_schema(bond_type)

    try:
        # Validate request data against the appropriate schema
        validated_request = request_schema(**request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {bond_type} bond data: {str(e)}"
        )

    return await controller.update_bond(
        bond_id=bond_id,
        bond_data=validated_request,
        bond_type=bond_type,
        user_token=token
    )


@fixed_income_router.patch("/{bond_type}/bonds/{bond_id}")
async def partial_update_bond_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_id: int = Path(..., description="Bond ID"),
        request: Dict[str, Any] = Body(..., description="Partial bond data"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Partially update an existing bond instrument with dynamic schema validation."""
    bond_type = validate_bond_type(bond_type)

    # For partial updates, we validate only the provided fields
    # You might want to create a custom partial validation function

    return await controller.partial_update_bond(
        bond_id=bond_id,
        bond_data=request,  # Pass raw dict for partial updates
        bond_type=bond_type,
        user_token=token
    )


@fixed_income_router.delete("/{bond_type}/bonds/{bond_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bond_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_id: int = Path(..., description="Bond ID"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Delete a bond instrument with dynamic type validation."""
    bond_type = validate_bond_type(bond_type)

    success = await controller.delete_bond(
        bond_id=bond_id,
        bond_type=bond_type,
        user_token=token
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{bond_type} bond {bond_id} not found"
        )


# === Bond Bulk Operations with Dynamic Schemas ===
@fixed_income_router.post("/{bond_type}/bonds/bulk/create")
async def bulk_create_bonds_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bulk_request: List[Dict[str, Any]] = Body(..., description="List of bond data"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Create multiple bond instruments in bulk for a specific type with dynamic schema validation."""
    bond_type = validate_bond_type(bond_type)

    # Get the appropriate schema and validate all requests
    request_schema = get_request_schema(bond_type)
    validated_requests = []

    for i, bond_data in enumerate(bulk_request):
        try:
            validated_request = request_schema(**bond_data)
            validated_requests.append(validated_request)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid {bond_type} bond data at index {i}: {str(e)}"
            )

    return await controller.bulk_create_bonds(
        bulk_request=validated_requests,
        bond_type=bond_type,
        user_token=token
    )


@fixed_income_router.post("/bonds/bulk/create-mixed")
async def bulk_create_mixed_bonds_dynamic(
        bond_requests: List[Dict[str, Any]] = Body(..., description="List of {bond_type, bond_data} objects"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Create multiple bonds of different types in bulk with dynamic schema validation."""
    validated_requests = []

    for i, bond_request in enumerate(bond_requests):
        if "bond_type" not in bond_request or "bond_data" not in bond_request:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing bond_type or bond_data at index {i}"
            )

        bond_type = validate_bond_type(bond_request["bond_type"])
        bond_data = bond_request["bond_data"]

        # Get the appropriate schema and validate
        request_schema = get_request_schema(bond_type)

        try:
            validated_request = request_schema(**bond_data)
            validated_requests.append((bond_type, validated_request))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid {bond_type} bond data at index {i}: {str(e)}"
            )

    return await controller.bulk_create_mixed_bonds(validated_requests, token)


@fixed_income_router.post("/{bond_type}/bonds/bulk/get")
async def bulk_get_bonds_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_ids: List[int] = Body(..., description="List of bond IDs"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get multiple bond instruments by IDs for a specific type."""
    bond_type = validate_bond_type(bond_type)
    return await controller.get_bonds_bulk(bond_ids, bond_type)


@fixed_income_router.post("/{bond_type}/bonds/bulk/get-by-symbols")
async def bulk_get_bonds_by_symbols_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        symbols: List[str] = Body(..., description="List of bond symbols"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get multiple bond instruments by symbols for a specific type."""
    bond_type = validate_bond_type(bond_type)
    return await controller.get_bonds_by_symbols_bulk(symbols, bond_type)


# === Bond Listing and Search ===
@fixed_income_router.get("/{bond_type}/bonds")
async def get_bonds_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme),
        issuer: Optional[str] = Query(None, description="Filter by issuer"),
        currency: Optional[str] = Query(None, description="Filter by currency"),
        active_only: bool = Query(False, description="Get only active bonds"),
        order_by: str = Query("id", description="Order by field"),
        desc: bool = Query(False, description="Descending order"),
        start_date: Optional[datetime] = Query(None, description="Maturity start date filter"),
        end_date: Optional[datetime] = Query(None, description="Maturity end date filter")
):
    """Get list of bond instruments with optional filtering for a specific type."""
    bond_type = validate_bond_type(bond_type)

    if issuer:
        return await controller.get_bonds_by_issuer(issuer, bond_type)
    elif currency:
        return await controller.get_bonds_by_currency(currency, bond_type)
    elif start_date and end_date:
        return await controller.get_bonds_by_maturity_range(start_date, end_date, bond_type)
    elif active_only:
        return await controller.get_active_bonds(bond_type)
    else:
        return await controller.get_all_bonds(bond_type, order_by, desc)


@fixed_income_router.get("/{bond_type}/bonds/search/{search_term}")
async def search_bonds_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        search_term: str = Path(..., description="Search term"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Search bond instruments across multiple fields for a specific type."""
    bond_type = validate_bond_type(bond_type)
    return await controller.search_bonds(search_term, bond_type)


# === Bond Validation ===
@fixed_income_router.post("/{bond_type}/bonds/validate/exists", response_model=Dict[int, bool])
async def validate_bonds_exist_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_ids: List[int] = Body(..., description="List of bond IDs to validate"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Validate that multiple bonds exist for a specific type."""
    bond_type = validate_bond_type(bond_type)
    return await controller.validate_bonds_exist(bond_ids, bond_type)


@fixed_income_router.get("/{bond_type}/bonds/validate/{bond_id}/exists")
async def validate_bond_exists_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_id: int = Path(..., description="Bond ID"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Validate that a single bond exists for a specific type."""
    bond_type = validate_bond_type(bond_type)
    exists = await controller.validate_bond_exists(bond_id, bond_type)
    return {
        "bond_id": bond_id,
        "bond_type": bond_type,
        "exists": exists,
        "validated_at": datetime.now().isoformat()
    }


# === Price Operations ===
@fixed_income_router.get("/{bond_type}/bonds/{bond_id}/price/current", response_model=BondPriceResponse)
async def get_current_price_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_id: int = Path(..., description="Bond ID"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Get current price for a specific bond."""
    bond_type = validate_bond_type(bond_type)

    price = await controller.get_current_price(bond_id, bond_type)
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No current price available for {bond_type} bond {bond_id}"
        )
    return price


@fixed_income_router.post("/{bond_type}/bonds/{bond_id}/price/update", response_model=BondPriceResponse)
async def update_price_dynamic(
        bond_type: str = Path(..., description="Bond type"),
        bond_id: int = Path(..., description="Bond ID"),
        price: Decimal = Body(..., description="New price"),
        timestamp: Optional[datetime] = Body(None, description="Price timestamp"),
        source: str = Body("manual", description="Price source"),
        price_type: str = Body("clean", description="Price type (clean, dirty, yield)"),
        controller: FixedIncomeController = Depends(get_fixed_income_controller),
        token: str = Depends(oauth2_scheme)
):
    """Update price for a specific bond."""
    bond_type = validate_bond_type(bond_type)

    return await controller.update_price(
        bond_id=bond_id,
        bond_type=bond_type,
        price=price,
        timestamp=timestamp,
        source=source,
        price_type=price_type,
        user_token=token
    )


# === Advanced Typed Endpoints Generation ===
def create_typed_endpoints():
    """Create type-specific endpoints with proper schemas for better API documentation"""

    for bond_type in SUPPORTED_BOND_TYPES:
        try:
            schemas = bond_schema_factory(bond_type)
            request_schema = schemas["request"]
            response_schema = schemas["response"]
            model_class = bond_model_factory(bond_type)

            # Create a route tag for this bond type
            tag_name = f"{bond_type.lower().replace('_', '-')}-typed"

            # Create typed endpoint for bond creation
            async def create_typed_bond(
                    request_data: request_schema,
                    controller: FixedIncomeController = Depends(get_fixed_income_controller),
                    token: str = Depends(oauth2_scheme),
                    _bond_type: str = bond_type  # Capture in closure
            ):
                return await controller.create_bond(
                    bond_data=request_data,
                    bond_type=_bond_type,
                    user_token=token
                )

            # Register the typed endpoint
            fixed_income_router.add_api_route(
                path=f"/typed/{bond_type.lower()}/bonds",
                endpoint=create_typed_bond,
                methods=["POST"],
                response_model=response_schema,
                status_code=status.HTTP_201_CREATED,
                tags=[tag_name],
                summary=f"Create {bond_type} Bond (Typed)",
                description=f"Create a new {bond_type} bond with strongly typed schema validation"
            )

            # Create typed endpoint for bond retrieval
            async def get_typed_bond(
                    bond_id: int,
                    controller: FixedIncomeController = Depends(get_fixed_income_controller),
                    token: str = Depends(oauth2_scheme),
                    _bond_type: str = bond_type  # Capture in closure
            ):
                bond = await controller.get_bond_by_id(bond_id, _bond_type)
                if not bond:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"{_bond_type} bond {bond_id} not found"
                    )
                return bond

            # Register the typed retrieval endpoint
            fixed_income_router.add_api_route(
                path=f"/typed/{bond_type.lower()}/bonds/{{bond_id}}",
                endpoint=get_typed_bond,
                methods=["GET"],
                response_model=response_schema,
                tags=[tag_name],
                summary=f"Get {bond_type} Bond (Typed)",
                description=f"Retrieve a {bond_type} bond by ID with strongly typed response"
            )

        except Exception as e:
            logger.error(f"Failed to create typed endpoints for {bond_type}: {str(e)}")


# Initialize typed endpoints
create_typed_endpoints()


# === Health and Monitoring ===
@fixed_income_router.get("/health", response_model=Dict[str, Any])
async def health_check(
        controller: FixedIncomeController = Depends(get_fixed_income_controller)
):
    """Health check for the fixed income service with schema registry status."""
    health_result = await controller.health_check()

    # Add schema registry health information
    schema_registry_status = {}
    for bond_type in SUPPORTED_BOND_TYPES:
        try:
            schemas = bond_schema_factory(bond_type)
            model = bond_model_factory(bond_type)
            schema_registry_status[bond_type] = {
                "schemas_loaded": True,
                "model_loaded": True,
                "request_schema": schemas["request"].__name__,
                "response_schema": schemas["response"].__name__,
                "model_class": model.__name__
            }
        except Exception as e:
            schema_registry_status[bond_type] = {
                "schemas_loaded": False,
                "model_loaded": False,
                "error": str(e)
            }

    health_result.update({
        "supported_bond_types": SUPPORTED_BOND_TYPES,
        "schema_registry_status": schema_registry_status,
        "factory_functions": {
            "bond_schema_factory": "active",
            "bond_model_factory": "active"
        }
    })

    return health_result


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Example API Usage:
#
# 1. Dynamic Endpoints (flexible):
#    POST /FIXED_COUPON/bonds - Creates using FixedRateBondRequest schema
#    POST /ZERO_COUPON/bonds - Creates using ZeroCouponBondRequest schema
#
# 2. Typed Endpoints (type-safe):
#    POST /typed/fixed_coupon/bonds - Strongly typed in API docs
#    POST /typed/zero_coupon/bonds - Strongly typed in API docs
#
# 3. Schema Introspection:
#    GET /bond-types/FIXED_COUPON/schema - Returns schema definition
#    GET /bond-types/FIXED_COUPON/model-info - Returns model information
#
# 4. Health Check with Registry Status:
#    GET /health - Shows status of all schemas and models
