from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import TeachingClass, UserProfile


FULL_READ_ROLES = {"admin", "academic", "viewer"}
FULL_WRITE_ROLES = {"admin", "academic"}


def get_teaching_role(user):
    """Return a normalized role; an unprofiled account is not implicitly a viewer."""
    if not user or not user.is_authenticated:
        return "unassigned"
    if user.is_superuser or user.is_staff:
        return "admin"
    try:
        role = user.teaching_profile.role
    except UserProfile.DoesNotExist:
        return "unassigned"
    return role or "unassigned"


def get_linked_student_id(user):
    try:
        return user.teaching_profile.student_id
    except (UserProfile.DoesNotExist, AttributeError):
        return None


def get_linked_teacher_id(user):
    try:
        return user.teaching_profile.teacher_id
    except (UserProfile.DoesNotExist, AttributeError):
        return None


def teacher_course_ids(user):
    teacher_id = get_linked_teacher_id(user)
    if not teacher_id:
        return TeachingClass.objects.none().values_list("course_id", flat=True)
    return TeachingClass.objects.filter(
        teacher_id=teacher_id
    ).values_list("course_id", flat=True)


def scope_grade_queryset(queryset, user):
    """
    Restrict grade rows by role:
    - student: own published grades only;
    - teacher: grades for courses in their teaching classes;
    - admin/academic/viewer: existing read scope;
    - unassigned: no grade rows.
    """
    role = get_teaching_role(user)
    if role == "student":
        student_id = get_linked_student_id(user)
        if not student_id:
            return queryset.none()
        return queryset.filter(
            student_id=student_id,
            is_published=True,
        )
    if role == "teacher":
        teacher_id = get_linked_teacher_id(user)
        if not teacher_id:
            return queryset.none()
        return queryset.filter(
            course__teaching_classes__teacher_id=teacher_id
        ).distinct()
    if role in FULL_READ_ROLES:
        return queryset
    return queryset.none()


class TeachingRolePermission(BasePermission):
    """
    Authenticated users may read only the rows exposed by role-scoped querysets.
    Writes remain limited to administrators and academic administrators.
    """
    message = "当前账号没有执行此操作的权限。"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return get_teaching_role(request.user) in FULL_WRITE_ROLES
