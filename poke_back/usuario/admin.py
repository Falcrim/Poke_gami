from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models.User import User
from .models.Player import Player
from .models.Bag import Bag
from .models.Pokedex import Pokedex
from .models.PlayerPokemon import PlayerPokemon

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'battles_won', 'battles_lost', 'pvp_rating')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Pokémon Stats', {
            'fields': ('battles_won', 'battles_lost', 'pvp_rating')
        }),
    )

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_location', 'money', 'starter_chosen')
    list_filter = ('starter_chosen',)

@admin.register(Bag)
class BagAdmin(admin.ModelAdmin):
    list_display = ('player', 'pokeballs', 'potions')

@admin.register(Pokedex)
class PokedexAdmin(admin.ModelAdmin):
    list_display = ('player', 'pokemon', 'state', 'date_registered')
    list_filter = ('state',)

@admin.register(PlayerPokemon)
class PlayerPokemonAdmin(admin.ModelAdmin):
    list_display = ('player', 'pokemon', 'nickname', 'level')
    list_filter = ('player',)