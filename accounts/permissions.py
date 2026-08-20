from rest_framework.permissions import BasePermission


class IsAdminOrSuperAdmin(BasePermission):
    message = "Only ADMIN or SUPERADMIN users can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ("ADMIN", "SUPERADMIN")
        )


class IsAuthenticatedOrAdminForWrite(BasePermission):
    message = "Only ADMIN or SUPERADMIN users can modify job positions."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return request.user.role in ("ADMIN", "SUPERADMIN")