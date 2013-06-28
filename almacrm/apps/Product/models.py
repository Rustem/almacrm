from django.db import models

class Product(models.Model):
	name=models.CharField(max_length=200)
	price=models.DecimalField(default=0, max_digits=10, decimal_places=2)
	quantity=models.IntegerField(default=0)
	description=models.TextField()

	def __unicode__(self):
		return "{},price- {}, quantity - {}, description:\n {}".format(self.name, self.price, self.quantity, self.description)
		
