from datetime import timedelta

from django.utils import timezone

from misago.acl.testutils import override_acl
from misago.threads.api.postingendpoint import PostingInterrupt
from misago.threads.api.postingendpoint.floodprotection import FloodProtectionMiddleware
from misago.users.testutils import AuthenticatedUserTestCase


def get_middleware_for_testing(**kwargs):
    mock_kwargs = {
        'prefix': 'test',
        'mode': 0,

        'request': None,
        'user': None,

        'datetime': None,
        'parsing_result': None,

        'thread': None,
        'post': None,
    }
    mock_kwargs.update(kwargs)

    return FloodProtectionMiddleware(**mock_kwargs)


class FloodProtectionMiddlewareTests(AuthenticatedUserTestCase):
    def test_flood_protection_middleware_on_no_posts(self):
        """middleware sets last_posted_on on user"""
        self.user.update_fields = []
        self.assertIsNone(self.user.last_posted_on)

        middleware = get_middleware_for_testing(user=self.user)
        middleware.interrupt_posting(None)

        self.assertIsNotNone(self.user.last_posted_on)

    def test_flood_protection_middleware_old_posts(self):
        """middleware is not interrupting if previous post is old"""
        self.user.update_fields = []

        original_last_posted_on = timezone.now() - timedelta(days=1)
        self.user.last_posted_on = original_last_posted_on

        middleware = get_middleware_for_testing(user=self.user)
        middleware.interrupt_posting(None)

        self.assertTrue(self.user.last_posted_on > original_last_posted_on)

    def test_flood_protection_middleware_on_flood(self):
        """middleware is interrupting flood"""
        self.user.last_posted_on = timezone.now()

        with self.assertRaises(PostingInterrupt):
            middleware = get_middleware_for_testing(user=self.user)
            middleware.interrupt_posting(None)

    def test_flood_permission(self):
        """middleware is respects permission to flood for team members"""
        override_acl(self.user, {'can_omit_flood_protection': True})

        middleware = get_middleware_for_testing(user=self.user)
        self.assertFalse(middleware.use_this_middleware())
