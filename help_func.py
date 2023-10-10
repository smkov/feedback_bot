def split_message(text, message, bot):
    if len(text) > 900:
        for x in range(0, len(text), 900):
            await bot.send_message(chat_id=message.from_id, disable_web_page_preview=True,
                                   text='Бот не несет ответственности за содержание поста, а только читает документ, который ему прислали:\n\n' + text[
                                                                                                                                                  x:x + 900])
    else:
        await bot.send_message(chat_id=message.from_id, disable_web_page_preview=True,
                               text='Бот не несет ответственности за содержание поста, а только читает документ, который ему прислали:\n\n' + text)