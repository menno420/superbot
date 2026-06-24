"""Ticket subsystem views — launcher, in-channel controls, and the hub panel."""

from __future__ import annotations

from views.tickets._shared import (
    TicketOpenModal,
    build_launcher_embed,
    build_welcome_embed,
    is_ticket_staff,
)
from views.tickets.confirm import TicketConfirmView, build_confirm_embed
from views.tickets.control import TicketControlView, build_control_view
from views.tickets.hub import TicketHubView, open_ticket_hub
from views.tickets.launcher import TicketLauncherView, post_launcher

__all__ = [
    "TicketConfirmView",
    "TicketControlView",
    "TicketHubView",
    "TicketLauncherView",
    "TicketOpenModal",
    "build_confirm_embed",
    "build_control_view",
    "build_launcher_embed",
    "build_welcome_embed",
    "is_ticket_staff",
    "open_ticket_hub",
    "post_launcher",
]
