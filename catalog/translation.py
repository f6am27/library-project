from modeltranslation.translator import register, TranslationOptions
from .models import Author, Category, Book


@register(Author)
class AuthorTranslationOptions(TranslationOptions):
    fields = ('full_name', 'bio')


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Book)
class BookTranslationOptions(TranslationOptions):
    fields = ('title', 'description')