import datetime
from random import randint

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from django.core.paginator import Paginator

from simple_voting.forms import *
from simple_votings_11 import settings
from .models import *


def index(request):
    clear_session(request)
    context = {'data': datetime.datetime.now(), 'username': request.user}
    return render(request, 'index.html', context)


def about_us(request):
    clear_session(request)
    return render(request, 'about_us.html')


@login_required()
def available_voting(request):
    clear_session(request)
    context = {'data': datetime.datetime.now(),
               'user': User.objects.get(id=request.user.id)}
    counting_index = 0
    for option in Option.objects.all():
        option.vote_count = option.votes().count()
        counting_index += 1
        option.save()
    counting_index = 0
    for voting in Voting.objects.all():
        voting.like_count = voting.likes().count()
        counting_index += 1
        voting.save()
    votings_list = Voting.objects.all()
    paginator = Paginator(votings_list, 4)
    if request.method == 'GET':
        page = request.GET.get('page')
        votings = paginator.get_page(page)
        context['votings'] = votings
        return render(request, 'vote/available_voting.html', context)
    elif request.method == 'POST':
        if not (request.POST.get('id') is None):
            return redirect('/vote?voting={}'.format(request.POST.get('id')))
        elif not (request.POST.get('id_advanced') is None):
            return redirect('/like_comment?voting={}'.format(request.POST.get('id_advanced')))
    return render(request, 'vote/available_voting.html', context)


@login_required()
def create_voting(request):
    context = {}
    voting_form = VotingForm(request.POST)
    context['voting_form'] = voting_form
    if request.method == 'POST':
        if voting_form.is_valid():
            is_single = False
            if request.POST.get('isSingle', None):
                is_single = True
            item = Voting(
                question=voting_form.data['question'],
                author=User.objects.get(id=request.user.id),
                description=voting_form.data['description'],
                single=is_single
            )
            data = Voting.objects.all().values('question', 'author')
            for row in data:
                if row['question'] == voting_form.data['question'] and row['author'] == request.user.id:
                    error = dict()
                    error['message'] = 'Вы уже создали опрос с таким названием'
                    error['question'] = voting_form.data['question']
                    context['error'] = error
                    return render(request, 'vote/create_voting.html', context)
            item.save()
            request.session['id_voting'] = item.id
            return generate_voting(request)
    return render(request, 'vote/create_voting.html', context)


def generate_voting(request):
    context = {}
    id_voting = request.session.get('id_voting', -1)
    option_form = OptionForm(request.POST)
    if request.method == 'POST' and id_voting > 0:
        if option_form.is_valid():
            item = Option(text=option_form.data['option'], voting=Voting.objects.get(id=id_voting))
            item.save()
            return redirect('/generate_voting/')
    if id_voting > 0:
        voting = Voting.objects.all().filter(id=id_voting).values('question', 'description')
        question = voting[0]['question']
        description = voting[0]['description']
    else:
        question = 'question'
        description = 'description'
    voting_context = {'question': question, 'description': description}
    option_context = {'form': option_form}
    context['voting'] = voting_context
    context['option'] = option_context
    context['option_list'] = Option.objects.filter(voting=Voting.objects.get(id=id_voting))
    if request.POST.get('status'):
        if id_voting > 0:
            del request.session['id_voting']
        return redirect('/available_voting')
    return render(request, 'vote/generate_voting.html', context)

# def login_page(request):
#     if request.method == 'POST':
#         loginform = LoginForm(request.POST)
#         if loginform.is_valid():
#             username = loginform.data['username']
#             password = loginform.data['password']
#             user = authenticate(request, username=username, password=password)
#     return redirect('index')

def signup(request):
    clear_session(request)
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password2'])
            new_user.save()
            login(request, new_user)
            return render(request, 'index.html', {'username': user_form.data['username']})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'profile/register.html', {'user_form': user_form})


