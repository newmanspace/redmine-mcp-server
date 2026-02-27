import logging
import os
import sys
from importlib.metadata import version, PackageNotFoundError

"""
Main entry point for the MCP Redmine server.
"""

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Import MCP from new location
from .mcp.server import mcp  # noqa: E402
# Scheduler import removed for cleaner startup  # noqa: E402
from .dws.services import subscription_service
try:
    from .scheduler.tasks import init_scheduler, shutdown_scheduler
except ImportError:
    init_scheduler = None
    shutdown_scheduler = None  # noqa: E402

logger = logging.getLogger(__name__)

def get_version() -> str:
    try:
        return version("redmine-mcp-server")
    except PackageNotFoundError:
        return "dev"

# Apply settings at module level
mcp.settings.host = os.getenv("SERVER_HOST", "0.0.0.0")
mcp.settings.port = int(os.getenv("SERVER_PORT", "8000"))
mcp.settings.stateless_http = True

# Export the Starlette/FastAPI app for testing and external use
app = mcp.streamable_http_app()

def main():
    """Main entry point for the console script."""
    server_version = get_version()
    logger.info(f"Redmine MCP Server v{server_version}")

    # Determine transport
    transport = "streamable-http"
    if len(sys.argv) > 1:
        transport = sys.argv[1]
    elif os.getenv("MCP_TRANSPORT"):
        transport = os.getenv("MCP_TRANSPORT")

    logger.info(f"Starting with transport: {transport}")

    # Initialize warehouse sync scheduler (only for HTTP transport)
    if transport == "streamable-http":
        # Initialize subscription manager
        try:
            subscription_service.init_subscription_manager()
            logger.info("Subscription manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize subscription manager: {e}")
        
        sync_enabled = os.getenv("WAREHOUSE_SYNC_ENABLED", "true").lower() == "true"
        if sync_enabled:
            try:
                logger.info("Initializing warehouse sync scheduler...")
                init_scheduler()
                logger.info("Warehouse sync scheduler started")
            except Exception as e:
                logger.error(f"Failed to start sync scheduler: {e}")
                logger.warning("Continuing without sync scheduler")

    if transport == "stdio":
        mcp.settings.port = 0

    mcp.run(transport=transport)

if __name__ == "__main__":
    import signal
    
    def signal_handler(sig, frame):
        """Handle shutdown signal"""
        logger.info("Shutting down...")
        shutdown_scheduler()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()
