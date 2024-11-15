from modes.modes import Mode
class ModeHandler:
    current_mode = None
    def __init__(self):
        self.current_mode = Mode.JARVIS
        self.modes = {
            f"Turn on {Mode.JARVIS.value} mode": (self.jarvis_mode, Mode.JARVIS),
            f"Turn on {Mode.TV.value} mode": (self.tv_mode, Mode.TV),
        }

    def handle_main_input(self, user_said: str):
        # Strip leading/trailing spaces
        cleaned_input = user_said.strip()
        if cleaned_input in self.modes:
            mode_function, mode_enum = self.modes[cleaned_input]
            self.current_mode = mode_enum  # Update the current_mode
            return mode_function()
        else:
            return "No valid mode command found."

    def jarvis_mode(self):
        self.current_mode = Mode.JARVIS
        return "Normal mode activated."

    def tv_mode(self):
        self.current_mode = Mode.TV
        return "TV mode activated."
    def glossaryck_mode(self):
        self.current_mode = Mode.GLOSSARYCK

