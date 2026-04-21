"""
products/management/commands/seed_data.py
Run: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product
from orders.models import Coupon

CATEGORIES = [
    {'name': 'One Sound Crackers', 'icon': '💥', 'slug': 'one-sound'},
    {'name': 'Wala Items',         'icon': '🎵', 'slug': 'wala-items'},
    {'name': 'Bomb',               'icon': '💣', 'slug': 'bomb'},
    {'name': 'Flower Pots',        'icon': '🌸', 'slug': 'flower-pots'},
    {'name': 'Ground Chakkar',     'icon': '🌀', 'slug': 'ground'},
    {'name': 'Candles',            'icon': '🕯️', 'slug': 'candles'},
    {'name': 'Rockets',            'icon': '🚀', 'slug': 'rockets'},
    {'name': 'Fountains',          'icon': '⛲', 'slug': 'fountains'},
    {'name': 'Showers',            'icon': '🌟', 'slug': 'showers'},
    {'name': 'Premium Products',   'icon': '👑', 'slug': 'premium-products'},
    {'name': 'Sky Shots',          'icon': '🎆', 'slug': 'sky-shots'},
    {'name': 'Repeating Skyshots', 'icon': '🎇', 'slug': 'repeating-skyshots'},
    {'name': 'Sparklers',          'icon': '✨', 'slug': 'sparklers'},
    {'name': 'Matches',            'icon': '🔥', 'slug': 'matches'},
    {'name': 'Gift Boxes',         'icon': '🎁', 'slug': 'gift-boxes'},
    {'name': 'Combo Items',        'icon': '🎊', 'slug': 'combo-packs'},
]

PRODUCTS = [
    {'name': 'Gold Sparklers 10cm',        'category': 'sparklers',           'price': 50,   'original_price': 75,   'stock': 500, 'featured': True, 'image_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'},
    {'name': 'Silver Sparklers 20cm',      'category': 'sparklers',           'price': 80,   'original_price': 110,  'stock': 300, 'featured': False, 'image_url': 'https://images.unsplash.com/photo-1467810563316-b5476525c0f9?w=400'},
    {'name': 'Color Sparklers Pack',       'category': 'sparklers',           'price': 120,  'original_price': 160,  'stock': 200, 'featured': True, 'image_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'},
    {'name': 'Sky King Rocket',            'category': 'rockets',             'price': 150,  'original_price': 200,  'stock': 100, 'featured': True, 'image_url': 'https://images.unsplash.com/photo-1533922922960-9fceb9ef4733?w=400'},
    {'name': 'Whistling Rocket 5-Pack',    'category': 'rockets',             'price': 250,  'original_price': 320,  'stock': 80,  'featured': False, 'image_url': 'https://images.unsplash.com/photo-1533922922960-9fceb9ef4733?w=400'},
    {'name': 'Thunder Rocket',             'category': 'rockets',             'price': 180,  'original_price': 220,  'stock': 60,  'featured': False, 'image_url': 'https://images.unsplash.com/photo-1533922922960-9fceb9ef4733?w=400'},
    {'name': 'Classic Flower Pot',         'category': 'flower-pots',         'price': 90,   'original_price': 120,  'stock': 150, 'featured': True, 'image_url': 'https://images.unsplash.com/photo-1467810563316-b5476525c0f9?w=400'},
    {'name': 'Giant Flower Pot',           'category': 'flower-pots',         'price': 200,  'original_price': 260,  'stock': 70,  'featured': False, 'image_url': 'https://images.unsplash.com/photo-1467810563316-b5476525c0f9?w=400'},
    {'name': 'Atom Bomb',                  'category': 'one-sound',        'price': 100,  'original_price': 130,  'stock': 200, 'featured': False, 'image_url': 'https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=400'},
    {'name': 'Laxmi Bomb Box of 10',       'category': 'one-sound',        'price': 60,   'original_price': 80,   'stock': 400, 'featured': True, 'image_url': 'https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=400'},
    {'name': 'Multi-Color Sky Shot',       'category': 'sky-shots',           'price': 350,  'original_price': 450,  'stock': 50,  'featured': True, 'image_url': 'https://images.unsplash.com/photo-1533922922960-9fceb9ef4733?w=400'},
    {'name': '7-Shot Sky Cracker',         'category': 'sky-shots',           'price': 500,  'original_price': 650,  'stock': 40,  'featured': True, 'image_url': 'https://images.unsplash.com/photo-1533922922960-9fceb9ef4733?w=400'},
    {'name': 'Diwali Gift Box Small',      'category': 'gift-boxes',          'price': 799,  'original_price': 999,  'stock': 30,  'featured': True, 'image_url': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400'},
    {'name': 'Diwali Gift Box Large',      'category': 'gift-boxes',          'price': 1499, 'original_price': 1999, 'stock': 20,  'featured': True, 'image_url': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400'},
    {'name': 'Rainbow Fountain',           'category': 'fountains',           'price': 140,  'original_price': 180,  'stock': 90,  'featured': False, 'image_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'},
    {'name': 'Color Waterfall Fountain',   'category': 'fountains',           'price': 220,  'original_price': 280,  'stock': 60,  'featured': True, 'image_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'},
    {'name': 'Repeating Sky Star',         'category': 'repeating-skyshots',  'price': 450,  'original_price': 580,  'stock': 35,  'featured': True, 'image_url': 'https://images.unsplash.com/photo-1533922922960-9fceb9ef4733?w=400'},
    {'name': 'Butterfly Kids Pack',        'category': 'showers',        'price': 75,   'original_price': 100,  'stock': 250, 'featured': True, 'image_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'},
    {'name': 'Ground Chakkar Set',         'category': 'ground',              'price': 120,  'original_price': 150,  'stock': 180, 'featured': False, 'image_url': 'https://images.unsplash.com/photo-1467810563316-b5476525c0f9?w=400'},
    # ── Combo Packs ──
    {'name': 'Budget Blast Combo',          'category': 'combo-packs',         'price': 2999, 'original_price': 5000,  'stock': 50,  'featured': True,  'image_url': 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400',
     'description': 'Budget la irundhaalum Blast la compromise illa! Perfect starter pack for a happy Diwali. Includes sparklers, ground chakkars, flower pots and more.'},
    {'name': 'Vera Level Combo',            'category': 'combo-packs',         'price': 4999, 'original_price': 8000,  'stock': 40,  'featured': True,  'image_url': 'https://images.unsplash.com/photo-1533922922960-9fceb9ef4733?w=400',
     'description': 'Idhu vechaa Diwali vera level dhaan! Sound + Light + Full fun combo. Rockets, sky shots, bombs and premium sparklers.'},
    {'name': 'Area King Combo',             'category': 'combo-packs',         'price': 6999, 'original_price': 10000, 'stock': 30,  'featured': True,  'image_url': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400',
     'description': 'Indha combo vaanguna neenga dhaan area king! Full set for family and friends celebration. Premium selection across all categories.'},
    {'name': 'Royal Celebration Combo',     'category': 'combo-packs',         'price': 9999, 'original_price': 15000, 'stock': 20,  'featured': True,  'image_url': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400',
     'description': 'Grand ah celebrate panna ready ah irunga! Full skyshots + premium crackers set for a truly royal Diwali experience.'},
    {'name': 'Ultimate Diwali Thiruvizha Combo', 'category': 'combo-packs',    'price': 14999,'original_price': 20000, 'stock': 15,  'featured': True,  'image_url': 'https://images.unsplash.com/photo-1467810563316-b5476525c0f9?w=400',
     'description': 'Indha combo vechaa unga veedu dhaan Diwali center! Grand celebration. Maximum fireworks. Unlimited happiness. The ultimate Diwali experience.'},
]

COUPONS = [
    # DIWALI5: 5% off on orders above ₹5,000 (as displayed in banners)
    {'code': 'DIWALI5', 'discount_type': 'percent', 'discount_value': 5, 'min_order_value': 5000, 'max_uses': 500, 'excluded_category_slugs': 'gift-boxes,combo-packs'},
]


class Command(BaseCommand):
    help = 'Seed the database with categories, products, and coupons'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding Lakshmi Crackers data...\n')

        cat_map = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={'name': cat_data['name'], 'icon': cat_data['icon'], 'is_active': True}
            )
            cat_map[cat_data['slug']] = cat
            self.stdout.write(f'  {"✅ Created" if created else "⏭  Exists"} category: {cat.name}')

        for p in PRODUCTS:
            category = cat_map.get(p['category'])
            slug = slugify(p['name'])
            _, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name':           p['name'],
                    'category':       category,
                    'price':          p['price'],
                    'original_price': p.get('original_price'),
                    'stock':          p['stock'],
                    'is_featured':    p.get('featured', False),
                    'image_url':      p.get('image_url', ''),
                    'description':    p.get('description', ''),
                    'is_active':      True,
                }
            )
            self.stdout.write(f'  {"✅ Created" if created else "⏭  Exists"} product: {p["name"]}')

        for c in COUPONS:
            _, created = Coupon.objects.get_or_create(
                code=c['code'],
                defaults={
                    'discount_type':           c['discount_type'],
                    'discount_value':           c['discount_value'],
                    'min_order_value':          c['min_order_value'],
                    'max_uses':                 c['max_uses'],
                    'is_active':                True,
                    'excluded_category_slugs':  c.get('excluded_category_slugs', 'gift-boxes,combo-packs'),
                }
            )
            self.stdout.write(f'  {"✅ Created" if created else "⏭  Exists"} coupon: {c["code"]}')

        self.stdout.write(self.style.SUCCESS('\n🎆 Seed complete!'))
