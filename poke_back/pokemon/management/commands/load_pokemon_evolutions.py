import requests
from django.core.management.base import BaseCommand
from pokemon.models.Pokemon import Pokemon


class Command(BaseCommand):
    help = 'Carga las evoluciones de los Pokémon desde PokeAPI'

    def handle(self, *args, **options):
        self.stdout.write('Cargando evoluciones de Pokémon...')

        # Cargar evoluciones para los primeros 151 Pokémon
        for i in range(1, 152):
            self.load_evolution(i)

        self.stdout.write(self.style.SUCCESS('Evoluciones cargadas exitosamente!'))

    def load_evolution(self, pokemon_id):
        try:
            # Obtener datos de la especie para la evolución
            species_url = f'https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}/'
            response = requests.get(species_url)
            species_data = response.json()

            # Obtener la cadena de evolución
            evolution_chain_url = species_data['evolution_chain']['url']
            evolution_response = requests.get(evolution_chain_url)
            evolution_data = evolution_response.json()

            # Procesar la cadena de evolución
            self.process_evolution_chain(evolution_data['chain'])

            self.stdout.write(f'Procesado: {species_data["name"].capitalize()}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cargando evolución para Pokémon {pokemon_id}: {str(e)}'))

    def process_evolution_chain(self, chain):
        current_pokemon_name = chain['species']['name']

        # Buscar el Pokémon actual en la base de datos
        try:
            current_pokemon = Pokemon.objects.get(name__iexact=current_pokemon_name.capitalize())
        except Pokemon.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Pokémon {current_pokemon_name} no encontrado en BD'))
            return

        # Procesar evoluciones
        for evolution in chain.get('evolves_to', []):
            evolution_name = evolution['species']['name']

            # Buscar el Pokémon evolucionado en la base de datos
            try:
                evolved_pokemon = Pokemon.objects.get(name__iexact=evolution_name.capitalize())
            except Pokemon.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Pokémon evolucionado {evolution_name} no encontrado en BD'))
                continue

            # Obtener detalles de la evolución
            evolution_details = evolution['evolution_details'][0]

            # Determinar nivel de evolución (si es por nivel)
            evolution_level = None
            if evolution_details['trigger']['name'] == 'level-up':
                if evolution_details.get('min_level'):
                    evolution_level = evolution_details['min_level']
                # Algunas evoluciones son por nivel pero sin nivel específico (por amistad, etc.)
                elif evolution_details.get('min_happiness'):
                    evolution_level = 1  # Valor por defecto para evoluciones por amistad
                elif evolution_details.get('min_affection'):
                    evolution_level = 1  # Valor por defecto para evoluciones por cariño

            # Actualizar el Pokémon evolucionado con su pre-evolución y nivel
            evolved_pokemon.evolves_from = current_pokemon
            evolved_pokemon.evolution_level = evolution_level
            evolved_pokemon.save()

            self.stdout.write(
                f'  → {current_pokemon.name} evoluciona a {evolved_pokemon.name} al nivel {evolution_level}')

            # Procesar recursivamente las siguientes evoluciones
            self.process_evolution_chain(evolution)