class Warning():
    warning_settings = True

    @classmethod
    def raiseWarning(cls, warning:str):
        if cls.warning_settings:
            print(warning)
            print("To stifle warnings, run pygrab.warn_settings(False)")