"""Single append-only manifest of feature modules that register themselves
(task types, render overlays, HUD lines) as an import side effect. Each
build-order ticket adds its module here as one line - this file, not
game.py or world.py, is the extension point for new task types/overlays."""

import gather_task  # noqa: F401
import expand_task  # noqa: F401
import build_task  # noqa: F401
import render_buildings  # noqa: F401
import destroy_task  # noqa: F401
import magic  # noqa: F401
import render_magic  # noqa: F401
import farmland_task  # noqa: F401
import wildlife  # noqa: F401
import hunt_task  # noqa: F401
import tame_task  # noqa: F401
import spoilage  # noqa: F401
import onboarding_hints  # noqa: F401
