"""
FPGA Backend Stub
Currently NOT CONNECTED. Returns not_connected status.
When FPGA hardware is available, implement this class.
"""


class FPGABackend:
    """
    Stub FPGA backend. Returns 'not_connected' for all calls.
    Future implementation: connect to FPGA via PCIe/UART/AXI interface.
    """

    def __init__(self):
        self.status = "not_connected"
        self.error_message = "FPGA accelerator is not connected. Software inference is currently active."

    def predict(self, features) -> dict:
        return {
            "success": False,
            "backend": "fpga",
            "status": "not_connected",
            "error": self.error_message,
            "note": "FPGA hardware implementation is planned future work."
        }

    def get_status(self) -> dict:
        return {
            "backend": "fpga",
            "status": "not_connected",
            "message": self.error_message,
            "planned": True
        }
