from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import SafeString


class Voting(models.Model):
    question = models.CharField(max_length=255)
    author = models.ForeignKey(to=User, null=False, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, default=None)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    single = models.BooleanField(default=False)
    like_count = models.IntegerField(default=0)

    def options(self):
        return Option.objects.filter(voting=self)

    def labels(self):
        labels = []
        for i in self.options():
            labels.append(i.text)
        return SafeString(labels)

    def vote_data(self):
        votes = []
        for i in self.options():
            votes.append(len(i.votes()))
        return SafeString(votes)

    def likes(self):
        return Like.objects.filter(voting=self)

    def comments(self):
        return Comment.objects.filter(voting=self)


class Option(models.Model):
    text = models.CharField(max_length=50)
    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    vote_count = models.IntegerField(default=0)

    def votes(self):
        return Vote.objects.filter(option=self)


class Vote(models.Model):
    option = models.ForeignKey(to=Option, on_delete=models.CASCADE)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE, null=True, default='Anonymous')
    created = models.DateTimeField(auto_now_add=True)
    anonymous = models.BooleanField(default=False)
    useragent = models.CharField(max_length=25, null=True, default=None)
    ip = models.CharField(max_length=15, null=False)


class Like(models.Model):
    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE, null=False)
    created = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    text = models.CharField(max_length=255)
    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    author = models.ForeignKey(to=User, on_delete=models.CASCADE, null=False)
    created = models.DateTimeField(auto_now_add=True)


class Recovery(models.Model):
    target_user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    from_ip = models.CharField(max_length=15, null=False, default=None)
    code = models.CharField(max_length=10)
    created = models.DateTimeField(auto_now_add=True)


class UserPhoto(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    img = models.ImageField(upload_to='profile', null=True, default='profile/profile_icon')

