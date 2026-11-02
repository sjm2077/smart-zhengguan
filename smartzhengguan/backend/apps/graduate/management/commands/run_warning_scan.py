"""
管理命令：运行预警扫描
"""
from django.core.management.base import BaseCommand

from apps.graduate import warning_services


class Command(BaseCommand):
    help = "Run warning rule scan"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview only, do not create warning instances',
        )
        parser.add_argument(
            '--rules',
            type=str,
            help='Comma-separated rule IDs to scan',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        rule_ids = None

        if options['rules']:
            rule_ids = [int(rid) for rid in options['rules'].split(',')]

        self.stdout.write('Starting warning scan...')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be written'))

        result = warning_services.run_scan(rule_ids=rule_ids, dry_run=dry_run)

        self.stdout.write(
            self.style.SUCCESS(
                f"Scan completed: {result['total_rules']} rules, "
                f"{result['total_students_scanned']} students scanned"
            )
        )
        self.stdout.write(f"New warnings: {result['new_count']}")
        self.stdout.write(f"Duplicates skipped: {result['duplicate_count']}")
