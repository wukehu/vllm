# SPDX-License-Identifier: Apache-2.0
"""Stage-local pull routing for identical TP/PP layouts; no resharding."""


def matching_stage(local_size: int, local_rank: int, remote_size: int) -> tuple[int]:
    """Reject different PP degrees before selecting a remote stage."""
    if local_size < 1 or remote_size != local_size:
        raise ValueError("NIXL PP pull requires identical PP sizes")
    if not 0 <= local_rank < local_size:
        raise ValueError("Invalid local NIXL PP rank")
    return (local_rank,)


def validate_peer_stage(
    local_size: int,
    local_rank: int,
    local_tp: int,
    remote_tp: int,
    local_layers: tuple[int, int],
    remote_version: int,
    remote_size: int,
    remote_rank: int,
    remote_layers: tuple[int, int] | None,
) -> None:
    """Validate identity and geometry before registering peer memory."""
    matching_stage(local_size, local_rank, remote_size)
    if remote_version != 1:
        raise ValueError("Peer does not support NIXL PP pull layout v1")
    if local_tp != remote_tp:
        raise ValueError("NIXL PP pull requires identical TP sizes")
    if remote_rank != local_rank or remote_layers != local_layers:
        raise ValueError("NIXL PP pull layer partition mismatch")
    if local_layers[0] < 0 or local_layers[1] <= local_layers[0]:
        raise ValueError("Invalid NIXL PP layer interval")
