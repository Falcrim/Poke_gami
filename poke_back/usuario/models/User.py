from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)


    battles_won = models.IntegerField(default=0)
    battles_lost = models.IntegerField(default=0)
    pvp_rating = models.IntegerField(default=1000)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username