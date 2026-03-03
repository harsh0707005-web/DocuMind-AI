"""Startup script for DocuMind AI server with output logging."""
import os
import sys
import logging

# Ensure we're running from the server directory
server_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(server_dir)
sys.path.insert(0, server_dir)

# Set up file logging
log_file = os.path.join(server_dir, "server.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("startup")
logger.info("Starting DocuMind AI server...")

try:
    import uvicorn
    logger.info("uvicorn imported OK")
    uvicorn.run("main:app", host="127.0.0.1", port=8003, log_level="info")
except Exception as e:
    logger.error(f"Failed to start server: {e}", exc_info=True)
