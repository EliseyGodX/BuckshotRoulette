from vk_api.keyboard import VkKeyboard, VkKeyboardColor



class Keyboard:

    def inventory(player: object) -> object:
        keyboard = VkKeyboard(one_time=True)
        for i, slot in enumerate(player.inventory):
            if i % 2 == 0 and i != 0: keyboard.add_line()
            keyboard.add_button(f'{i+1}. {slot}', color=VkKeyboardColor.SECONDARY)
        keyboard.add_button('-', color=VkKeyboardColor.NEGATIVE)
        return keyboard

    def shot() -> object:
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('В СЕБЯ', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_button('Противника', color=VkKeyboardColor.PRIMARY)
        return keyboard
    