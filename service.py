import os

import xbmc
import xbmcaddon
import xbmcgui


ADDON = xbmcaddon.Addon()
LANGUAGE_SETTING_ID = 'language'
LANG_STATE_FILE = 'last_language.txt'


class NLZietSettingsMonitor(xbmc.Monitor):
    """Monitor addon setting changes and notify on language switch."""

    def __init__(self):
        super().__init__()
        self._last_language = self._read_state()
        current = self._current_language()
        if self._last_language is None:
            self._last_language = current
            self._write_state(current)

    def _profile_dir(self):
        try:
            profile = xbmc.translatePath(ADDON.getAddonInfo('profile'))
        except Exception:
            profile = ''
        if profile and not os.path.exists(profile):
            try:
                os.makedirs(profile)
            except Exception:
                pass
        return profile

    def _state_path(self):
        profile = self._profile_dir()
        if not profile:
            return ''
        return os.path.join(profile, LANG_STATE_FILE)

    def _current_language(self):
        try:
            return ADDON.getSetting(LANGUAGE_SETTING_ID) or '0'
        except Exception:
            return '0'

    def _read_state(self):
        path = self._state_path()
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as handle:
                value = handle.read().strip()
            return value if value else None
        except Exception:
            return None

    def _write_state(self, value):
        path = self._state_path()
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(str(value))
        except Exception:
            pass

    def onSettingsChanged(self):
        try:
            current = self._current_language()
            previous = self._last_language

            # Keep state synced on every settings save.
            self._write_state(current)
            self._last_language = current

            if previous is not None and previous != current:
                message = ADDON.getLocalizedString(30117) or 'Restart Kodi to apply language changes'
                xbmcgui.Dialog().ok('NLZiet', message)
        except Exception as exc:
            xbmc.log(f'NLZiet settings monitor error: {exc}', xbmc.LOGDEBUG)


def run():
    monitor = NLZietSettingsMonitor()
    while not monitor.waitForAbort(1):
        pass


if __name__ == '__main__':
    run()
