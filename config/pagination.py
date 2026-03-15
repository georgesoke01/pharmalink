# config/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class FlexiblePageNumberPagination(PageNumberPagination):
    """Pagination configurable par le client via le paramètre `page_size`.

    Le client peut demander la taille qu'il veut dans la limite de `max_page_size`.
    Si aucun `page_size` n'est fourni, on utilise le PAGE_SIZE défini dans settings.

    Usage :
        GET /api/v1/pharmacies/?page=1&page_size=10   → mobile (léger)
        GET /api/v1/pharmacies/?page=1&page_size=50   → dashboard admin
        GET /api/v1/pharmacies/?page=1                → défaut (20)
    """

    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count":    self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "next":     self.get_next_link(),
            "previous": self.get_previous_link(),
            "results":  data,
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "count":       {"type": "integer"},
                "total_pages": {"type": "integer"},
                "next":        {"type": "string", "nullable": True},
                "previous":    {"type": "string", "nullable": True},
                "results":     schema,
            },
        }