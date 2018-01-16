from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.models import Category
from rango.models import Page
from rango.models import UserProfile, User
from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from datetime import datetime as dt
from rango.bing_search import run_query

#helper function to visitor_cookie_handler
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)

    if not val:
        val = default_val
    return val

# ------All the commented out part was of getting 
# page visits using cookies --------
#def visitor_cookie_handler(request, response):

def visitor_cookie_handler(request):

    #visits = int(request.COOKIES.get('visits', '1'))
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    
    #ast_visit_cookie = request.COOKIES.get('last_visit', str(dt.now()))
    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(dt.now()))

    last_visit_time = dt.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')

    if (dt.now() - last_visit_time).seconds > 0:
        visits = visits + 1

        request.session['last_visit'] = str(dt.now())
        #response.set_cookie('last_visit', str(dt.now()))
        
    else:
        visits = 1

        request.session['last_visit'] = last_visit_cookie
        #response.set_cookie('last_visit', last_visit_cookie)
        
    #response.set_cookie('visits', visits)
    request.session['visits'] = visits

def index(request):
    request.session.set_test_cookie()
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list,
                    'pages': page_list,
                     #request.COOKIES.get('visits', visitor_cookie_handler)
                    }

    visitor_cookie_handler(request)
    context_dict['visits'] = request.session['visits']
    
    response = render(request, 'rango/index.html', context_dict)
    #visitor_cookie_handler(request, response)
    
    return response

def about(request):
    request.session.set_test_cookie()

    visitor_cookie_handler(request)
  
    return render(request, 'rango/about.html', {'visits':request.session['visits']})

def show_category(request, category_name_slug):
    context_dict = {}

    try:
        category = Category.objects.get(slug=category_name_slug)
        category.views = category.views + 1

        pages = Page.objects.filter(category=category)

        context_dict['pages'] = pages
        context_dict['category'] = category
        context_dict['views'] = category.views
        
        category.save()
    except Category.DoesNotExist:
        context_dict['category'] = None
        context_dict['pages'] = None

    print("Show category wali: ",request)
    #search func
    context_dict['result_list'] = None
    context_dict['query'] = None
    if request.method == 'POST':
        query = request.POST.get('query')
        print(query)
        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)
            context_dict['result_list'] = result_list
            context_dict['query'] = query

    if not context_dict['query']:
        context_dict['query'] = category.name

    return render(request, 'rango/category.html', context_dict)

@login_required
def add_category(request):
    form = CategoryForm()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print(form.errors)
            
    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def like_category(request):
    print("Like category wali: ",request)
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        print("CAT_ID:",cat_id)
        likes = 0
        if cat_id:
            cat = Category.objects.get(id=int(cat_id))
            if cat:
                likes = cat.likes + 1
                cat.likes = likes
                cat.save()
    return HttpResponse(likes)

#helper function to suggest_category()
def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]
    return cat_list

def suggest_category(request):
    cat_list = []
    starts_with = ''

    if request.method == 'GET':
        starts_with = request.GET['suggestion']
    cat_list = get_category_list(8, starts_with)

    return render(request, 'rango/cats.html', {'cats': cat_list})

@login_required
def add_page(request, category_name_slug):
    print("Add page wali: ",request)
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None

    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                return show_category(request, category_name_slug)
        else:
            print(form.errors)
    
    return render(request, 'rango/add_page.html', {'form': form, 'category': category})

@login_required
def auto_add_page(request):
    cat_id = None
    url = None
    title = None
    context_dict ={}

    print("Auto add page wali: ",request)
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)
            pages  = Page.objects.filter(category=category).order_by('-views')
            context_dict['pages'] = pages

    return render(request, 'rango/page_list.html', context_dict)

def track_url(request):
    pid=None
    if request.method == 'GET':
        if 'page_id' in request.GET:
            pid = request.GET['page_id']
            print(pid)

            page = Page.objects.get(id=pid)
            page.views = page.views + 1
            page.save()
        
            return redirect(page.url)
        else:
            return redirect('/rango/')

def search(request):
    result_list = []
    query = ""
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)
    return render(request, 'rango/search.html', {'result_list': result_list, 'query':query})

'''
def register(request):
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            
            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            
            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form =UserProfileForm()

    return render(request, 'rango/register.html', {'user_form': user_form, 'profile_form': profile_form, 'registered': registered})

def user_login(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            #print("Invalid login details: {0}, {1}".format(username, password))
            return render(request, 'rango/login.html', {'msg':"Invalid login credentials. Please try again."})
    else:
        return render(request, 'rango/login.html', {})

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('rango:index'))
'''

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})


@login_required
def register_profile(request):
    form = UserProfileForm()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()

            return redirect('/rango/')
        else:
            print(form.errors)

    context_dict = {'form':form}

    return render(request, 'rango/profile_registration.html', context_dict)

@login_required
def profile(request, username):
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('/rango/')

    userprof = UserProfile.objects.get_or_create(user=user)[0]
    form = UserProfileForm({'website': userprof.website, 'picture': userprof.picture})
    
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=userprof)
        if form.is_valid():
            form.save(commit=True)
            return redirect('rango:profile', user.username)
        else:
            print(form.errors)

    return render(request, 'rango/profile.html', {'userprofile': userprof, 'selecteduser': user, 'form': form})


def list_profiles(request):
    userprofile_list = User.objects.all()

    return render(request, 'rango/list_profiles.html', {'userprofile_list': userprofile_list})
