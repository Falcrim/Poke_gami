from django.core.management.base import BaseCommand
from pokemon.models.Location import Location
from pokemon.models.Pokemon import Pokemon
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter


class Command(BaseCommand):
    help = 'Carga encuentros de Pokémon salvajes por ubicación'

    def handle(self, *args, **options):
        self.stdout.write('Cargando encuentros de Pokémon salvajes...')

        # Ruta 1 - Pokémon iniciales comunes
        route_1 = Location.objects.get(name='Ruta 1')
        WildPokemonEncounter.objects.get_or_create(
            location=route_1,
            pokemon=Pokemon.objects.get(pokedex_id=16),  # Pidgey
            defaults={'min_level': 2, 'max_level': 4, 'rarity': 'common'}
        )
        WildPokemonEncounter.objects.get_or_create(
            location=route_1,
            pokemon=Pokemon.objects.get(pokedex_id=19),  # Ratata
            defaults={'min_level': 2, 'max_level': 4, 'rarity': 'common'}
        )
        WildPokemonEncounter.objects.get_or_create(
            location=route_1,
            pokemon=Pokemon.objects.get(pokedex_id=10),  # Caterpie
            defaults={'min_level': 2, 'max_level': 3, 'rarity': 'uncommon'}
        )

        self.stdout.write(self.style.SUCCESS('Encuentros salvajes cargados exitosamente!'))