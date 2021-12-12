from rest_framework import pagination

class TransactionSummaryPaginator(pagination.LimitOffsetPagination):
    default_limit = 2
    page_query_param = 'page'