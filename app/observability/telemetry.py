import os
from logging import getLogger

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.observability.metrics import create_metrics, record_instrumentation_failure

logger = getLogger(__name__)


def get_environment() -> str:
    """Get environment - prefers OTEL_ENVIRONMENT but falls back to ENV."""
    return os.getenv("OTEL_ENVIRONMENT", os.getenv("ENV", "dev"))


def init_telemetry(app=None, sqlalchemy_engine=None):
    """
    Initialize traces + metrics and instrument common libraries.
    - app: FastAPI app instance (optional). If provided, FastAPIInstrumentor.instrument_app(app) is called.
    - sqlalchemy_engine: optional SQLAlchemy engine to instrument (pass engine when supported).
    """
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip() or None
    service_name = os.getenv("OTEL_SERVICE_NAME", "fastapi-app")
    service_version = os.getenv("OTEL_SERVICE_VERSION", "0.0.1")
    environment = get_environment()

    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": environment,
        }
    )

    # Traces
    tp = TracerProvider(resource=resource)
    trace.set_tracer_provider(tp)
    if otlp_endpoint:
        span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        tp.add_span_processor(BatchSpanProcessor(span_exporter))

    # Metrics - OTLP exporter optional
    if otlp_endpoint:
        metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        metric_reader = PeriodicExportingMetricReader(
            metric_exporter, export_interval_millis=5000
        )
        mp = MeterProvider(resource=resource, metric_readers=[metric_reader])
    else:
        # Create a MeterProvider so metric API works locally; no exporter
        mp = MeterProvider(resource=resource, metric_readers=[])

    metrics.set_meter_provider(mp)

    # NOW create the metrics (after provider is set)
    create_metrics()

    # Instrument common libraries
    AsyncioInstrumentor().instrument()
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    if sqlalchemy_engine is not None:
        try:
            SQLAlchemyInstrumentor().instrument(engine=sqlalchemy_engine)
        except Exception as e:
            logger.warning(
                f"SQLAlchemy auto-instrumentation failed: {e}. "
                "Use app.observability.db_metrics.db_timed for manual DB timing."
            )
            record_instrumentation_failure("sqlalchemy")

    # FastAPI instrumentation: instrument app instance if supplied
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)

    return {"tracer_provider": tp, "meter_provider": mp}
