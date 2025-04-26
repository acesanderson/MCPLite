from typing import Dict, Any, Optional
from MCPLite.messages.Notifications import MCPNotification


class InitializedNotification(MCPNotification):
    """
    This notification is sent from the client to the server after initialization has finished.
    """

    method: str = "notifications/initialized"
    params: Optional[Dict[str, Any]] = Field(
        default={}, description="Optional parameters for the notification"
    )


def create_minimal_initialized_notification() -> InitializedNotification:
    # Create a minimal notification
    notification = InitializedNotification()

    # Return the notification as a JSON string
    return notification


# Create and print the notification
if __name__ == "__main__":
    i = create_minimal_initialized_notification()
    print(i)
    print(i.model_dump_json(indent=2))
