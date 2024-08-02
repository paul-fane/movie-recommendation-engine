from django.http import Http404
from django.views.generic import ListView, DetailView
from django.utils import timezone

from netflix.db.models import PublishStateOptions


from .mixins import PlaylistMixin
from .models import Playlist, MovieProxy, TVShowProxy, TVShowSeasonProxy

class SearchView(PlaylistMixin, ListView):
    def get_context_data(self):
        context = super().get_context_data()
        query = self.request.GET.get("q")
        if query is not None:
            context['title'] = f"Searched for {query}"
        else:
            context['title'] = 'Perform a search'
        return context
    
    def get_queryset(self):
        query = self.request.GET.get("q") # request.GET = {}
        return Playlist.objects.all().movie_or_show().search(query=query)



class MovieListView(PlaylistMixin, ListView):
    queryset = MovieProxy.objects.all()
    title = "Movies"

class MovieDetailView(PlaylistMixin, DetailView):
    template_name = 'playlists/movie_detail.html'
    queryset = MovieProxy.objects.all()

class PlaylistDetailView(PlaylistMixin, DetailView):
    template_name = 'playlists/playlist_detail.html'
    queryset = Playlist.objects.all()

class TVShowListView(PlaylistMixin, ListView):
    queryset = TVShowProxy.objects.all()
    title = "TV Shows"

class TVShowDetailView(PlaylistMixin, DetailView):
    template_name = 'playlists/tvshow_detail.html'
    queryset = TVShowProxy.objects.all()


class TVShowSeasonDetailView(PlaylistMixin, DetailView):
    template_name = 'playlists/season_detail.html'
    queryset = TVShowSeasonProxy.objects.all()

    def get_object(self):
        kwargs = self.kwargs
        show_slug = kwargs.get("showSlug")
        season_slug = kwargs.get("seasonSlug")
        now = timezone.now()
        try:
            obj = TVShowSeasonProxy.objects.get(
                state=PublishStateOptions.PUBLISH,
                publish_timestamp__lte=now,
                parent__slug__iexact=show_slug,
                slug__iexact=season_slug
            )
        except TVShowSeasonProxy.MultipleObjectsReturned:
            qs = TVShowSeasonProxy.objects.filter(
                parent__slug__iexact=show_slug,
                slug__iexact=season_slug
            ).published()
            obj = qs.first()
            # log this
        except:
            raise Http404
        return obj


        # qs = self.get_queryset().filter(parent__slug__iexact=show_slug, slug__iexact=season_slug)
        # if not qs.count() == 1:
        #     raise Http404
        # return qs.first()

class FeaturedPlaylistListView(PlaylistMixin, ListView):
    template_name = 'playlists/featured_list.html'
    queryset = Playlist.objects.featured_playlists()
    title = "Featured"
    
    
    
    
    
#####################


SORTING_CHOICES = {
    "popular": "popular",
    "unpopular": "unpopular",
    "top rated": "-rating_avg",
    "low rated": "rating_avg",
    "recent": "-release_date",
    "old": "release_date"
}


class MovieListView(ListView):
    paginate_by = 100
    # context -> object_list

    def get_queryset(self):
        request = self.request
        sort = request.GET.get('sort') or request.session.get('movie_sort_order') or 'popular'
        qs =  MovieProxy.objects.all()
        if sort is not None:
            request.session['movie_sort_order'] = sort
            if sort == 'popular':
                return qs.popular()
            elif sort == 'unpopular':
                return qs.popular(reverse=True)
            qs = qs.order_by(sort)
        print(qs.first())
        return qs

    def get_template_names(self):
        request = self.request
        if request.htmx:
            return ['movies/snippet/list.html']
        return ['movies/list-view.html']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        request = self.request
        user = request.user
        context['sorting_choices'] = SORTING_CHOICES
        if user.is_authenticated:
            object_list = context['object_list']
            object_ids = [x.id for x in object_list]
            my_ratings =  user.rating_set.playlists().as_object_dict(object_ids=object_ids)
            context['my_ratings'] = my_ratings
        return context


movie_list_view = MovieListView.as_view()

class MovieDetailView(DetailView):
    template_name = 'movies/detail.html'
    # context -> object -> id
    queryset = MovieProxy.objects.all()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        request = self.request
        user = request.user
        if user.is_authenticated:
            object = context['object']
            object_ids = [object.id]
            my_ratings =  user.rating_set.playlists().as_object_dict(object_ids=object_ids)
            context['my_ratings'] = my_ratings
        return context


movie_detail_view = MovieDetailView.as_view()


class MovieInfiniteRatingView(MovieDetailView):
    def get_object(self):
        user = self.request.user
        # exclude_ids = []
        # if user.is_authenticated:
        #     exclude_ids = [x.object_id for x in user.rating_set.filter(active=True)]
        return MovieProxy.objects.all().order_by("?").first()
    
    def get_template_names(self):
        request = self.request
        if request.htmx:
            return ['movies/snippet/infinite.html']
        return ['movies/infinite-view.html']


movie_infinite_rating_view = MovieInfiniteRatingView.as_view()




class MoviePopularView(MovieDetailView):

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['endless_path'] = '/movies/popular/'
        return context
    
    def get_object(self):
        user = self.request.user
        exclude_ids = []
        if user.is_authenticated:
            exclude_ids = [x.object_id for x in user.rating_set.filter(active=True)]
        movie_id_options = MovieProxy.objects.all().popular().exclude(id__in=exclude_ids).values_list('id', flat=True)[:250]
        return MovieProxy.objects.filter(id__in=movie_id_options).order_by("?").first()
    
    def get_template_names(self):
        request = self.request
        if request.htmx:
            return ['movies/snippet/infinite.html']
        return ['movies/infinite-view.html']


movie_popular_view = MoviePopularView.as_view()