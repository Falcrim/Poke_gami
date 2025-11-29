from django.core.management.base import BaseCommand
from pokemon.models.Location import Location
from pokemon.models.Pokemon import Pokemon
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter


class Command(BaseCommand):
    help = 'Carga encuentros de Pokémon salvajes para todas las rutas'

    def handle(self, *args, **options):
        self.stdout.write('Cargando encuentros de Pokémon salvajes para todas las rutas...')

        # Distribución completa por rutas (basada en Pokémon Rojo/Azul)
        route_distributions = {
            'Ruta 1': [
                (16, 2, 5, 'common'),  # Pidgey
                (19, 2, 4, 'common'),  # Rattata
                (10, 2, 4, 'uncommon'),  # Caterpie
                (13, 2, 4, 'uncommon'),  # Weedle
            ],
            'Ruta 2': [
                (16, 3, 6, 'common'),
                (19, 3, 5, 'common'),
                (10, 3, 5, 'uncommon'),
                (13, 3, 5, 'uncommon'),
                (43, 4, 6, 'rare'),  # Oddish
                (69, 4, 6, 'rare'),  # Bellsprout
            ],
            'Ruta 3': [
                (16, 4, 7, 'common'),
                (19, 4, 6, 'common'),
                (21, 4, 7, 'common'),  # Spearow
                (39, 5, 7, 'uncommon'),  # Jigglypuff
                (56, 5, 8, 'rare'),  # Mankey
            ],
            'Ruta 4': [
                (19, 5, 8, 'common'),
                (21, 5, 8, 'common'),
                (23, 6, 9, 'uncommon'),  # Ekans
                (27, 6, 9, 'uncommon'),  # Sandshrew
                (50, 7, 10, 'rare'),  # Diglett
            ],
            'Ruta 5': [
                (16, 6, 9, 'common'),
                (43, 7, 10, 'common'),
                (52, 8, 11, 'uncommon'),  # Meowth
                (69, 7, 10, 'uncommon'),
                (96, 8, 11, 'rare'),  # Drowzee
            ],
            'Ruta 6': [
                (16, 7, 10, 'common'),
                (43, 8, 11, 'common'),
                (52, 9, 12, 'uncommon'),
                (69, 8, 11, 'uncommon'),
                (96, 9, 12, 'rare'),
            ],
            'Ruta 7': [
                (19, 9, 12, 'common'),
                (52, 10, 13, 'common'),
                (58, 10, 13, 'uncommon'),  # Growlithe
                (37, 10, 13, 'uncommon'),  # Vulpix
                (39, 11, 14, 'rare'),
            ],
            'Ruta 8': [
                (19, 10, 13, 'common'),
                (52, 11, 14, 'common'),
                (23, 11, 14, 'uncommon'),
                (27, 11, 14, 'uncommon'),
                (39, 12, 15, 'rare'),
            ],
            'Ruta 9': [
                (19, 11, 14, 'common'),
                (21, 11, 14, 'common'),
                (23, 12, 15, 'uncommon'),
                (27, 12, 15, 'uncommon'),
                (30, 13, 16, 'rare'),  # Nidorina
            ],
            'Ruta 10': [
                (21, 12, 15, 'common'),
                (23, 13, 16, 'common'),
                (27, 13, 16, 'uncommon'),
                (100, 14, 17, 'rare'),  # Voltorb
                (81, 14, 17, 'rare'),  # Magnemite
            ],
            'Ruta 11': [
                (19, 13, 16, 'common'),
                (21, 13, 16, 'common'),
                (23, 14, 17, 'uncommon'),
                (27, 14, 17, 'uncommon'),
                (96, 15, 18, 'rare'),
            ],
            'Ruta 12': [
                (43, 13, 16, 'common'),
                (69, 13, 16, 'common'),
                (48, 14, 17, 'uncommon'),  # Venonat
                (118, 15, 18, 'uncommon'),  # Goldeen
                (79, 15, 18, 'rare'),  # Slowpoke
            ],
            'Ruta 13': [
                (16, 14, 17, 'common'),
                (43, 14, 17, 'common'),
                (48, 15, 18, 'uncommon'),
                (118, 16, 19, 'uncommon'),
                (83, 16, 19, 'rare'),  # Farfetch'd
            ],
            'Ruta 14': [
                (16, 15, 18, 'common'),
                (43, 15, 18, 'common'),
                (48, 16, 19, 'uncommon'),
                (49, 17, 20, 'uncommon'),  # Venomoth
                (123, 18, 21, 'rare'),  # Scyther
            ],
            'Ruta 15': [
                (16, 16, 19, 'common'),
                (43, 16, 19, 'common'),
                (48, 17, 20, 'uncommon'),
                (49, 18, 21, 'uncommon'),
                (114, 19, 22, 'rare'),  # Tangela
            ],
            'Ruta 16': [
                (19, 16, 19, 'common'),
                (52, 17, 20, 'common'),
                (20, 18, 21, 'uncommon'),  # Raticate
                (56, 18, 21, 'uncommon'),
                (58, 19, 22, 'rare'),
            ],
            'Ruta 17': [
                (19, 18, 21, 'common'),
                (52, 19, 22, 'common'),
                (20, 20, 23, 'uncommon'),
                (56, 20, 23, 'uncommon'),
                (57, 21, 24, 'rare'),  # Primeape
            ],
            'Ruta 18': [
                (19, 19, 22, 'common'),
                (52, 20, 23, 'common'),
                (20, 21, 24, 'uncommon'),
                (56, 21, 24, 'uncommon'),
                (57, 22, 25, 'rare'),
            ],
            'Ruta 19': [
                (72, 20, 25, 'common'),  # Tentacool
                (90, 20, 25, 'common'),  # Shellder
                (116, 21, 26, 'uncommon'),  # Horsea
                (120, 22, 27, 'uncommon'),  # Staryu
                (98, 23, 28, 'rare'),  # Krabby
            ],
            'Ruta 20': [
                (72, 21, 26, 'common'),
                (90, 21, 26, 'common'),
                (116, 22, 27, 'uncommon'),
                (120, 23, 28, 'uncommon'),
                (98, 24, 29, 'rare'),
            ],
            'Ruta 21': [
                (16, 22, 27, 'common'),
                (19, 22, 27, 'common'),
                (21, 23, 28, 'common'),
                (72, 23, 28, 'uncommon'),
                (114, 24, 29, 'rare'),  # Tangela
            ],
            'Ruta 22': [
                (19, 3, 6, 'common'),
                (21, 3, 6, 'common'),
                (56, 4, 7, 'uncommon'),
                (29, 5, 8, 'rare'),  # Nidoran♀
                (32, 5, 8, 'rare'),  # Nidoran♂
            ],
            'Ruta 23': [
                (21, 25, 30, 'common'),
                (22, 26, 31, 'common'),  # Fearow
                (56, 27, 32, 'uncommon'),
                (57, 28, 33, 'uncommon'),
                (30, 29, 34, 'rare'),  # Nidorina
                (33, 29, 34, 'rare'),  # Nidorino
            ],
            'Ruta 24': [
                (10, 7, 10, 'common'),
                (13, 7, 10, 'common'),
                (16, 8, 11, 'common'),
                (43, 9, 12, 'uncommon'),
                (69, 9, 12, 'uncommon'),
                (63, 10, 13, 'rare'),  # Abra
            ],
            'Ruta 25': [
                (10, 8, 11, 'common'),
                (13, 8, 11, 'common'),
                (16, 9, 12, 'common'),
                (43, 10, 13, 'uncommon'),
                (69, 10, 13, 'uncommon'),
                (63, 11, 14, 'rare'),
            ],
        }

        for route_name, pokemon_list in route_distributions.items():
            try:
                location = Location.objects.get(name=route_name)

                WildPokemonEncounter.objects.filter(location=location).delete()

                created_count = 0
                for pokedex_id, min_level, max_level, rarity in pokemon_list:
                    try:
                        pokemon = Pokemon.objects.get(pokedex_id=pokedex_id)
                        WildPokemonEncounter.objects.create(
                            location=location,
                            pokemon=pokemon,
                            min_level=min_level,
                            max_level=max_level,
                            rarity=rarity
                        )
                        created_count += 1
                    except Pokemon.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'Pokémon {pokedex_id} no encontrado para {route_name}'))

                self.stdout.write(f'{route_name}: {created_count} Pokémon cargados')

            except Location.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Ubicación {route_name} no encontrada'))

        self.stdout.write(self.style.SUCCESS('¡Encuentros salvajes cargados exitosamente para todas las rutas!'))