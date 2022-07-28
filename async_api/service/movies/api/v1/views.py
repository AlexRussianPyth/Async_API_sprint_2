from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from movies.models import Filmwork, Roles


class MoviesApiMixin:
    model = Filmwork
    http_method_names = ['get']

    def get_queryset(self):

        # Use predefined person roles for api output
        persons = {}
        for role in Roles:
            plural = (role.name + 's').lower()
            persons[plural] = ArrayAgg(
                        'persons__full_name',
                        distinct=True,
                        filter=Q(personfilmwork__role__icontains=role.name)
                        )

        queryset = Filmwork.objects.values(
            'id',
            'title',
            'description',
            'creation_date',
            'rating',
            'type',).annotate(
                genres=ArrayAgg('genres__name', distinct=True),
                **persons,
                # actors=ArrayAgg(
                #     'persons__full_name',
                #     distinct=True,
                #     filter=Q(personfilmwork__role__contains='actor')
                #     ),
                # directors=ArrayAgg(
                #     'persons__full_name',
                #     distinct=True,
                #     filter=Q(personfilmwork__role__contains='director')
                #     ),
                # writers=ArrayAgg(
                #     'persons__full_name',
                #     distinct=True,
                #     filter=Q(personfilmwork__role__contains='writer')
                #     ),
                )
        return queryset

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, **kwargs):

        full_queryset = self.get_queryset()

        paginator, page, page_queryset, is_paginated = self.paginate_queryset(full_queryset, self.paginate_by)

        page_number = self.request.GET.get('page')
        if page_number is None:
            page_number = 1
        elif page_number == 'last':
            page_number = paginator.num_pages
        page = paginator.get_page(page_number)

        results = []
        for object in page:
            results.append(object)

        context = {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev': page.previous_page_number() if page.has_previous() else None,
            'next': page.next_page_number() if page.has_next() else None,
            'results': results,
        }

        return context


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):
    def get_context_data(self, **kwargs):
        object = kwargs['object'].values()
        context = list(object)[0]
        return context

    def get_object(self, queryset, pk):
        return queryset.filter(pk=pk)

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        self.object = self.get_object(self.get_queryset(), pk)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
