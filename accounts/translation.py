from modeltranslation.translator import register, TranslationOptions
from .models import MembershipPlan


@register(MembershipPlan)
class MembershipPlanTranslationOptions(TranslationOptions):
    fields = ('name',)