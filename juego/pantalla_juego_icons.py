"""Icon loading and management mixin for GameScreen.

This module contains the GameIconsMixin class which provides all icon loading
functionality for the game screen, including header icons, audio icons,
keyboard icons, and wildcard icons.
"""


class GameIconsMixin:
    """Mixin providing icon loading functionality for GameScreen.

    This mixin requires the following attributes to be present on the class:
    - image_handler: ImageHandler instance for loading icons
    - ICONS: dict mapping icon keys to icon paths
    - BASE_SIZES: dict with base size values
    - audio_enabled: bool for audio state
    - audio_toggle_btn: CTkButton for audio toggle

    All icon references (clock_icon, star_icon, etc.) are expected to be
    initialized to None before this mixin's methods are called.
    """

    def _load_icon(self, icon_key, size):
        """Load an icon from the ICONS dict at the specified size.

        Args:
            icon_key: Key in self.ICONS dict
            size: Size in pixels (icons are square)

        Returns:
            CTkImage or None if loading fails
        """
        return self.image_handler.create_ctk_icon(self.ICONS[icon_key], (size, size))

    def load_header_icons(self):
        """Load icons used in the header (clock, star, freeze)."""
        self.clock_icon = self._load_icon("clock", 24)
        self.star_icon = self._load_icon("star", 24)
        self.freeze_icon = self._load_icon("freeze", 24)

    def load_audio_icons(self):
        """Load audio toggle icons (volume on/off)."""
        sz = self.BASE_SIZES["audio_icon_base"]
        self.audio_icon_on = self._load_icon("volume_on", sz)
        self.audio_icon_off = self._load_icon("volume_off", sz)

    def load_info_icon(self):
        """Load the info icon for the definition section."""
        self.info_icon = self._load_icon("info", 24)

    def load_delete_icon(self):
        """Load the delete/backspace icon for the keyboard."""
        self.delete_icon = self._load_icon(
            "delete", self.BASE_SIZES["delete_icon_base"]
        )

    def load_lightning_icon(self, size=18):
        """Load the lightning icon for the charges display.

        Args:
            size: Icon size in pixels (default 18)
        """
        self.lightning_icon = self._load_icon("lightning", size)

    def load_freeze_wildcard_icon(self, size=28):
        """Load the freeze icon for the wildcard button.

        Args:
            size: Icon size in pixels (default 28)
        """
        self.freeze_wildcard_icon = self._load_icon("freeze", size)

    def update_audio_button_icon(self):
        """Update the audio toggle button icon based on audio_enabled state."""
        if not self.audio_toggle_btn:
            return
        icon = self.audio_icon_on if self.audio_enabled else self.audio_icon_off
        if icon:
            self.audio_toggle_btn.configure(image=icon, text="")
        else:
            self.audio_toggle_btn.configure(
                image=None, text="On" if self.audio_enabled else "Off"
            )
