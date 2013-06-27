from django.shortcuts import render_to_response


def homepage(request, *args, **kwargs):
    return render_to_response('home/homepage.html', {})