from django.core.exceptions import PermissionDenied
from django.http import Http404


def is_manager(user):
    """Проверяет, состоит ли пользователь в группе модераторов"""
    return user.is_superuser or user.groups.filter(name="manager").exists()


def check_user_can_create(user, entity_name="объект"):
    """Запрещает модераторам создавать сущности"""
    if is_manager(user) and not user.is_superuser:
        raise PermissionDenied(f"Модераторам запрещено создавать {entity_name}")


def check_user_can_edit(user, obj, entity_name="объект"):
    """Проверяет, может ли пользователь редактировать объект"""
    if user.is_superuser or getattr(obj, "owner", None) == user:
        return
    raise PermissionDenied(f"Вы не можете редактировать чужой {entity_name}")


def check_user_can_delete(user, obj, entity_name="объект"):
    """Проверяет, может ли пользователь удалить объект"""
    if user.is_superuser or getattr(obj, "owner", None) == user:
        return
    raise PermissionDenied(f"Вы не можете удалить чужой {entity_name}")


def can_user_view(user, obj):
    """Проверяет доступ к карточке объекта"""
    if not user.is_authenticated:
        raise Http404("Информация недоступна")
    if not is_manager(user) and obj.owner != user:
        raise Http404("Информация недоступна")
