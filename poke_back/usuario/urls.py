from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.PlayerPokemonViewSet import PlayerPokemonViewSet
from .api.PokedexViewSet import PokedexViewSet
from .api.UserViewSet import UserViewSet
from .api.PlayerViewSet import PlayerViewSet
from .api.BagViewSet import BagViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'bag', BagViewSet, basename='bag')
router.register(r'pokedex', PokedexViewSet, basename='pokedex')
router.register(r'player-pokemons', PlayerPokemonViewSet, basename='playerpokemon')

urlpatterns = [
    path('', include(router.urls)),
]