from django.urls import path

from clients.views import ClientListView, ClientDetailView, ClientCreateView, ClientUpdateView, ClientDeleteView, \
    client_search_view

app_name = "clients"

urlpatterns = [
    path("clients", ClientListView.as_view(), name="clients_list"),
    path("search/", client_search_view, name="client_search"),
    path("client/<int:pk>/", ClientDetailView.as_view(), name="client_detail"),
    path("create/",ClientCreateView.as_view(), name="client_create"),
    path("client/<int:pk>/update/", ClientUpdateView.as_view(), name="client_update"),
    path("client/<int:pk>/delete/", ClientDeleteView.as_view(), name="client_delete"),
]
