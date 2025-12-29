"""
Protocol direction and intent enums.

These define the communication patterns between Controller and Host.
"""

from enum import Enum


class Direction(Enum):
    """
    Message direction based on ROLE (not language).

    - TO_HOST: Controller sends to Host (C++ -> Java today)
    - TO_CONTROLLER: Host sends to Controller (Java -> C++ today)

    If languages change (e.g., Rust controller, Python host),
    the directions remain the same.
    """

    TO_HOST = "to_host"
    TO_CONTROLLER = "to_ctrl"


class Intent(Enum):
    """
    Message intent - what the sender expects.

    - COMMAND: Fire-and-forget action (e.g., "play transport")
    - QUERY: Request expecting a RESPONSE (e.g., "get device list")
    - NOTIFY: State notification (e.g., "transport is now playing")
    - RESPONSE: Answer to a QUERY (e.g., "here's the device list")
    """

    COMMAND = "command"
    QUERY = "query"
    NOTIFY = "notify"
    RESPONSE = "response"
