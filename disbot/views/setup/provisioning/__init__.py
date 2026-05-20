"""Provisioning UI adapters — Track 3 PR 7.

Two panels that surface the
:class:`~services.resource_provisioning.ResourceProvisioningPipeline`
through the standard
:class:`~disbot.views.base.BaseView` shell:

* :class:`~disbot.views.setup.provisioning.preview_panel.PreviewPanelView`
  — renders ``pipeline.preview(...)`` output and offers Apply / Cancel
  buttons.
* :class:`~disbot.views.setup.provisioning.confirm_panel.ConfirmPanelView`
  — runs ``pipeline.provision(..., confirmed=True)`` on construction
  and renders the :class:`ProvisioningResult`.

Both panels are pure orchestration — they neither write to the DB nor
call ``guild.create_*``. Every mutation goes through the pipeline so
audit / cache invalidation / event emission stay intact.
"""

from views.setup.provisioning.confirm_panel import (
    ConfirmPanelView,
    build_confirm_embed,
)
from views.setup.provisioning.preview_panel import (
    PreviewPanelView,
    build_preview_embed,
)

__all__ = [
    "ConfirmPanelView",
    "PreviewPanelView",
    "build_confirm_embed",
    "build_preview_embed",
]
