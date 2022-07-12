from django.shortcuts import render
from .models import *
from project.settings import BOT_TOKEN
import json
from telebot import TeleBot, types
from telebot.apihelper import ApiTelegramException
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

# Create your views here.

bot = TeleBot(BOT_TOKEN)

def save_user(chat_id, data):
    # Saving the user in the database
    if TelegramUser.objects.filter(chat_id=chat_id).count() == 0:
        first_name = data["message"]["chat"]["first_name"]
        if "last_name" in data["message"]["chat"]:
            last_name = data["message"]["chat"]["last_name"]
        else:
            last_name = ""
        user = TelegramUser.objects.create(chat_id=f"{chat_id}",
                                          first_name=f"{first_name}",
                                          last_name=f"{last_name}")
        user.save()

# menu command
def tests(chat_id):
    markup = types.InlineKeyboardMarkup()
    for test in Test.objects.order_by('pk'):
        btn = types.InlineKeyboardButton(text=f"{test.name}", callback_data=f"test {test.pk}")
        markup.add(btn)
    bot.send_message(chat_id, "Какой тест вы хотите пройти? При выборе теста откроется его описание. Затем, когда вы нажмете начать, предыдущая попытка будет удалена, если такая имеется.", reply_markup=markup)

# callback command
def test(chat_id, callback_data, callback_id, message_id):
    bot.answer_callback_query(callback_id, text="")
    markup = types.InlineKeyboardMarkup()
    data = callback_data.split(" ")
    test = get_object_or_404(Test, pk=int(data[1]))
    if len(data) == 2:
        text = f"<b>{test.name}</b>\n\n{test.description}"
        markup.add(types.InlineKeyboardButton(text="Начать", callback_data=f"test {test.pk} run"))
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="html")
    elif data[2] == 'run':
        if Result.objects.filter(test=get_object_or_404(Test, pk=int(data[1]))).filter(user=get_object_or_404(TelegramUser, chat_id=chat_id)).count() == 0:
            result = Result.objects.create(text="", test=get_object_or_404(Test, pk=int(data[1])), complete=False, user=get_object_or_404(TelegramUser, chat_id=chat_id))
            result.save()
        else:
            result = Result.objects.filter(test=get_object_or_404(Test, pk=int(data[1]))).filter(user=get_object_or_404(TelegramUser, chat_id=chat_id))[0]
            result.text = ""
            result.complete = False
            result.save()
        questions = Question.objects.filter(test=get_object_or_404(Test, pk=int(data[1]))).order_by('serial_number')
        question = questions[0]
        text = f"<b>{test.name}</b>\n\n<b>{question.serial_number + 1}/{questions.count()}</b>\n\n{question}"
        
        answers = Answer.objects.filter(question=question)
        for answer in answers:
            markup.add(types.InlineKeyboardButton(text=f"{answer.text}", callback_data=f"test {test.pk} {question.pk} {answer.pk} {question.serial_number} {questions.count()} {result.pk}"))
        bot.edit_message_text(text, chat_id, message_id, parse_mode="html", reply_markup=markup)
    elif len(data) == 7:
        answer = get_object_or_404(Answer, pk=int(data[3]))
        result = get_object_or_404(Result, pk=int(data[6]))
        result.text = result.text + "\n\n" + answer.result
        result.save()
        questions = Question.objects.filter(test=get_object_or_404(Test, pk=int(data[1]))).order_by('serial_number')
        question = questions[int(data[4])+1]
        text = f"<b>{test.name}</b>\n\n<b>{question.serial_number + 1}/{data[5]}</b>\n\n{question}"
        
        answers = Answer.objects.filter(question=question)
        for answer in answers:
            if questions[int(data[4])+1] == questions.last():
                markup.add(types.InlineKeyboardButton(text=f"{answer.text}", callback_data=f"test {test.pk} {question.pk} {answer.pk} {question.serial_number} {data[5]} {result.pk} end"))
            else:
                markup.add(types.InlineKeyboardButton(text=f"{answer.text}", callback_data=f"test {test.pk} {question.pk} {answer.pk} {question.serial_number} {data[5]} {result.pk}"))
        bot.edit_message_text(text, chat_id, message_id, parse_mode="html", reply_markup=markup)
    elif data[7] == 'end':
        answer = get_object_or_404(Answer, pk=int(data[3]))
        result = get_object_or_404(Result, pk=int(data[6]))
        result.text = result.text + "\n\n" + answer.result + "\n\nРезультаты, полученные без участия специалиста, не воспринимайте слишком серьезно."
        result.complete = True
        result.save()
        bot.edit_message_text(result.text, chat_id, message_id, parse_mode="html")
# menu command
def results(chat_id):
    markup = types.InlineKeyboardMarkup()
    if TelegramUser.objects.filter(chat_id=chat_id).count() == 1:
        user = get_object_or_404(TelegramUser, chat_id=chat_id)
        for result in Result.objects.filter(user=user):
            if result.complete:
                btn = types.InlineKeyboardButton(text=f"{result.test.name}", callback_data=f"result {result.pk}")
                markup.add(btn)
    if len(markup.to_dict()['inline_keyboard']) == 0:
        bot.send_message(chat_id, "Вы еще не прошли ни одного теста...")
    else:
        bot.send_message(chat_id, "Выберите чтобы просмотреть результат. Сохраняется только последняя попытка.", reply_markup=markup)

# callback command
def result(chat_id, pk, callback_id):
    if Result.objects.filter(id=pk).count() == 1:
        text = get_object_or_404(Result, pk=pk).text
        bot.answer_callback_query(callback_id, text="Ваш результат")
        bot.send_message(chat_id, text)

@csrf_exempt
def bot_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        if "message" in data:
            chat_id = data['message']['chat']['id']
            
            save_user(chat_id, data)

            # Recognize commands and respond to them
            if 'text' in data["message"]:
                if data["message"]["text"] == "/tests":
                    tests(chat_id)
                elif data["message"]["text"] == "/results":
                    results(chat_id)
        elif 'callback_query' in data:
            chat_id = data["callback_query"]["message"]["chat"]["id"]
            save_user(chat_id, data)
            callback_id = data["callback_query"]["id"]
            callback_data = data["callback_query"]["data"]
            # "test ..." or "result ..."
            if callback_data.split(" ")[0] == 'result':
                result(chat_id, callback_data.split(" ")[1], callback_id)
            elif callback_data.split(" ")[0] == 'test':
                message_id = data["callback_query"]["message"]["message_id"]
                test(chat_id, callback_data, callback_id, message_id)
    return render(request, 'bot/base.html', {})
