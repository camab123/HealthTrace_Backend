from rest_framework import permissions

class IsStafforReadOnly(permissions.BasePermission):
    post_methods = ("POST")
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        if not request.user.is_staff and request.method not in self.post_methods:
            return True
        return False
        

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if obj.author == request.user:
            return True
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False