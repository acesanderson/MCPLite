"""
Our first actual client/server transport implementation.
"""

from pydantic import Json
from typing import Callable
from MCPLite.transport.Transport import Transport
from MCPLite.logs.logging_config import get_logger
import sys, json

# Get logger with this module's name
logger = get_logger(__name__)


class StdioClientTransport(Transport):
    """
    Client spawns and manages server processes, communicating with them via stdio.
    """

    def __init__(self, server_command: list[str]):
        """
        Initialize the transport with the command to start the server.
        Server_command should be a list of strings, where the first string is the command.
        """
        self.server_command = server_command
        self.process = None

    def start(self):
        """Start the server process with better error checking."""
        import subprocess
        import time

        try:
            # Start the server process
            self.process = subprocess.Popen(
                self.server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Give the process a moment to start
            time.sleep(0.1)

            # Check if it started successfully
            if self.process.poll() is not None:
                # Process has already terminated
                return_code = self.process.returncode
                stderr_output = (
                    self.process.stderr.read() if self.process.stderr else ""
                )
                stdout_output = (
                    self.process.stdout.read() if self.process.stdout else ""
                )

                raise RuntimeError(
                    f"Server process failed to start (exit code: {return_code}). "
                    f"Command: {' '.join(self.server_command)}. "
                    f"Stderr: {stderr_output}. "
                    f"Stdout: {stdout_output}"
                )

            logger.info(f"Started server process with command: {self.server_command}")

        except FileNotFoundError as e:
            raise RuntimeError(
                f"Could not start server: {e}. Check that the command exists: {self.server_command}"
            )
        except PermissionError as e:
            raise RuntimeError(f"Permission denied starting server: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error starting server: {e}")

    #
    # def start(self):
    #     """
    #     Start the server process.
    #     """
    #     import subprocess
    #
    #     # Start the server process
    #     self.process = subprocess.Popen(
    #         self.server_command,
    #         stdin=subprocess.PIPE,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.PIPE,
    #         text=True,
    #     )
    #     if not self.process:
    #         logger.error("Failed to start server process.")
    #         raise RuntimeError("Failed to start server process.")
    #     else:
    #         logger.info(f"Started server process with command: {self.server_command}")
    #
    def stop(self):
        """
        Stop the server process.
        """
        if self.process:
            self.process.terminate()
            self.process.wait()
            logger.info("Stopped server process.")
        else:
            logger.warning("No server process to stop.")

    def send_json_message(self, json_str: str) -> Json:
        """
        Send a JSON message to the server process and return the response.
        """
        if not self.process:
            logger.error("Server process is not running.")
            raise RuntimeError("Server process is not running.")
        if not self.process.stdin:
            logger.error("Server process stdin is not available.")
            raise RuntimeError("Server process stdin is not available.")
        if not self.process.stdout:
            logger.error("Server process stdout is not available.")
            raise RuntimeError("Server process stdout is not available.")
        self.process.stdin.write(json_str + "\n")
        self.process.stdin.flush()
        # Read the response from the server
        response = self.process.stdout.readline().strip()
        if response:
            logger.info(f"Received JSON response from server: {response}")
            return response
        else:
            logger.info("No JSON response from server.")
            return None


class StdioServerTransport(Transport):
    """
    Server listens for JSON messages on stdin and sends responses to stdout.
    """

    def __init__(self):
        """
        Server uses the default stdin and stdout for communication.
        """
        self.stdin = sys.stdin
        self.stdout = sys.stdout

    def start(self):
        """
        Server just starts listening; no process to spawn.
        """
        pass

    def stop(self):
        pass

    def send_json_message(self, json_str: str) -> Json:
        """
        Server writes to its own stdout.
        """
        self.stdout.write(json_str + "\n")
        self.stdout.flush()

    def read_json_message(self) -> Json:
        """
        Read a JSON message from stdin.
        """
        line = self.stdin.readline().strip()
        if line:
            logger.info(f"Received JSON message: {line}")
            return line
        else:
            logger.info("No JSON message received.")
            return None

    def run_server_loop(self, message_handler: Callable):
        """
        Run the server loop, listening for JSON messages on stdin.
        The message_handler should be a callable that takes a JSON string and returns a JSON string; i.e. server.process_message.
        """
        while True:
            try:
                line = self.read_json_message()
                # Check for EOF
                if not line:
                    break

                # Skip empty lines
                line = line.strip()
                if not line:
                    continue

                # Process the JSON message
                response_json = message_handler(line)

                # Only send a response if the handler returns a value
                if response_json:
                    self.send_json_message(response_json)
            except KeyboardInterrupt:
                break
            except Exception as e:
                error_json = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32603,
                            "message": str(e),
                        },
                    }
                )
                self.send_json_message(error_json)
