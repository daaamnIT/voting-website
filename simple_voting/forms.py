from django import forms
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms.widgets import Input
from django.views.generic.edit import FormView

from simple_voting.models import Voting
from simple_voting.forms import *
from simple_votings_11 import settings
from .models import *

class LoginFormView(FormView):
    form_class = AuthenticationForm

    template_name = "login.html"
    success_url = "/"

    def form_valid(self, form):
        self.user = form.get_user()
        login(self.request, self.user)
        return super(LoginFormView, self).form_valid(form)


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}), min_length=8)
    password2 = forms.CharField(label='Повторите', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': Input(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя', 'autofocus': ''}),
            'first_name': Input(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': Input(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': Input(attrs={'class': 'form-control', 'placeholder': 'Электронная почта'}),
        }

    def clean_password2(self):
        cd = self.data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают.')
        return cd['password2']

    def clean_username(self):
        cd = self.data
        if len(cd['username']) < 6:
            raise forms.ValidationError('Имя пользователя должно содержать 6 символов и более.')
        return cd['username']

    def clean_email(self):
        cd = self.data
        users = User.objects.all()
        for user in users:
            if user.email == cd['email']:
                raise forms.ValidationError('Эта электронная почта уже используется')
        return cd['email']


class VotingForm(forms.Form):
    question = forms.CharField(
        label='Вопрос',
        min_length=5,
        max_length=25,
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Вопрос', 'style': 'border-radius: 8px'})

    )
    description = forms.CharField(
        label='Дополнительное описание',
        max_length=255,
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'placeholder': 'Описание', 'style': 'border-radius: 8px'})
    )
    isSingle = forms.BooleanField(
        label='Один вариант ответа',
        required=False,
    )


class OptionForm(forms.Form):
    option = forms.CharField(
        label='Ответ',
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Ответ', 'style': 'border-radius: 8px', 'autofocus': ''})
    )


class VoteFormCheckBox(forms.Form):
    items = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'style': ''}), )


class LikeForm(forms.Form):
    like = forms.BooleanField(required=False, label='Добавить в избранное: ')


class CommentForm(forms.Form):
    comment = forms.CharField(
        label='Обсудите опрос здесь:',
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'placeholder': 'Описание', 'style': 'border-radius: 8px'}),
        required=False
    )


class ChangeInfoForm(forms.Form):

    username = forms.CharField(label='Имя пользователя', min_length=3, required=False)
    first_name = forms.CharField(label='Имя', min_length=3, required=False)
    last_name = forms.CharField(label='Фамилия', min_length=3, required=False)
    email = forms.EmailField(label='Электронная почта', required=False)
    old_password = forms.CharField(label='Старый пароль', widget=forms.PasswordInput, required=False, initial=None)
    new_password = forms.CharField(label='Новый пароль', widget=forms.PasswordInput, min_length=8, required=False,
                                   initial=None)
    new_password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput, required=False, initial=None)
    old_password_flag = True

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        widgets = {
            'username': Input(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя', 'autofocus': ''}),
            'first_name': Input(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': Input(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': Input(attrs={'class': 'form-control', 'placeholder': 'Электронная почта'}),
        }

    def set_old_password_flag(self):
        self.old_password_flag = False

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not old_password and self.data.get('new_password'):
            print('Not')
            raise forms.ValidationError("Вы должны ввести Ваш старый пароль.")
        if self.old_password_flag is False:
            raise forms.ValidationError("Старый пароль, который Вы ввели, - неверен.")
        return old_password

    def clean_new_password2(self):
        new_password = self.cleaned_data.get('new_password')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password != new_password2:
            raise forms.ValidationError('Новые пароли не совпадают.')
        return new_password2


class Question(forms.Form):
    name = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput
    )

    email = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput
    )

    message = forms.CharField(
        label='Опишите Ваш вопрос',
        widget=forms.Textarea
    )


class EditVotingForm(forms.Form):
    question = forms.CharField(
        label='Вопрос',
        min_length=5,
        max_length=25,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Вопрос', 'style': 'border-radius: 8px'})

    )
    description = forms.CharField(
        label='Дополнительное описание',
        max_length=255,
        required=False,
        widget=forms.Textarea(
            attrs={'class': 'form-control', 'placeholder': 'Описание', 'style': 'border-radius: 8px'})
    )

    class Meta:
        model = Voting


class RecoveryPass(forms.Form):
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль', 'autofocus': ''}), min_length=8, required=True)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput(attrs = {'class': 'form-control', 'placeholder': 'Повторите пароль'}), required=True)

    class Meta:
        model = User
        fields = ()

    def clean_password2(self):
        cd = self.data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']


class FileForm(forms.Form):
    file = forms.FileField(label='Select a file', required=False,
                           widget=forms.FileInput(attrs={'class': 'custom-file-input', 'id': 'inputGroupFile', 'aria-describedby': "inputGroupFileBtn", 'accept': "image/jpeg, image/png"}))
