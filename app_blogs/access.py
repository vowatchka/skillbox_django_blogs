from django.contrib.auth.mixins import UserPassesTestMixin


def has_access(request):
    if not request.user.is_authenticated:
        return False
    
    username = request.resolver_match.kwargs.get("username")
    if username:
        return request.user.username == username
    return True


class UserAccessMixin(UserPassesTestMixin):
    def test_func(self):
        if hasattr(self, "request"):
            return has_access(self.request)
        return True