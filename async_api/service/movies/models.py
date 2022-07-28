import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Roles(models.TextChoices):
    DIRECTOR = 'DIR', _('Director')
    WRITER = 'SCW', _('Screenwriter')
    ACTOR = 'ACT', _('Actor')


class TimeStampedMixin(models.Model):
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Genre(UUIDMixin, TimeStampedMixin):
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'), blank=True)

    class Meta:
        db_table = "content\".\"genre"
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')

    def __str__(self):
        return f'{self.name}'


class Gender(models.TextChoices):
    MALE = 'male', _('male')
    FEMALE = 'female', _('female')


class Person(UUIDMixin, TimeStampedMixin):
    full_name = models.CharField(_('full name'), max_length=255)
    gender = models.TextField(_('gender'), choices=Gender.choices, null=True)

    class Meta:
        db_table = "content\".\"person"
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')

    def __str__(self):
        return self.full_name


class Filmwork(UUIDMixin, TimeStampedMixin):
    genres = models.ManyToManyField(Genre, through='GenreFilmwork', verbose_name=_('genres'))
    persons = models.ManyToManyField(Person, through='PersonFilmwork', verbose_name=_('persons'))
    title = models.CharField(_('title'), max_length=250)
    description = models.TextField(_('description'), blank=True)
    creation_date = models.DateField(_('creation_date'))
    rating = models.FloatField(_('rating'), blank=True,
                               validators=[MinValueValidator(0),
                                           MaxValueValidator(100)])

    class FilmTypes(models.TextChoices):
        MOVIE = 'movie', _('movie')
        TV_SHOW = 'show', _('show')

    type = models.CharField(
        _('type'),
        max_length=5,
        choices=FilmTypes.choices,
        default=FilmTypes.MOVIE,
    )

    class Meta:
        db_table = "content\".\"film_work"
        verbose_name = _('Film Work')
        verbose_name_plural = _('Film Works')

    def __str__(self):
        return self.title


class PersonFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE, verbose_name=_('Filmwork'))
    person = models.ForeignKey(Person, on_delete=models.CASCADE, verbose_name=_('Person'))
    created = models.DateTimeField(_('created'), auto_now_add=True)

    role = models.CharField(_('role'), max_length=50, null=False, choices=Roles.choices, default=Roles.ACTOR)

    class Meta:
        db_table = "content\".\"person_film_work"
        indexes = [models.Index(fields=['film_work_id', 'person_id', 'role'])]

    def __str__(self):
        return f"{self.film_work}-{self.person} relation"


class GenreFilmwork(UUIDMixin):
    film_work = models.ForeignKey(Filmwork, on_delete=models.CASCADE, verbose_name=_('Filmwork'))
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name=_('Genre'), )
    created = models.DateTimeField(_('created'), auto_now_add=True)

    class Meta:
        db_table = "content\".\"genre_film_work"
        indexes = [models.Index(fields=['film_work_id', 'genre_id'])]

    def __str__(self):
        return f"{self.film_work}-{self.genre} relation"
