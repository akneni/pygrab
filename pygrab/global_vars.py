class GlobalVars():
    Tor_Reconnect = None
    warning_settings = True

    def raiseWarning(cls, warning:str):
        if cls.warning_settings:
            print(warning)
            print("To stifle warnings, run pygrab.warn_settings(False)")