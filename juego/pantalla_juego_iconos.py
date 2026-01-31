class GameIconsMixin:

    def _load_icon(self, icon_key, size):
        return self.image_handler.create_ctk_icon(self.ICONS[icon_key], (size, size))

    def load_header_icons(self):
        self.clock_icon = self._load_icon("clock", 24)
        self.star_icon = self._load_icon("star", 24)
        self.freeze_icon = self._load_icon("freeze", 24)

    def load_audio_icons(self):
        sz = self.BASE_SIZES["audio_icon_base"]
        self.audio_icon_on = self._load_icon("volume_on", sz)
        self.audio_icon_off = self._load_icon("volume_off", sz)

    def load_info_icon(self):
        self.info_icon = self._load_icon("info", 24)

    def load_delete_icon(self):
        self.delete_icon = self._load_icon(
            "delete", self.BASE_SIZES["delete_icon_base"]
        )

    def load_lightning_icon(self, size=18):
        self.lightning_icon = self._load_icon("lightning", size)

    def load_freeze_wildcard_icon(self, size=28):
        self.freeze_wildcard_icon = self._load_icon("freeze", size)

    def update_audio_button_icon(self):
        if not self.audio_toggle_btn:
            return
        icon = self.audio_icon_on if self.audio_enabled else self.audio_icon_off
        if icon:
            self.audio_toggle_btn.configure(image=icon, text="")
        else:
            self.audio_toggle_btn.configure(
                image=None, text="On" if self.audio_enabled else "Off"
            )
