"""
core/management/commands/ensure_indexes.py

PostgreSQL version — replaces the MongoDB ensure_indexes command.

PostgreSQL automatically enforces all indexes defined in Meta.indexes and
unique constraints from unique=True fields during migrate. This command
verifies those indexes exist and shows a summary.

Run: python manage.py ensure_indexes
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Verify PostgreSQL indexes are in place (run after migrate)'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n📊 Checking PostgreSQL indexes...\n')

        # Expected indexes (created by Django migrations from Meta.indexes)
        expected = [
            ('products_product',  'idx_product_active_date'),
            ('products_product',  'idx_product_featured'),
            ('products_product',  'idx_product_category_active'),
            ('products_product',  'idx_product_price'),
            ('orders_order',      'idx_order_status_date'),
            ('orders_order',      'idx_order_email'),
            # Unique indexes (from unique=True fields — Django auto-names them)
            ('products_product',  'products_product_slug_key'),
            ('products_category', 'products_category_slug_key'),
            ('orders_coupon',     'orders_coupon_code_key'),
            ('users_user',        'users_user_email_key'),
        ]

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tablename, indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            existing = {(row[0], row[1]) for row in cursor.fetchall()}

        ok   = 0
        miss = 0
        for table, idx in expected:
            # Check both exact name and Django-generated names
            found = any(
                (t, i) in existing
                for (t, i) in existing
                if t == table and (i == idx or idx in i)
            )
            if found:
                self.stdout.write(self.style.SUCCESS(f'  ✓  {table}.{idx}'))
                ok += 1
            else:
                self.stdout.write(self.style.WARNING(f'  ✗  {table}.{idx} — NOT FOUND (run migrate)'))
                miss += 1

        self.stdout.write(f'\n  {ok} indexes verified, {miss} missing')
        if miss:
            self.stdout.write(self.style.WARNING(
                '\n  Run: python manage.py migrate\n'
                '  to create all missing indexes.\n'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n  ✅ All indexes in place.\n'))
