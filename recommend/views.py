from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.shortcuts import render, get_object_or_404, redirect
from .forms import *
from django.http import Http404
from .models import Song, Myrating, MyList
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Case, When
import pandas as pd

# Create your views here.

def index(request):
    songs = Song.objects.all()
    query = request.GET.get('q')

    if query:
        songs = Song.objects.filter(Q(title__icontains=query)).distinct()
        return render(request, 'recommend/list.html', {'songs': songs})

    return render(request, 'recommend/list.html', {'songs': songs})


# Show details of the song
def detail(request, song_id):
    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404
    songs = get_object_or_404(Song, id=song_id)
    song = Song.objects.get(id=song_id)
    
    temp = list(MyList.objects.all().values().filter(song_id=song_id,user=request.user))
    if temp:
        update = temp[0]['watch']
    else:
        update = False
    if request.method == "POST":

        # For my list
        if 'watch' in request.POST:
            watch_flag = request.POST['watch']
            if watch_flag == 'on':
                update = True
            else:
                update = False
            if MyList.objects.all().values().filter(song_id=song_id,user=request.user):
                MyList.objects.all().values().filter(song_id=song_id,user=request.user).update(watch=update)
            else:
                q=MyList(user=request.user,song=song,watch=update)
                q.save()
            if update:
                messages.success(request, "Song added to your list!")
            else:
                messages.success(request, "Song removed from your list!")

            
        # For rating
        else:
            rate = request.POST['rating']
            if Myrating.objects.all().values().filter(song_id=song_id,user=request.user):
                Myrating.objects.all().values().filter(song_id=song_id,user=request.user).update(rating=rate)
            else:
                q=Myrating(user=request.user,song=song,rating=rate)
                q.save()

            messages.success(request, "Rating has been submitted!")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    out = list(Myrating.objects.filter(user=request.user.id).values())

    # To display ratings in the song detail page
    song_rating = 0
    rate_flag = False
    for each in out:
        if each['song_id'] == song_id:
            song_rating = each['rating']
            rate_flag = True
            break

    context = {'songs': songs,'song_rating':song_rating,'rate_flag':rate_flag,'update':update}
    return render(request, 'recommend/detail.html', context)


# MyList functionality
def watch(request):

    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404

    songs = Song.objects.filter(mylist__watch=True,mylist__user=request.user)
    query = request.GET.get('q')

    if query:
        songs = Song.objects.filter(Q(title__icontains=query)).distinct()
        return render(request, 'recommend/watch.html', {'songs': songs})

    return render(request, 'recommend/watch.html', {'songs': songs})


# To get similar songs based on user rating
def get_similar(song_name,rating,corrMatrix):
    similar_ratings = corrMatrix[song_name]*(rating-2.5)
    similar_ratings = similar_ratings.sort_values(ascending=False)
    return similar_ratings

# Recommendation Algorithm
def recommend(request):

    if not request.user.is_authenticated:
        return redirect("login")
    if not request.user.is_active:
        raise Http404


    song_rating=pd.DataFrame(list(Myrating.objects.all().values()))
    new_user=song_rating.user_id.unique().shape[0]
    print(new_user)
    current_user_id= request.user.id
	# if new user not rated any song
    if current_user_id>new_user:
        song=Song.objects.get(id=19)
        q=Myrating(user=request.user,song=song,rating=0)
        q.save()


    userRatings = song_rating.pivot_table(index=['user_id'],columns=['song_id'],values='rating')

    userRatings = userRatings.fillna(0,axis=1)
    corrMatrix = userRatings.corr(method='pearson')

    user = pd.DataFrame(list(Myrating.objects.filter(user=request.user).values())).drop(['user_id','id'],axis=1)
    user_filtered = [tuple(x) for x in user.values]
    song_id_watched = [each[0] for each in user_filtered]

    similar_songs = pd.DataFrame()
    for song,rating in user_filtered:
        similar_songs = similar_songs.append(get_similar(song,rating,corrMatrix),ignore_index = True)

    songs_id = list(similar_songs.sum().sort_values(ascending=False).index)
    songs_id_recommend = [each for each in songs_id if each not in song_id_watched]
    preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(songs_id_recommend)])
    song_list=list(Song.objects.filter(id__in = songs_id_recommend).order_by(preserved)[:10])

    context = {'song_list': song_list}
    return render(request, 'recommend/recommend.html', context)


# Register user
def signUp(request):
    form = UserForm(request.POST or None)

    if form.is_valid():
        user = form.save(commit=False)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user.set_password(password)
        user.save()
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("index")

    context = {'form': form}

    return render(request, 'recommend/signUp.html', context)


# Login User
def Login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("index")
            else:
                return render(request, 'recommend/login.html', {'error_message': 'Your account disable'})
        else:
            return render(request, 'recommend/login.html', {'error_message': 'Invalid Login'})

    return render(request, 'recommend/login.html')


# Logout user
def Logout(request):
    logout(request)
    return redirect("login")
