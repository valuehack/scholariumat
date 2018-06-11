from django.contrib import admin

from .models import Book, Author, Collection


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    raw_id_fields = ['authors']
    search_fields = ['description']
    list_display = ['title', 'get_authors']
    list_filter = ['year']

    def get_authors(self, obj):
        return ", ".join([author.__str__() for author in obj.authors.all()])


admin.site.register(Author)
admin.site.register(Collection)
