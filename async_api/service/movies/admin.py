from django.contrib import admin

from .models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified')
    search_fields = ('name', 'description', 'id')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'get_roles', 'created', 'modified')
    search_fields = ('full_name', 'id', 'modified')
    list_prefetch_related = ['personfilmwork_set']

    def get_queryset(self, request):
        queryset = (
            super().get_queryset(request).prefetch_related(*self.list_prefetch_related)
        )
        return queryset

    def get_roles(self, obj):
        all_roles = set([filmwork.role for filmwork in obj.personfilmwork_set.all()])
        return ', '.join(all_roles)

    get_roles.short_description = 'Профиль деятельности'


class GenreFilmworkInline(admin.TabularInline):
    model = GenreFilmwork
    autocomplete_fields = ('genre',)


class PersonFilmworkInline(admin.StackedInline):
    model = PersonFilmwork
    autocomplete_fields = ('person',)


@admin.register(Filmwork)
class FilmworkAdmin(admin.ModelAdmin):
    inlines = (GenreFilmworkInline, PersonFilmworkInline)
    list_display = ('title', 'type', 'get_genres', 'creation_date', 'rating', 'created', 'modified')
    list_prefetch_related = ['genres']

    def get_queryset(self, request):
        queryset = (
            super().get_queryset(request).prefetch_related(*self.list_prefetch_related)
        )
        return queryset

    def get_genres(self, obj):
        return ', '.join([genre.name for genre in obj.genres.all()])

    get_genres.short_description = 'Жанры фильма'

    list_filter = ('type', 'rating')
    search_fields = ('title', 'description', 'id')
