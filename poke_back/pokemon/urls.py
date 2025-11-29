from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import ShopViewSet
from .api.MoveViewSet import MoveViewSet
from .api.PokemonMoveViewSet import PokemonMoveViewSet
from .api.PokemonViewSet import PokemonViewSet
from .api.LocationViewSet import LocationViewSet
from .api.WildPokemonEncounterViewSet import WildPokemonEncounterViewSet

router = DefaultRouter()
router.register(r'pokemons', PokemonViewSet, basename='pokemon')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'moves', MoveViewSet, basename='move')
router.register(r'pokemon-moves', PokemonMoveViewSet, basename='pokemonmove')
router.register(r'wild-encounters', WildPokemonEncounterViewSet, basename='wildencounter')
router.register(r'shop', ShopViewSet, basename='shop')

urlpatterns = [
    path('', include(router.urls)),
]