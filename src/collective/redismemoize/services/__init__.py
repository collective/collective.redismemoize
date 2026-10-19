"""The ``@redismemoize`` REST API endpoint."""

from collective.redismemoize import api
from plone.restapi.deserializer import json_body
from plone.restapi.exceptions import DeserializationError
from plone.restapi.services import Service
from zExceptions import BadRequest
from zExceptions import NotFound
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse


class StatusGet(Service):
    """``GET @redismemoize``: the status of this process's cache."""

    def reply(self) -> dict:
        """Return :func:`collective.redismemoize.api.status`.

        :returns: The status mapping.
        """
        return api.status()


@implementer(IPublishTraverse)
class InvalidatePost(Service):
    """``POST @redismemoize/invalidate``: drop cached values.

    The body names one function, ``{"function": "module.function"}``, or is
    empty (``{}``) to drop everything under the prefix.
    """

    def __init__(self, context, request):
        super().__init__(context, request)
        self.params: list[str] = []

    def publishTraverse(self, request, name: str) -> "InvalidatePost":
        """Collect the path segment after the service name.

        :param request: The request.
        :param name: The segment.
        :returns: This service.
        """
        self.params.append(name)
        return self

    def reply(self) -> dict:
        """Invalidate one function, or everything.

        :returns: ``{"function": ..., "removed": <Redis keys removed>}``.
        :raises NotFound: For any path other than ``invalidate``.
        :raises BadRequest: When ``function`` is not a non-empty string.
        """
        if self.params != ["invalidate"]:
            raise NotFound(self.request.URL)
        try:
            data = json_body(self.request)
        except DeserializationError as exc:
            raise BadRequest(f"The body must be a JSON object: {exc}") from exc
        if "function" not in data:
            return {"function": None, "removed": api.invalidate_all()}
        function = data["function"]
        if not isinstance(function, str) or not function:
            raise BadRequest("'function' must be a non-empty string.")
        return {"function": function, "removed": api.invalidate(function)}
