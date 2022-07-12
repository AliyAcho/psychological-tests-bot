from django.db import models

# Create your models here.


class Test(models.Model):
    name = models.CharField(verbose_name="Название теста", max_length=300)
    description = models.TextField(verbose_name="Описани теста", blank=True)

    def __str__(self):
        return self.name


class Question(models.Model):
    text = models.TextField(verbose_name="Текст вопроса")
    serial_number = models.PositiveIntegerField(verbose_name="Номер вопроса")
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Относиться к тесту...")

    def __str__(self):
        return self.text


class Answer(models.Model):
    text = models.TextField(verbose_name="Текст ответа", blank=True)
    result = models.TextField(
        verbose_name="Текст который добавиться к результату тестирования при выборе этого ответа", blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Относиться к вопросу...")

    def __str__(self):
        return self.text

class TelegramUser(models.Model):
    chat_id = models.CharField(max_length=50, verbose_name="Идентификатор чата")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(
        blank=True, max_length=50, verbose_name="Фамилия")

    def __str__(self):
        return self.first_name + " " + self.last_name


class Result(models.Model):
    text = models.TextField(verbose_name="Результаты тестирования")
    test = models.ForeignKey(Test, verbose_name="Название теста", on_delete=models.CASCADE)
    complete = models.BooleanField(verbose_name="Тест пройден полностью?")
    user = models.ForeignKey(TelegramUser, verbose_name="Чей результат?", on_delete=models.CASCADE)
