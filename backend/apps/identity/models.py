import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from common.models import TimeStampedUUIDModel


class UserManager(BaseUserManager):
    """
    Custom user manager for the canonical User model.
    """

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be provided")
        username = username.strip()
        email = extra_fields.pop('email', None)
        if email:
            email = self.normalize_email(email).strip().lower()

        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('must_change_password', True)

        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('must_change_password', False)
        extra_fields.setdefault('status', 'ACTIVE')

        if not password:
            raise ValueError("Superusers must have a password.")

        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, TimeStampedUUIDModel):
    """
    Canonical User model for Identity & Access module.
    Physical table: 'users'.
    Governed by DATABASE_ARCHITECTURE.md Deliverable N.
    """

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('INACTIVE', 'Inactive'),
    ]

    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Canonical username (e.g. Enrollment number for students, staff code for faculty/admin)"
    )
    email = models.EmailField(
        max_length=254,
        null=True,
        blank=True,
        help_text="Optional contact/notification email"
    )
    # Password field from AbstractBaseUser maps to password_hash column in PostgreSQL
    password = models.CharField(
        max_length=255,
        db_column='password_hash',
        help_text="Hashed password string"
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="User lifecycle status (ACTIVE, SUSPENDED, INACTIVE)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user account is active"
    )
    must_change_password = models.BooleanField(
        default=True,
        help_text="Flag indicating mandatory password change on first login (ADR-004)"
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the Django admin site"
    )
    is_superuser = models.BooleanField(
        default=False,
        help_text="Designates administrative superuser privileges"
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['username'], name='idx_users_username'),
        ]

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


class Role(TimeStampedUUIDModel):
    """
    Physical table: 'roles'.
    Governed by DATABASE_ARCHITECTURE.md Deliverable H and Deliverable N.
    """
    SCOPE_CHOICES = [
        ('SYSTEM', 'System-wide'),
        ('DEPARTMENT', 'Department-scoped'),
        ('BATCH', 'Batch-scoped'),
        ('OWN', 'Self/Own-record scoped'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique role name (e.g. SYSTEM_ADMIN, HOD, FACULTY, STUDENT)"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed description of role responsibilities"
    )
    scope_type = models.CharField(
        max_length=30,
        choices=SCOPE_CHOICES,
        help_text="Scope granularity of this role: SYSTEM, DEPARTMENT, BATCH, or OWN"
    )

    class Meta:
        db_table = 'roles'
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.scope_type})"


class Permission(TimeStampedUUIDModel):
    """
    Physical table: 'permissions'.
    Governed by DATABASE_ARCHITECTURE.md Deliverable H and Deliverable N.
    """
    codename = models.CharField(
        max_length=150,
        unique=True,
        help_text="Unique permission identifier (e.g. identity.manage_users, students.view_record)"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Human-readable description of what this permission grants"
    )
    module = models.CharField(
        max_length=50,
        help_text="Owning bounded context / module (e.g. identity, academic, students)"
    )

    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['module', 'codename']

    def __str__(self):
        return f"{self.codename} [{self.module}]"


class RolePermission(TimeStampedUUIDModel):
    """
    Physical table: 'role_permissions'.
    M2M mapping between Roles and Permissions.
    Governed by DATABASE_ARCHITECTURE.md Deliverable H and Deliverable N.
    """
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='permission_roles'
    )

    class Meta:
        db_table = 'role_permissions'
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'permission'],
                name='uq_role_permissions'
            )
        ]

    def __str__(self):
        return f"{self.role.name} -> {self.permission.codename}"


class UserRole(TimeStampedUUIDModel):
    """
    Physical table: 'user_roles'.
    M2M mapping between Users and Roles with optional scope references.
    Governed by DATABASE_ARCHITECTURE.md Deliverable H and Deliverable N.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.RESTRICT,
        related_name='role_users'
    )
    scope_department_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Optional department scope reference (resolved when Academic Foundation is active)"
    )
    scope_batch_id = models.UUIDField(
        null=True,
        blank=True,
        help_text="Optional batch scope reference (resolved when Academic Foundation is active)"
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name='assigned_roles'
    )

    class Meta:
        db_table = 'user_roles'
        verbose_name = 'User Role'
        verbose_name_plural = 'User Roles'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'role', 'scope_department_id', 'scope_batch_id'],
                name='uq_user_roles'
            )
        ]

    def __str__(self):
        return f"{self.user.username} has {self.role.name}"


