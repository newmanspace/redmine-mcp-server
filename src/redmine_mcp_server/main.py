import logging
import os
import sys
from importlib.metadata import version, PackageNotFoundError
from starlette.middleware.trustedhost import TrustedHostMiddleware

"""
Main entry point for the MCP Redmine server.

This module uses FastMCP native streamable HTTP transport for MCP protocol
communication.
"""

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from .redmine_handler import mcp  # noqa: E402
from . import redmine_scheduler as scheduler  # noqa: E402
from . import subscriptions  # noqa: E402

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
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


def main():
    """Main entry point for the console script."""
    # Note: .env is already loaded during redmine_handler import
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
            subscriptions.init_subscription_manager()
            logger.info("Subscription manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize subscription manager: {e}")
        
        sync_enabled = os.getenv("WAREHOUSE_SYNC_ENABLED", "true").lower() == "true"
        if sync_enabled:
            try:
                logger.info("Initializing warehouse sync scheduler...")
                scheduler.init_scheduler()
                logger.info("Warehouse sync scheduler started")
            except Exception as e:
                logger.error(f"Failed to start sync scheduler: {e}")
                logger.warning("Continuing without sync scheduler")

    if transport == "stdio":
        mcp.settings.port = 0

    mcp.run(transport=transport)


if __name__ == "__main__":
    import signal
    import sys
    
    def signal_handler(sig, frame):
        """处理关闭信号"""
        logger.info("Shutting down...")
        scheduler.shutdown_scheduler()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()
