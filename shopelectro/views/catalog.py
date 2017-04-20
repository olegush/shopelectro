"""
Shopelectro's catalog views.

NOTE: They all should be 'zero-logic'.
All logic should live in respective applications.
"""
from itertools import chain
from collections import defaultdict

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.template import Context, Template
from django.views.decorators.http import require_POST
from django_user_agents.utils import get_user_agent

from catalog.views import catalog
from images.models import Image
from pages import views as pages_views

from shopelectro import config
from shopelectro import models
from shopelectro.views.helpers import set_csrf_cookie

PRODUCTS_ON_PAGE_PC = 48
PRODUCTS_ON_PAGE_MOB = 10


def get_products_count(request):
    """Get Products count for response context depends on the `user_agent`."""
    mobile_view = get_user_agent(request).is_mobile
    return PRODUCTS_ON_PAGE_MOB if mobile_view else PRODUCTS_ON_PAGE_PC


# CATALOG VIEWS
class CategoryTree(catalog.CategoryTree):
    category_model = models.Category


@set_csrf_cookie
class ProductPage(catalog.ProductPage):
    pk_url_kwarg = None
    slug_url_kwarg = 'product_vendor_code'
    slug_field = 'vendor_code'

    queryset = (
        models.Product.objects
        .filter(category__isnull=False)
        .prefetch_related('product_feedbacks', 'page__images')
        .select_related('page')
    )

    def get_context_data(self, **kwargs):
        """Inject breadcrumbs into context."""
        context = super(ProductPage, self).get_context_data(**kwargs)
        feedbacks = (
            context[self.context_object_name]
            .product_feedbacks.all()
            .order_by('-date')
        )

        return {
            **context,
            'price_bounds': config.PRICE_BOUNDS,
            'feedbacks': feedbacks
        }


# SHOPELECTRO-SPECIFIC VIEWS
@set_csrf_cookie
class IndexPage(pages_views.CustomPageView):

    def get_context_data(self, **kwargs):
        """Extended method. Add product's images to context."""
        context = super(IndexPage, self).get_context_data(**kwargs)
        mobile_view = get_user_agent(self.request).is_mobile

        top_products = (
            models.Product.objects
            .filter(id__in=settings.TOP_PRODUCTS)
            .prefetch_related('category')
            .select_related('page')
        )

        images = Image.objects.get_main_images_by_pages(
            models.ProductPage.objects.filter(
                shopelectro_product__in=top_products
            )
        )

        categories = models.Category.objects.get_root_categories_by_products(top_products)

        prepared_top_products = []
        if not mobile_view:
            prepared_top_products = [
                (product, images.get(product.page), categories.get(product))
                for product in top_products
            ]

        return {
            **context,
            'category_tile': config.MAIN_PAGE_TILE,
            'prepared_top_products': prepared_top_products,
        }


def merge_products_and_images(products):
    images = Image.objects.get_main_images_by_pages(
        models.ProductPage.objects.filter(shopelectro_product__in=products)
    )

    return [
        (product, images.get(product.page))
        for product in products
    ]


URL_TAGS_TYPE_DELIMITER = '-or-'
URL_TAGS_GROUP_DELIMITER = '-and-'

TITLE_TAGS_TYPE_DELIMITER = ' или '
TITLE_TAGS_GROUP_DELIMITER = ' и '


def serialize_tags(tags: list,
                   attribute: str,
                   type_delimiter: str,
                   group_delimiter: str) -> str:
    # [Tag(name='220-v'), ...] -> {1: ['220-v', '...'}
    tags_by_group = defaultdict(list)
    for tag in tags:
        tags_by_group[tag.group.id].append(
            tag
        )
    # {1: ['220-v', '...']} -> {1: '220-v-or-...'}
    for group, tags in tags_by_group.items():
        tags_by_group[group] = type_delimiter.join(
            getattr(tag, attribute) for tag in tags
        )
    # {1: '220-v-or-...', ...} -> '220-v-or-...-and-...'
    return group_delimiter.join(
        tags for tags in tags_by_group.values()
    )


def serialize_url_tags(tags: list) -> str:
    return serialize_tags(
        tags, 'slug', URL_TAGS_TYPE_DELIMITER, URL_TAGS_GROUP_DELIMITER
    )


def parse_url_tags(tags: str) -> list:
    groups = tags.split(URL_TAGS_GROUP_DELIMITER)
    return chain(
        *(
            group.split(URL_TAGS_TYPE_DELIMITER) for group in groups
        )
    )


