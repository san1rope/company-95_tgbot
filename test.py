from tg_bot.misc.utils import Utils as Ut, AdditionalButtons


async def temp_func():
    additional_buttons = [AdditionalButtons(index=0, buttons={"skip": 0, "back": None})]
    markup = await Ut.get_markup(mtype="inline", lang="ru", key="messangers_availabilities",
                                 additional_buttons=additional_buttons)
    print(markup.inline_keyboard[0])
    print(markup.inline_keyboard[1])
