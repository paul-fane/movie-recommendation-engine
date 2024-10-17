from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_http_methods

from ml import tasks as ml_tasks

from .models import Rating
from playlists.models import MovieProxy

@require_http_methods(['POST'])
def rate_movie_view(request):
    if not request.htmx:
        return HttpResponse("Not Allowed", status=400)
    object_id = request.POST.get('object_id')
    rating_value = request.POST.get("rating_value")
    if object_id is None or rating_value is None:
        response = HttpResponse("Skipping", status=200)
        response['HX-Trigger'] = 'did-skip-movie'
        return response
    user = request.user
    message = "You must <a href='/accounts/login'>login</a> to rate this."
    if user.is_authenticated:
        message = "<span class='bg-danger text-light py-1 px-3 rounded'>An error occured.</div>"
        ctype = ContentType.objects.get_for_model(MovieProxy, for_concrete_model=False)
        #ctype = ContentType.objects.get(app_label='playlists', model='MovieProxy')
        rating_obj = Rating.objects.create(content_type=ctype, object_id=object_id, value=rating_value, user=user)
        if rating_obj.content_object is not None:
            total_new_suggestions = request.session.get("total-new-suggestions") or 0
            items_rated = request.session.get('items-rated') or 0
            items_rated += 1
            request.session['items-rated'] = items_rated
            print('items_rated', items_rated)
            if items_rated % 5 == 0:
                print("trigger new suggestions")
                users_ids = [user.id]
                # apply_async() function in Celery is used to schedule the execution of a task asynchronously
                ml_tasks.batch_users_prediction_task.apply_async(kwargs ={
                    "users_ids": users_ids,
                    "start_page": total_new_suggestions,
                    "max_pages": 10
                }) # kwargs: A dictionary of keyword arguments to pass to the task.
            message = "<span class='bg-success text-light py-1 px-3 rounded'>Rating saved!</div>"
            response = HttpResponse(message, status=200)
            response['HX-Trigger-After-Settle'] = 'did-rate-movie'
            return response
    return HttpResponse(message, status=200)


# from django.contrib.contenttypes.models import ContentType
# from django.http import HttpResponseRedirect
# from django.shortcuts import render

# from .forms import RatingForm
# from .models import Rating

# def rate_object_view(request):
#     if not request.user.is_authenticated:
#         return HttpResponseRedirect('/')
#     if request.method == "POST":
#         form = RatingForm(request.POST)
#         if form.is_valid():
#             object_id = form.cleaned_data.get('object_id')
#             rating = form.cleaned_data.get('rating')
#             content_type_id = form.cleaned_data.get('content_type_id')
#             c_type = ContentType.objects.get_for_id(content_type_id)
#             obj = Rating.objects.create(
#                 content_type=c_type,
#                 object_id=object_id,
#                 value=rating,
#                 user=request.user
#             )
#             next_path = form.cleaned_data.get('next') # detail view
#             return HttpResponseRedirect(next_path)
#     return HttpResponseRedirect('/')