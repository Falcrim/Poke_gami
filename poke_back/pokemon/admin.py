from django.contrib import admin
from .models.Pokemon import Pokemon
from .models.Move import Move
from .models.Location import Location
from .models.PokemonMove import PokemonMove
from .models.WildPokemonEncounter import WildPokemonEncounter

@admin.register(Pokemon)
class PokemonAdmin(admin.ModelAdmin):
    list_display = ('pokedex_id', 'name', 'type1', 'type2')
    list_filter = ('type1', 'type2')
    search_fields = ('name',)

@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'power', 'accuracy', 'pp')
    list_filter = ('type', 'damage_class')

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_type')
    list_filter = ('location_type',)

@admin.register(PokemonMove)
class PokemonMoveAdmin(admin.ModelAdmin):
    list_display = ('pokemon', 'move', 'level')
    list_filter = ('pokemon', 'level')

@admin.register(WildPokemonEncounter)
class WildPokemonEncounterAdmin(admin.ModelAdmin):
    list_display = ('pokemon', 'location', 'min_level', 'max_level', 'rarity')
    list_filter = ('location', 'rarity')