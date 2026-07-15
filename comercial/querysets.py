# comercial/querysets.py
"""
Centraliza a lógica de filtragem de querysets baseada nas permissões do usuário.
Elimina a duplicação de blocos if/else espalhados nas views.
"""
from django.db import models
from django.db.models import Q


class OportunidadeQuerySet(models.QuerySet):
    def para_usuario(self, user):
        """
        Retorna oportunidades visíveis para o usuário autenticado.
        - Superusuários e membros do grupo 'Gerência' veem tudo.
        - Vendedores comuns veem apenas as suas próprias oportunidades.
        """
        if user.is_superuser or user.groups.filter(name='Gerência').exists():
            return self
        return self.filter(vendedor=user)


class OportunidadeManager(models.Manager):
    def get_queryset(self):
        return OportunidadeQuerySet(self.model, using=self._db)

    def para_usuario(self, user):
        return self.get_queryset().para_usuario(user)


class ClienteQuerySet(models.QuerySet):
    def para_usuario(self, user):
        """
        Retorna clientes visíveis para o usuário autenticado.
        - Superusuários e membros do grupo 'Gerência' veem todos.
        - Vendedores veem apenas clientes da sua carteira ou com oportunidades suas.
        """
        if user.is_superuser or user.groups.filter(name='Gerência').exists():
            return self
        return self.filter(
            Q(vendedor=user) | Q(oportunidades__vendedor=user)
        ).distinct()


class ClienteManager(models.Manager):
    def get_queryset(self):
        return ClienteQuerySet(self.model, using=self._db)

    def para_usuario(self, user):
        return self.get_queryset().para_usuario(user)
