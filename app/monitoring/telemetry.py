"""OpenTelemetry tracing setup."""

import structlog

from app.config import Settings, get_settings

logger = structlog.get_logger()
_tracer = None


def setup_telemetry(settings: Settings | None = None) -> None:
    """Initialize OpenTelemetry tracing if enabled."""
    global _tracer
    settings = settings or get_settings()

    if not settings.otel_enabled:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider

        trace.set_tracer_provider(TracerProvider())
        _tracer = trace.get_tracer(settings.otel_service_name)
        logger.info("telemetry_disabled", mode="no-op-tracer")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(settings.otel_service_name)
        logger.info("telemetry_initialized", endpoint=settings.otel_exporter_otlp_endpoint)
    except Exception as exc:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider

        trace.set_tracer_provider(TracerProvider())
        _tracer = trace.get_tracer(settings.otel_service_name)
        logger.warning("telemetry_fallback", reason=str(exc))


def get_tracer():
    """Get the configured tracer instance."""
    global _tracer
    if _tracer is None:
        setup_telemetry()
    from opentelemetry import trace

    return _tracer or trace.get_tracer("ai-agent-platform")


def get_current_trace_id() -> str | None:
    """Return the active OpenTelemetry trace ID as a 32-char hex string."""
    from opentelemetry import trace

    ctx = trace.get_current_span().get_span_context()
    if ctx.is_valid:
        return format(ctx.trace_id, "032x")
    return None
