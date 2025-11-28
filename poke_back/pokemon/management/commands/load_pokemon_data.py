import requests
import time
from django.core.management.base import BaseCommand
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move
from pokemon.models.PokemonMove import PokemonMove


class Command(BaseCommand):
    help = 'Carga los datos completos de los 151 Pokémon de Kanto desde PokeAPI'

    def handle(self, *args, **options):
        self.stdout.write('Cargando datos completos de Pokémon...')

        # Primero cargar todos los Pokémon básicos
        for i in range(1, 152):
            self.load_pokemon_basic_data(i)
            time.sleep(0.5)  # Esperar para no sobrecargar la API

        # Luego cargar las evoluciones
        self.stdout.write('Cargando evoluciones...')
        for i in range(1, 152):
            self.load_evolution_data(i)
            time.sleep(0.5)

        self.stdout.write(self.style.SUCCESS('Datos completos de Pokémon cargados exitosamente!'))

    def load_pokemon_basic_data(self, pokemon_id):
        try:
            # Obtener datos del Pokémon
            url = f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}/'
            response = requests.get(url)
            data = response.json()

            # Obtener datos de la especie
            species_url = f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/'
            species_response = requests.get(species_url)
            species_data = species_response.json()

            # Determinar si evoluciona de otro Pokémon
            evolves_from = None
            if species_data.get('evolves_from_species'):
                evolves_from_name = species_data['evolves_from_species']['name']
                try:
                    evolves_from = Pokemon.objects.get(name__iexact=evolves_from_name.capitalize())
                except Pokemon.DoesNotExist:
                    pass

            # Crear o actualizar el Pokémon
            pokemon, created = Pokemon.objects.get_or_create(
                pokedex_id=pokemon_id,
                defaults={
                    'name': data['name'].capitalize(),
                    'type1': data['types'][0]['type']['name'],
                    'type2': data['types'][1]['type']['name'] if len(data['types']) > 1 else None,
                    'base_hp': data['stats'][0]['base_stat'],
                    'base_attack': data['stats'][1]['base_stat'],
                    'base_defense': data['stats'][2]['base_stat'],
                    'base_special_attack': data['stats'][3]['base_stat'],
                    'base_special_defense': data['stats'][4]['base_stat'],
                    'base_speed': data['stats'][5]['base_stat'],
                    'experience_growth': species_data['base_happiness'],
                    'evolves_from': evolves_from,
                    'sprite_front': data['sprites']['front_default'],
                    'sprite_back': data['sprites']['back_default'],
                }
            )

            # Cargar movimientos
            self.load_moves(pokemon, data['moves'])

            status = 'Creado' if created else 'Actualizado'
            self.stdout.write(f'{status}: {pokemon.name}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cargando Pokémon {pokemon_id}: {str(e)}'))

    def load_evolution_data(self, pokemon_id):
        try:
            # Obtener datos de la especie para la evolución
            species_url = f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/'
            species_response = requests.get(species_url)
            species_data = species_response.json()

            # Obtener la cadena de evolución
            evolution_chain_url = species_data['evolution_chain']['url']
            evolution_response = requests.get(evolution_chain_url)
            evolution_data = evolution_response.json()

            # Procesar la cadena de evolución
            self.process_evolution_chain(evolution_data['chain'])

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cargando evolución para Pokémon {pokemon_id}: {str(e)}'))

    def process_evolution_chain(self, chain):
        current_pokemon_name = chain['species']['name']

        try:
            current_pokemon = Pokemon.objects.get(name__iexact=current_pokemon_name.capitalize())
        except Pokemon.DoesNotExist:
            return

        for evolution in chain.get('evolves_to', []):
            evolution_name = evolution['species']['name']

            try:
                evolved_pokemon = Pokemon.objects.get(name__iexact=evolution_name.capitalize())
            except Pokemon.DoesNotExist:
                continue

            evolution_details = evolution['evolution_details'][0]
            evolution_level = None

            if evolution_details['trigger']['name'] == 'level-up':
                if evolution_details.get('min_level'):
                    evolution_level = evolution_details['min_level']
                elif evolution_details.get('min_happiness') or evolution_details.get('min_affection'):
                    evolution_level = 1

            # Actualizar el Pokémon evolucionado
            evolved_pokemon.evolves_from = current_pokemon
            evolved_pokemon.evolution_level = evolution_level
            evolved_pokemon.save()

            self.stdout.write(f'  Evolución: {current_pokemon.name} → {evolved_pokemon.name} (nivel {evolution_level})')

            # Procesar recursivamente
            self.process_evolution_chain(evolution)

    def load_moves(self, pokemon, moves_data):
        for move_data in moves_data:
            for version in move_data['version_group_details']:
                if version['move_learn_method']['name'] == 'level-up' and version['version_group']['name'] in [
                    'red-blue', 'yellow']:
                    level = version['level_learned_at']
                    if level > 0:
                        move_name = move_data['move']['name']
                        move, created = Move.objects.get_or_create(
                            name=move_name,
                            defaults={
                                'type': 'normal',
                                'power': 0,
                                'accuracy': 0,
                                'pp': 0,
                                'damage_class': 'physical',
                            }
                        )

                        if created:
                            self.update_move_data(move)

                        PokemonMove.objects.get_or_create(
                            pokemon=pokemon,
                            move=move,
                            level=level
                        )

    def update_move_data(self, move):
        try:
            move_url = f'https://pokeapi.co/api/v2/move/{move.name}/'
            response = requests.get(move_url)
            if response.status_code == 200:
                data = response.json()
                move.type = data['type']['name']
                move.power = data['power'] if data['power'] else 0
                move.accuracy = data['accuracy'] if data['accuracy'] else 0
                move.pp = data['pp'] if data['pp'] else 0
                move.damage_class = data['damage_class']['name']
                move.save()
        except:
            pass  # Si falla, dejamos los valores por defecto