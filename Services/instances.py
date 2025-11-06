# socketio_instance.py
from flask_socketio import SocketIO
from logger import Logger

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")

# Initialize custom logger
logger = Logger()


def emit_agent(channel: str, content: dict | str, log: bool = True) -> bool:
    """
    Emit a message through SocketIO to a given channel.

    Args:
        channel (str): The socket channel name.
        content (dict | str): The data/message to emit.
        log (bool): Whether to log the message. Defaults to True.

    Returns:
        bool: True if emission succeeded, False otherwise.
    """
    try:
        socketio.emit(channel, content)
        if log:
            logger.info(f"SOCKET {channel} MESSAGE: {content}")
        return True
    except Exception as e:
        logger.error(f"SOCKET {channel} ERROR: {str(e)}")
        return False