@login_required()
def complain(request):
    context = {}
    clear_session(request)
    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        context['username'] = user.username
        context['email'] = user.email
    elif request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        complain = request.POST.get('complain')
        email_subject = 'EVILEG :: Сообщение через контактную форму '
        email_body = "С сайта отправлено новое сообщение\n\n" \
                     "Имя отправителя: %s \n" \
                     "E-mail отправителя: %s \n\n" \
                     "Сообщение: \n" \
                     "%s " % \
                     (username, email, complain)
        send_mail(email_subject, email_body, settings.EMAIL_HOST_USER, ['target_email@example.com'],
                  fail_silently=False)
        context['status'] = 'send'
    return render(request, 'users/complain.html', context)


def vote(request):
    context = {}
    choices = []
    form_vote = VoteFormCheckBox(request.POST)
    user_ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    user = None
    if not request.user.is_anonymous:
        user = User.objects.get(id=request.user.id)
    if request.method == 'POST':
        options = dict(form_vote.data).get('items')
        if options is not None:
            voting_id = request.session.get('id_voting', None)
            if len(options) > 1 and Voting.objects.get(id=voting_id).single:
                context['error'] = "You can choose the only one answer!"
                return render(request, 'vote/vote.html', context)
            if len(options) > 0:
                for option in options:
                    item = Vote(
                        option=Option.objects.get(id=option),
                        author=user,
                        ip=user_ip,
                        useragent=request.META['HTTP_USER_AGENT'] or None
                    )
                    item.save()
    if len(request.GET) > 0 and request.method == 'GET':
        voting_id = request.GET.get('voting', 'error')
        if voting_id == 'error':
            return redirect('/available_voting')
        request.session['id_voting'] = voting_id
        voting = Voting.objects.get(id=voting_id)
        opts = Option.objects.filter(voting=voting)
        for item in opts:
            vts = item.votes()
            for jtem in vts:
                if not request.user.is_anonymous and jtem.author is not None:
                    if jtem.author.username == User.objects.get(id=request.user.id).username and user_ip == jtem.ip:
                        context['error'] = "You are already voted"
                        return render(request, 'vote/vote.html', context)
                else:
                    if user_ip == jtem.ip:
                        context['error'] = "You are already voted"
                        return render(request, 'vote/vote.html', context)
        voting = Voting.objects.get(id=voting_id)
        context['question'] = voting.question
        context['description'] = voting.description
        context['single'] = SafeString(str(voting.single).lower())
        if context['description'] is None:
            context['description'] = 'Отсутствует'
        options = Option.objects.filter(voting_id=voting_id)
        for i in range(len(options)):
            choices.append(('{}'.format(options[i].id), '{}'.format(options[i].text)))
        form_vote.fields['items'].choices = choices
        context['form_vote'] = form_vote
    if len(request.GET) == 0:
        return redirect('/available_voting')
    return render(request, 'vote/vote.html', context)


@login_required()
def like_comment(request):
    context = {}
    voting_id = request.session.get('id_voting', None)
    if request.method == 'GET':
        context.update(csrf(request))
        context['like_form'] = LikeForm()
        context['comment_form'] = CommentForm()
        voting_id = request.GET.get('voting')
        request.session['id_voting'] = voting_id
        context['comments'] = Comment.objects.filter(voting=Voting.objects.get(id=voting_id))
        context['likes_count'] = Voting.objects.get(id=voting_id).likes().count()
        if voting_id:
            is_liked = False
            likes = Like.objects.filter(author=User.objects.get(id=request.user.id))
            for like in likes:
                if like.voting == Voting.objects.get(id=voting_id):
                    is_liked = True
                    break
            context['liked'] = is_liked
            context['voting_id'] = Voting.objects.get(id=voting_id)
    if request.method == 'POST' and voting_id:
        liked = request.POST.get('like')
        if liked:
            likes = Like.objects.filter(author=User.objects.get(id=request.user.id))
            already_like = False
            del_like = None
            for like in likes:
                if like.voting == Voting.objects.get(id=voting_id):
                    already_like = True
                    del_like = like
                    break
            if not already_like:
                like_item = Like(
                    voting=Voting.objects.get(id=voting_id),
                    author=User.objects.get(id=request.user.id)
                )
                like_item.save()
                voting = Voting.objects.get(id=voting_id)
                voting.like_count = voting.likes().count()
            if already_like:
                del_like.delete()
        if request.POST.get('comment'):
            text = request.POST.get('comment')
            comment_item = Comment(
                text=text,
                voting=Voting.objects.get(id=voting_id),
                author=User.objects.get(id=request.user.id)
            )
            comment_item.save()
        clear_session(request)
        return redirect('/like_comment/?voting={}'.format(voting_id))
    return render(request, 'vote/like_comment.html', context)


