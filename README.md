# Чат-бот расписания ЮРГПУ (НПИ)

На момент написания доступен в [сообществе](https://vk.com/npi_schedule) ВКонтакте.

### Вопрос-ответ
**Q:** Как запустить у себя?
<br>
**A:** Включить в сообществе Longpoll, выбрать приём сообщений. Далее создать файл `.env` с содержимым:
```shell
VK_BOT_TOKEN=<токен сообщества>
```
После этого выполнить:
```shell
docker compose up --build
```

**Q:** Что-то работает неправильно, куда писать?
<br>
**A:** Создавай issue здесь или пиши разработчику в [ВК](https://vk.com/id560302519).

**Q:** Это говнокод.
<br>
**A:** Я знаю, солнышко. Если тебе это не нравится, то можешь исправить и прислать Pull request.
