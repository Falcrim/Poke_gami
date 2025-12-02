from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api import PokemonCenterViewSet, BagItemsViewSet, TeamOrderViewSet, BattleViewSet, PvPBattleViewSet
from .api.PlayerPokemonViewSet import PlayerPokemonViewSet
from .api.PokedexViewSet import PokedexViewSet
from .api.UserViewSet import UserViewSet
from .api.PlayerViewSet import PlayerViewSet
from .api.BagViewSet import BagViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'bag', BagViewSet, basename='bag')
router.register(r'bag-items', BagItemsViewSet, basename='bagitems')
router.register(r'pokedex', PokedexViewSet, basename='pokedex')
router.register(r'player-pokemons', PlayerPokemonViewSet, basename='playerpokemon')
router.register(r'pokemon-center', PokemonCenterViewSet, basename='pokemoncenter')
router.register(r'team-order', TeamOrderViewSet, basename='teamorder')
router.register(r'battles', BattleViewSet, basename='battle')
router.register(r'pvp-battles', PvPBattleViewSet, basename='pvp-battle')


urlpatterns = [
    path('', include(router.urls)),
]