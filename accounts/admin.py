from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Member, Admin, MembershipPlan


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        (_('Additional Info'), {'fields': ('phone',)}),
    )


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'duration_months', 'price', 'max_loans', 'is_active')
    list_filter = ('plan_type', 'is_active')
    search_fields = ('name',)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('membership_number', 'full_name', 'national_id',
                    'plan', 'membership_end', 'status')
    list_filter = ('status', 'plan')
    search_fields = ('membership_number', 'full_name', 'national_id')
    readonly_fields = ('membership_number',)


@admin.register(Admin)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)