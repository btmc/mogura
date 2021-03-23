import mptt
from django.core.management.base import NoArgsCommand
from reports.models import report

class Command(NoArgsCommand):
    help = "Triggers rebuild of MPTT pointers on reports.report."

    def handle_noargs(self, **options):
        print "Rebuilding MPTT pointers for reports.report"
        mptt.register(report).tree.rebuild()
