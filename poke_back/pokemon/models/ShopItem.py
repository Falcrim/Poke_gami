from django.db import models

class ShopItem(models.Model):
    ITEM_TYPES = (
        ('potion', 'Poción'),
        ('pokeball', 'Pokéball'),
        ('super_potion', 'Superpoción'),
        ('hyper_potion', 'Hiperpoción'),
        ('ultra_ball', 'Ultraball'),
    )

    name = models.CharField(max_length=50)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    price = models.IntegerField()
    description = models.TextField()
    effect_value = models.IntegerField(default=0)

    class Meta:
        db_table = 'shop_items'

    def __str__(self):
        return f"{self.name} - ${self.price}"