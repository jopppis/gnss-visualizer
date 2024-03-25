"""UBX protocol library."""

import pyubx2


def get_full_ubx_msg_id(msg: pyubx2.UBXMessage) -> str:
    """Get full message ID.

    Construct full UBX message ID like UBX-NAV-PVT for pyubx2.UBXMessage.
    """
    return f"UBX-{pyubx2.UBX_MSGIDS[msg.msg_cls + msg.msg_id]}"
