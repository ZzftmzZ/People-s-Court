from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Autentica por nome de usuário OU e-mail (case-insensitive).

    Se houver contas antigas com e-mail duplicado, tenta a senha em cada uma
    (nunca escolhe uma conta sem validar a senha).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or not password:
            return None
        username = username.strip()
        candidates = User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).order_by('date_joined')
        for user in candidates:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        # mitiga timing attack quando não há conta
        if not candidates:
            User().set_password(password)
        return None
