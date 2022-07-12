from django.contrib import admin
from .models import *
import nested_admin


# Register your models here.

class AnswerInline(nested_admin.NestedTabularInline):
    model = Answer
    extra = 0


class QuestionInline(nested_admin.NestedTabularInline):
    model = Question
    extra = 0
    sortable_field_name = "serial_number"
    inlines = [AnswerInline, ]


class TestAdmin(nested_admin.NestedModelAdmin):
    inlines = [QuestionInline]


admin.site.register(Test, TestAdmin)
admin.site.register(TelegramUser)
admin.site.register(Result)