@login_required()
def profile(request):
    clear_session(request)
    context = {}
    voting_items = Voting.objects.filter(author_id=User.objects.get(id=request.user.id))
    likes = Like.objects.filter(author_id=User.objects.get(id=request.user.id))
    context['voting_items'] = voting_items
    context['user'] = User.objects.get(id=request.user.id)
    context['likes'] = likes
    context['votes_count'] = voting_items.count()
    current_user = User.objects.get(id=request.user.id)
    if UserPhoto.objects.filter(user=current_user):
        context['photo'] = UserPhoto.objects.get(user=current_user).img
    else:
        context['photo'] = 'profile/profile_icon.png'
    if request.method == 'POST':
        if request.POST.get('id_advanced'):
            return redirect('/like_comment?voting={}'.format(request.POST.get('id_advanced')))
        if request.POST.get('link'):
            return redirect('/vote?voting={}'.format(request.POST.get('link')))
    return render(request, 'profile/profile.html', context)


@login_required()
def change_info(request):
    clear_session(request)
    current_user = User.objects.get(id=request.user.id)
    form = ChangeInfoForm(request.POST)
    photo = FileForm(request.POST, request.FILES)
    context = {'form': form, 'photo': photo}
    if UserPhoto.objects.filter(user=current_user):
        context['userphoto'] = UserPhoto.objects.get(user=current_user).img
    else:
        context['userphoto'] = 'profile/profile_icon.png'
    if request.method == 'POST':
        if request.POST.get('old_password'):
            old_password = request.POST.get('old_password')
            if current_user.check_password('{}'.format(old_password)) is False:
                form.set_old_password_flag()
                return render(request, 'profile/change_info.html', {'form': form})
        if form.is_valid():
            if request.POST.get('username'):
                current_user.username = request.POST.get('username')
            if request.POST.get('first_name'):
                current_user.first_name = request.POST.get('first_name')
            if request.POST.get('last_name'):
                current_user.last_name = request.POST.get('last_name')
            if request.POST.get('email'):
                current_user.email = request.POST.get('email')
            if request.POST.get('old_password'):
                old_password = request.POST.get('old_password')
                if current_user.check_password('{}'.format(old_password)) is False:
                    form.set_old_password_flag()
                    return render(request, 'profile/change_info.html', {'form': form})
                else:
                    current_user.set_password('{}'.format(form.data['new_password2']))
            current_user.save()
            login(request, current_user)
        else:
            return render(request, 'profile/change_info.html', context)
        if photo.is_valid():
            if UserPhoto.objects.filter(user=current_user):
                userphoto = UserPhoto.objects.get(user=current_user)
            else:
                userphoto = UserPhoto(user=current_user, img='profile/profile_icon.png')
            if request.FILES.get('file'):
                userphoto.img = request.FILES.get('file')
                userphoto.save()
    if request.POST.get('status'):
        return redirect('/profile')
    return render(request, 'profile/change_info.html', context)


@login_required()
def edit_voting(request):
    context = {}
    voting_form = EditVotingForm(request.POST)
    context['voting_form'] = voting_form
    option_form = OptionForm(request.POST)
    context['option_form'] = option_form
    if request.method == 'POST':
        if request.session.get('id_voting', 'error') == 'error':
            votes_id = request.POST
            for vid in votes_id:
                vote_id = vid
            request.session['id_voting'] = vote_id
        vote_id = request.session.get('id_voting', 'error')
        if voting_form.is_valid():
            new_question = voting_form.cleaned_data.get('question')
            new_desc = voting_form.cleaned_data.get('description')
            voting = Voting.objects.get(id=vote_id)
            if new_question:
                voting.question = new_question
                voting.save()
            if new_desc:
                voting.description = new_desc
                voting.save()
        options = Option.objects.filter(voting=Voting.objects.get(id=vote_id))
        context['options'] = options
        delete = request.POST.get('Delete')
        if delete:
            Option.objects.get(id=delete).delete()
        if option_form.is_valid():
            new_option = option_form.data['option']
            new_option = Option(text=new_option, voting=Voting.objects.get(id=vote_id))
            new_option.save()
        if request.POST.get('status') == 'Назад':
            return redirect('../profile')
        if request.POST.get('status') == 'Удалить':
            Voting.objects.get(id=vote_id).delete()
            return redirect('/profile/')
    return render(request, 'vote/edit_voting.html', context)


