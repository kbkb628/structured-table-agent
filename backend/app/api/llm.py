from fastapi import APIRouter

from app.llm.factory import describe_llm_provider_diagnostics
from app.llm.factory import describe_llm_provider_resolution
from app.llm.factory import get_llm_client
from app.schemas.analysis_schema import LLMProviderSmokeResponse
from app.schemas.analysis_schema import LLMProviderStatusResponse

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/provider-status", response_model=LLMProviderStatusResponse)
def get_provider_status() -> LLMProviderStatusResponse:
    resolution = describe_llm_provider_resolution()
    return LLMProviderStatusResponse(
        **resolution,
        diagnostics=describe_llm_provider_diagnostics(resolution),
    )


@router.post("/provider-smoke", response_model=LLMProviderSmokeResponse)
def run_provider_smoke() -> LLMProviderSmokeResponse:
    resolution = describe_llm_provider_resolution()
    diagnostics = describe_llm_provider_diagnostics(resolution)
    payload = {
        "provider_resolution": LLMProviderStatusResponse(
            **resolution,
            diagnostics=diagnostics,
        ),
        "diagnostics": diagnostics,
    }

    try:
        client = get_llm_client()
        payload["client_type"] = type(client).__name__
        payload["analysis_goal"] = client.generate_analysis_goal(
            question="analyse sales by region",
            file_profile={
                "filename": "sales_orders.csv",
                "row_count": 10,
                "column_count": 3,
                "columns": [
                    {"name": "region", "type": "string"},
                    {"name": "sales_amount", "type": "number"},
                    {"name": "order_id", "type": "string"},
                ],
            },
            business_context=[
                {
                    "id": "metric_sales_amount",
                    "title": "metric_sales_amount",
                    "content": "sales_amount sum gives sales amount",
                },
                {
                    "id": "dimension_region",
                    "title": "dimension_region",
                    "content": "region can be used for regional comparison",
                },
            ],
        )
        payload["ok"] = True
    except Exception as exc:
        payload["ok"] = False
        payload["client_type"] = type(locals().get("client")).__name__ if "client" in locals() else None
        payload["error_type"] = type(exc).__name__
        payload["error_message"] = str(exc)

    return LLMProviderSmokeResponse(**payload)
