from rest_framework.pagination import PageNumberPagination

from core.constants import PAGINATION_PAGE_SIZE


class PageNumberPagination(PageNumberPagination):
    page_size = PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