@login_required()
def other_users_review(request):
    clear_session(request)
    context = {}
    users = []
    users_dict = {}
    for i in range(1, int(User.objects.all().count()) + 1):
        users_dict['username'] = str(User.objects.get(id=i))
        users_dict['votes_count'] = Voting.objects.filter(author=i).count()
        users_dict['id'] = i
        users.append(users_dict.copy())
    context['users'] = users
    return render(request, 'users/other_users_review.html', context)


@login_required()
def user_votes_review(request):
    clear_session(request)
    current_user = User.objects.get(id=request.user.id)
    review_user = User.objects.get(id=request.GET.get('voting', 0))
    context = {'user': current_user,
               'user_review': review_user,
               'votes_count': Voting.objects.filter(author=request.GET.get('voting', 0)).count(),
               'data': datetime.datetime.now(),
               'votings': Voting.objects.filter(author=request.GET.get('voting', 0))}
    if UserPhoto.objects.filter(user=review_user):
        context['photo'] = UserPhoto.objects.get(user=review_user).img
    else:
        context['photo'] = 'profile/profile_icon.png'
    counting_index = 0
    for option in Option.objects.all():
        option.vote_count = option.votes().count()
        counting_index += 1
        option.save()
    counting_index = 0
    for voting in Voting.objects.all():
        voting.like_count = voting.likes().count()
        counting_index += 1
        voting.save()
    return render(request, 'users/user_votes_review.html', context)


def recovery_password(request):
    context = {'step': '1'}
    user_ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    form = RecoveryPass(request.POST)
    if request.method == 'POST':
        if request.POST.get('start_procedure'):
            data = request.POST.get('start_procedure')
            target_user = None
            if User.objects.filter(username=data):
                target_user = User.objects.get(username=data)
            elif User.objects.filter(email=data):
                target_user = User.objects.get(email=data)
            if target_user:
                code = '{}{}{}{}{}{}'.format(
                    randint(0, 9),
                    randint(0, 9),
                    randint(0, 9),
                    randint(0, 9),
                    randint(0, 9),
                    randint(0, 9)
                )
                send_recovery_code(code, target_user)
                rec = Recovery(target_user=target_user, from_ip=user_ip, code=code)
                rec.save()
                context['step'] = '2'
            else:
                context['error'] = 'Пользователь не найден'
        if request.POST.get('code'):
            code = request.POST.get('code')
            target_user = None
            if Recovery.objects.filter(code=code):
                data = Recovery.objects.filter(code=code)
                for item in data:
                    if user_ip == item.from_ip:
                        target_user = item.target_user
                        context['step'] = '3'
                        context['form'] = form
                        request.session['id_user'] = target_user.id
            if target_user is None:
                context['step'] = '2'
                context['error'] = 'Неверный код'
        if request.POST.get('password'):
            if form.is_valid():
                target_user = request.session.get('id_user')
                new_pass = form.data['password']
                target_user = User.objects.get(id=target_user)
                target_user.set_password(new_pass)
                target_user.save()
                login(request, target_user)
                data_for_delete = Recovery.objects.filter(target_user=target_user)
                for item in data_for_delete:
                    item.delete()
                context['step'] = '4'
            else:
                context['step'] = '3'
                context['form'] = form
                context['error'] = 'Ошибка при заполнении полей'
    return render(request, 'profile/recovery_password.html', context)


def clear_session(request):
    if request.session.get('id_voting', None):
        del request.session['id_voting']
    if request.session.get('id_user', None):
        del request.session['id_user']


def send_recovery_code(code, user):
    email_subject = 'EVILEG :: Сообщение через контактную форму '
    email_body = "Код для восстановления пароля: {}".format(code)
    send_mail(email_subject, email_body, settings.EMAIL_HOST_USER, ['{}'.format(user.email)],
              fail_silently=False)
