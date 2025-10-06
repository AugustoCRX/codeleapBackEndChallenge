# CodeLabTest/pagination.py
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from collections import OrderedDict

class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginação padrão com informações detalhadas
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page_size),
            ('results', data)
        ]))

class PostCursorPagination(CursorPagination):
    """
    Cursor pagination para feeds infinitos (mais eficiente)
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'
    cursor_query_param = 'cursor'