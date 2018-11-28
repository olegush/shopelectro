"""
Test catalog command, which call other commands like price and excel.

Note: tests running pretty long.
"""
from collections import defaultdict
import glob
import os
import random
import unittest
import uuid
from unittest import mock
from xml.etree import ElementTree

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, tag

from shopelectro.management.commands._update_catalog import (
    update_products, update_tags
)
from shopelectro.models import Category, Product, Tag, TagGroup

"""
@todo #179 Раздели тесты класса UpdateProducts на интеграционные и модульные.
 1. Используй файлы с фикстурами для модульных тестов, чтобы добиться стабильности.
 2. Тестируй скачивание файлов с FTP отдельно.
"""


def get_tag_as_dict(group: str, tag: str):
    return {
        str(uuid.uuid4()): {
            'name': group,
            'tags': {uuid.uuid4(): {'name': tag}}
        }
    }


# @todo #603:30m Resurrect update_catalog tests.
#  Now we have problems with files downloading.
@tag('slow')
@unittest.skip
class UpdateProducts(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command('update_catalog', '--recipients', 'username@example.com')
        super(UpdateProducts, cls).setUpTestData()

    def test_products_in_db(self):
        """Should be more than 3K products in DB."""
        self.assertGreaterEqual(Product.objects.count(), 3000)

    def test_product_has_all_fields(self):
        """Some product has all the fields."""
        product = random.choice(Product.objects.all())
        self.assertIsNotNone(product.id)
        self.assertIsNotNone(product.vendor_code)
        self.assertIsNotNone(product.price)
        self.assertIsNotNone(product.wholesale_small)
        self.assertIsNotNone(product.wholesale_medium)
        self.assertIsNotNone(product.wholesale_large)

    def test_delete_xml(self):
        """Delete XML files after process."""
        file_paths = glob.glob(
            os.path.join(settings.ASSETS_DIR, settings.FTP_IP, '**/*.xml'),
            recursive=True
        )

        self.assertEqual(len(file_paths), 0)

    def test_update_products(self):
        new_data = {'price': 12345.1}
        update_products_count = 30

        product_data = {
            str(product.uuid): new_data
            for product in Product.objects.all()[:update_products_count]
        }

        update_products.update(data=product_data)
        updated_products = Product.objects.filter(**new_data)

        self.assertEqual(len(updated_products), update_products_count)
        self.assertTrue(all(
            product.price == new_data['price']
            for product in updated_products))

    def test_create_products(self):
        create_count = 10
        tag_count = 2

        data = {
            'name': 'New product',
            'vendor_code': '123',
            'tags': Tag.objects.all()[:tag_count]
        }

        product_data = {
            str(uuid.uuid4()): data
            for _ in range(create_count)
        }

        updated_products = Product.objects.all()
        product_count = updated_products.count()

        update_products.create(data=product_data, updated_products=updated_products)

        self.assertEqual(product_count + create_count, Product.objects.count())
        self.assertEqual(create_count, Product.objects.filter(name=data['name']).count())

    # @todo #452:15m Resurrect delete prods test
    @unittest.expectedFailure
    def test_delete_products(self):
        save_product_count = 30

        product_data = {
            str(product.uuid): 'any data'
            for product in Product.objects.all()[:save_product_count]
        }

        update_products.delete(data=product_data)

        self.assertEqual(Product.objects.count(), save_product_count)

    def test_update_or_create_tags(self):
        create_count = 10
        tag_data = {
            str(uuid.uuid4()): {
                'name': 'New group',
                'tags': {uuid.uuid4(): {'name': 'New tag'}}
            } for _ in range(create_count)
        }

        updated_groups_count = TagGroup.objects.count()
        updated_tags_count = Tag.objects.count()

        update_tags.create_or_update(tag_data)

        self.assertEqual(updated_groups_count + create_count, TagGroup.objects.count())
        self.assertEqual(updated_tags_count + create_count, Tag.objects.count())


@tag('fast')
class GeneratePrices(TestCase):

    fixtures = ['dump.json']
    CATEGORY_TO_EXCLUDE = 'Category #1 of #Category #0 of #Category #1'

    @classmethod
    def setUpTestData(cls):
        cls.call_command_patched('price')
        super(GeneratePrices, cls).setUpTestData()

    @classmethod
    def tearDownClass(cls):
        for file_name in settings.UTM_PRICE_MAP.values():
            os.remove(cls.get_price_file_path(file_name))
        super(GeneratePrices, cls).tearDownClass()

    @classmethod
    def call_command_patched(cls, name):
        """Patch with test constants and call."""
        with mock.patch(
            'shopelectro.management.commands.price.Command.IGNORED_CATEGORIES_BY_TARGET',
            new_callable=mock.PropertyMock
        ) as target:
            target.return_value = defaultdict(list, {
                'GM': [cls.CATEGORY_TO_EXCLUDE]
            })
            call_command(name)

    @staticmethod
    def get_price_file_path(filename):
        return os.path.join(settings.ASSETS_DIR, filename)

    @classmethod
    def get_price_node(cls, filename):
        return ElementTree.parse(cls.get_price_file_path(filename))

    @classmethod
    def get_price_shop_node(cls, filename):
        return cls.get_price_node(filename).getroot().find('shop')

    @classmethod
    def get_price_categories_node(cls, filename):
        return cls.get_price_shop_node(filename).find('categories')

    @classmethod
    def get_price_offers_node(cls, filename):
        return cls.get_price_shop_node(filename).find('offers')

    def test_prices_exists(self):
        """Price command should generate various price-list files."""
        price_file_min_size = 10 ** 3  # ~1kb

        for name in settings.UTM_PRICE_MAP.values():
            file_name = self.get_price_file_path(name)
            self.assertIn(name, os.listdir(settings.ASSETS_DIR))
            size = os.stat(file_name).st_size
            self.assertGreaterEqual(size, price_file_min_size)

    def test_categories_in_price(self):
        categories_in_price = self.get_price_categories_node('priceru.xml')
        self.assertEqual(len(categories_in_price), Category.objects_.count())

    def test_categories_in_yandex_price(self):
        categories_in_yandex_price = self.get_price_categories_node('yandex.yml')
        self.assertEqual(
            len(categories_in_yandex_price),
            Category.objects_.get_categories_tree_with_pictures().count()
        )

    def test_categories_excluded_by_utm(self):
        """Price file should not contain it's excluded category."""
        def find_category(categories, name):
            for category in categories:
                if category.text.strip() == name:
                    return category
            return None
        included_name = 'Category #0 of #Category #0 of #Category #1'
        categories_node = self.get_price_categories_node('gm.yml')

        # check if find_category inner function is correct
        self.assertIsNotNone(
            find_category(
                categories=categories_node.findall('category'),
                name=included_name
            )
        )
        # check if category excluded
        self.assertIsNone(
            find_category(
                categories=categories_node.findall('category'),
                name=self.CATEGORY_TO_EXCLUDE
            )
        )

    def test_products_in_price(self):
        products_in_price = self.get_price_offers_node('priceru.xml')
        self.assertEqual(len(products_in_price), Product.objects.count())

    def test_products_in_gm_price_bounds(self):
        """GM.yml should contain only offers with price > CONST."""
        offers = self.get_price_offers_node('gm.yml').findall('offer')
        prices_are_in_bounds = all(
            float(offer.find('price').text) > settings.PRICE_GM_LOWER_BOUND
            for offer in offers
        )
        self.assertTrue(prices_are_in_bounds)

    def test_products_in_yandex_price(self):
        products_in_yandex_price = self.get_price_offers_node('yandex.yml')
        self.assertEqual(
            len(products_in_yandex_price),
            Product.objects.filter(page__images__isnull=False).distinct().count()
        )

    def test_brands(self):
        """Price contains brand data."""
        for price in settings.UTM_PRICE_MAP.values():
            offer = self.get_price_offers_node(price).find('offer')
            product = Product.objects.filter(id=offer.get('id')).first()
            self.assertEqual(
                product.get_brand_name(),
                offer.find(f'vendor').text,
            )
