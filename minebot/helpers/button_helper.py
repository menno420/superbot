# button_helper.py
import discord
from discord.ui import View, Button

class SimpleButtonView(View):
    def __init__(self, buttons_info: list, timeout=60):
        super().__init__(timeout=timeout)
        for label, style, callback in buttons_info:
            button = Button(label=label, style=style)
            button.callback = callback
            self.add_item(button)

# Helper function to quickly create a simple button view
def create_button_view(buttons_info: list, timeout=60) -> View:
    """
    buttons_info: List of tuples (label, discord.ButtonStyle, callback_function)
    """
    return SimpleButtonView(buttons_info, timeout=timeout)