def serialize_title_tags(tags: list) -> str:
    return serialize_tags(
        tags, 'name', TITLE_TAGS_TYPE_DELIMITER, TITLE_TAGS_GROUP_DELIMITER
    )


@set_csrf_cookie
class CategoryPage(catalog.CategoryPage):

    def get_context_data(self, **kwargs):
        """Add sorting options and view_types in context."""
        context = super(CategoryPage, self).get_context_data(**kwargs)
        products_on_page = get_products_count(self.request)

        # tile is default view_type
        view_type = self.request.session.get('view_type', 'tile')

        category = context['category']

        sorting = int(self.kwargs.get('sorting', 0))
        sorting_option = config.category_sorting(sorting)

        all_products = (
            models.Product.objects
            .prefetch_related('page__images')
            .select_related('page')
            .get_by_category(category, ordering=(sorting_option, ))
        )

        group_tags_pairs = models.Tag.objects.get_group_tags_pairs(
            models.Tag.objects
            .filter(products__in=all_products)
            .prefetch_related('group')
        )

        tags = self.kwargs.get('tags')
        tags_metadata = None

        if tags:
            slugs = parse_url_tags(tags)
            tags = models.Tag.objects.filter(slug__in=list(slugs))

            all_products = all_products.filter(tags__in=tags)

            tags_titles = serialize_title_tags(tags)
            tags_description = None

            if category.seo_description_template:
                tags_description_template = Template(
                    category.seo_description_template
                )
                tags_description_context = Context({
                    'tags': tags_titles,
                    'title': category.name,
                })
                tags_description = tags_description_template.render(
                    tags_description_context
                )

            tags_metadata = {
                'tags': tags_titles,
                'title': '{category} {tags}'.format(
                    category=category.name, tags=tags_titles
                ),
                'description': tags_description,
            }

        products = all_products.get_offset(0, products_on_page)

        return {
            **context,
            'product_image_pairs': merge_products_and_images(products),
            'group_tags_pairs': group_tags_pairs,
            'total_products': all_products.count(),
            'sorting_options': config.category_sorting(),
            'sort': sorting,
            'tags': tags,
            'view_type': view_type,
            'tags_metadata': tags_metadata,
        }


def load_more(request, category_slug, offset=0, sorting=0, tags=None):
    """
    Load more products of a given category.

    :param sorting: preferred sorting index from CATEGORY_SORTING tuple
    :param request: HttpRequest object
    :param category_slug: Slug for a given category
    :param offset: used for slicing QuerySet.
    :return:
    """
    products_on_page = get_products_count(request)

    category = get_object_or_404(models.CategoryPage, slug=category_slug).model
    sorting_option = config.category_sorting(int(sorting))

    products = (
        models.Product.objects
        .prefetch_related('page__images')
        .select_related('page')
        .get_by_category(category, ordering=(sorting_option,))
    )

    if tags:
        products = products.get_by_tags(
            models.Tag.objects.filter(slug__in=list(parse_url_tags(tags)))
        )

    products = products.get_offset(int(offset), products_on_page)
    view = request.session.get('view_type', 'tile')

    return render(request, 'catalog/category_products.html', {
        'product_image_pairs': merge_products_and_images(products),
        'view_type': view,
        'prods': products_on_page,
    })


@require_POST
def save_feedback(request):
    def get_keys_from_post(*args):
        return {arg: request.POST.get(arg, '') for arg in args}

    product_id = request.POST.get('id')
    product = models.Product.objects.filter(id=product_id).first()
    if not (product_id and product):
        return HttpResponse(status=422)

    fields = ['rating', 'name', 'dignities', 'limitations', 'general']
    feedback_data = get_keys_from_post(*fields)

    models.ProductFeedback.objects.create(product=product, **feedback_data)
    return HttpResponse('ok')


@require_POST
def delete_feedback(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Not today, sly guy...')

    feedback_id = request.POST.get('id')
    feedback = models.ProductFeedback.objects.filter(id=feedback_id).first()
    if not (feedback_id and feedback):
        return HttpResponse(status=422)

    feedback.delete()
    return HttpResponse('Feedback with id={} was deleted.'.format(feedback_id))


class ProductsWithoutImages(catalog.ProductsWithoutImages):
    model = models.Product


class ProductsWithoutText(catalog.ProductsWithoutText):
    model = models.Product
