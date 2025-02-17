from django.db import models, transaction
from django.forms.models import model_to_dict
from .element import Element
from .team import Team
from typing import List, Dict, Any
import hashlib
import json


class ElementGroupManager(models.Manager):
    def _hash_elements(self, elements: List) -> str:
        elements_list: List[Dict] = []
        for element in elements:
            el_dict = model_to_dict(element)
            [el_dict.pop(key) for key in ["event", "id", "group"]]
            elements_list.append(el_dict)
        return hashlib.md5(
            json.dumps(elements_list, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

    def create(self, *args: Any, **kwargs: Any):
        elements = kwargs.pop("elements")
        with transaction.atomic():
            kwargs["hash"] = self._hash_elements(elements)
            try:
                with transaction.atomic():
                    group = super().create(*args, **kwargs)
            except:
                return ElementGroup.objects.get(
                    hash=kwargs["hash"],
                    team_id=kwargs["team"].pk
                    if kwargs.get("team")
                    else kwargs["team_id"],
                )
            for element in elements:
                element.group = group
            for element in elements:
                setattr(element, "pk", None)
            Element.objects.bulk_create(elements)
            return group


class ElementGroup(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "hash"], name="unique hash for each team"
            )
        ]

    team: models.ForeignKey = models.ForeignKey(Team, on_delete=models.CASCADE)
    hash: models.CharField = models.CharField(max_length=400, null=True, blank=True)
    objects = ElementGroupManager()
