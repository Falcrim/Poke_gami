from django.db import models
from .Player import Player


class Bag(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='bag')

    # Pokéballs
    pokeballs = models.IntegerField(default=5)  # Pokéball normal
    ultra_balls = models.IntegerField(default=0)  # Ultraball

    # Pociones
    potions = models.IntegerField(default=2)  # Poción normal (cura 20 HP)
    super_potions = models.IntegerField(default=0)  # Superpoción (cura 50 HP)
    hyper_potions = models.IntegerField(default=0)  # Hiperpoción (cura 200 HP)

    class Meta:
        db_table = 'bags'

    def __str__(self):
        return f"Bag of {self.player.user.username}"

    def get_item_count(self, item_type):
        """Obtener la cantidad de un tipo específico de item"""
        item_map = {
            'pokeball': self.pokeballs,
            'ultra_ball': self.ultra_balls,
            'potion': self.potions,
            'super_potion': self.super_potions,
            'hyper_potion': self.hyper_potions,
        }
        return item_map.get(item_type, 0)

    def add_item(self, item_type, quantity=1):
        """Agregar items a la mochila"""
        if item_type == 'pokeball':
            self.pokeballs += quantity
        elif item_type == 'ultra_ball':
            self.ultra_balls += quantity
        elif item_type == 'potion':
            self.potions += quantity
        elif item_type == 'super_potion':
            self.super_potions += quantity
        elif item_type == 'hyper_potion':
            self.hyper_potions += quantity
        self.save()

    def use_item(self, item_type, quantity=1):
        """Usar items de la mochila"""
        current_count = self.get_item_count(item_type)
        if current_count < quantity:
            return False

        if item_type == 'pokeball':
            self.pokeballs -= quantity
        elif item_type == 'ultra_ball':
            self.ultra_balls -= quantity
        elif item_type == 'potion':
            self.potions -= quantity
        elif item_type == 'super_potion':
            self.super_potions -= quantity
        elif item_type == 'hyper_potion':
            self.hyper_potions -= quantity

        self.save()
        return True

    def get_summary(self):
        """Obtener resumen de todos los items"""
        return {
            'pokeballs': self.pokeballs,
            'ultra_balls': self.ultra_balls,
            'potions': self.potions,
            'super_potions': self.super_potions,
            'hyper_potions': self.hyper_potions,
        }