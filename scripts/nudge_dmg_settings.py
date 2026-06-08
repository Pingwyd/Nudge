"""DMG build settings for macOS release."""

import os

app_name = "Nudge"

# Where the .app is located
app_path = f"dist/{app_name}.app"

# Output DMG name
filename = f"dist/{app_name}.dmg"

# Volume icon
# icon = "nudge.icns"

# Size of the DMG window in Finder
format = "UDZO"
size = "200M"
compression_level = 9

# Files to include on the DMG
files = [app_path]
symlinks = {"Applications": "/Applications"}

# Badge icon on the DMG folder
badge_icon = "nudge.icns"

# Window settings
window_rect = ((100, 100), (600, 400))
icon_locations = {
    app_name: (140, 180),
    "Applications": (460, 180),
}
background = None
show_status_bar = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
show_icon_preview = False
show_item_info = False
default_view = "icon-view"
arrange_by = None
grid_offset = (0, 0)
grid_spacing = 100
scroll_position = (0, 0)
label_pos = "bottom"
text_size = 12
icon_size = 64
