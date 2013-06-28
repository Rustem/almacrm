from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.generic.list import MultipleObjectMixin
from .models import Product
from django.http import HttpResponse, HttpResponseRedirect
from .forms import ProductForm
from django.contrib import messages

class ProductListView(ListView, MultipleObjectMixin):
	model=Product
	context_object_name='products'
	template_name='products_list.html'

	def get_queryset(self):
		products=Product.objects.all()
		return products

class SpecificProductView(TemplateView):
    model=Product
    template_name='product.html'
    def get_context_data(self, **kwargs):
        pk=self.kwargs('pk')
        context=super(SpecificProductView, self).get_context_data(**kwargs):
        context['product']=Product.objects.filter(pk=pk)
        return context

class ProductUpdateView(UpdateView):
    form_class = ProductForm
    template_name = "update_product.html"
    success_url = "/Product/products"
    model = Product

	def get_queryset(self):
		pk=self.kwargs['pk']
		return Product.objects.filter(pk=pk)

class ProductCreateView(CreateView):
	template_name="create_product.html"
	form_class=ProductForm
	form=ProductForm()
	success_url="/Product/products"
	object=None

class ProductDeleteView(DeleteView):
    model = Product
    success_url = "/Product/products"
    context_object_name = "products"
    template_name = 'products_list.html'
    success_message='Deleted successfuly'

    def get(self, request, *args, **kwargs):
        messages.warning(request, "Are you sure you want to delete the product?: ")
        return super(ProductDeleteView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(ProductDeleteView, self).get_queryset()
        return qs.filter(owner=self.request.user)

