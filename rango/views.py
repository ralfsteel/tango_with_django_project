from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext

from rango.models import Category, Page
from rango.forms import UserForm, UserProfileForm, CategoryForm, PageForm, PageForm, UserForm, UserProfileForm
from rango.bing_search import run_query

# Create your views here.
def index(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    request.session.set_test_cookie()
    context = RequestContext(request)
    category_list = Category.objects.order_by('id')
    context_dict = {
        'cat_list': cat_list,
        'categories': category_list
    }
    for category in category_list:
        category.url = category.name.replace(' ', '_')

    return render_to_response('rango/index.html', context_dict, context)


def category(request, category_name_url):
        context = RequestContext(request)
        cat_list = get_category_list()
        category_name = category_name_url

        context_dict = {
            'cat_list': cat_list,
            'category_name': category_name
        }
        try:
                category = Category.objects.get(name=category_name)
                context_dict['category'] = category
                pages = Page.objects.filter(category=category)
                context_dict['pages'] = pages
        except Category.DoesNotExist:
                pass
        return render_to_response('rango/category.html', context_dict, context)



@login_required
def profile(request):
    context = RequestContext(request)
    cat_list = get_category_list()

    u = User.objects.get(username=request.user)

    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None

    context_dict = {
        'cat_list': cat_list,
        'user': u,
        'userprofile': up
    }
    return render_to_response('rango/profile.html', context_dict, context)




def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url, context)

def add_category(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()


    context_dict = {
        'cat_list': cat_list,
        'form': form
    }

    return render_to_response('rango/add_category.html', context_dict,  context)



def detail(request):
   context = RequestContext(request)
   cat_list = get_category_list()
   form = CategoryForm()
   context_dic = {
       'cat_list': cat_list,
       'form': form
   }

   return render_to_response('rango/detail.html', context_dic, context)




def add_page(request, category_name_url):
    context = RequestContext(request)
    cat_list = get_category_list()
    print category_name_url
    category_name = category_name_url
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            page = form.save(commit=False)
            cat = Category.objects.get(name=category_name)
            page.category = cat
            page.views = 0
            page.save()
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {
        'cat_list': cat_list,
        'category_name_url': category_name_url,
        'category_name': category_name,
        'form': form
    }

    return render_to_response('rango/add_page.html', context_dict, context)






def register(request):
    if request.session.test_cookie_worked():
          print ">>>> TEST COOKIE WORKED!"
          request.session.delete_test_cookie()
    context = RequestContext(request)

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
            print user_form.errors, profile_form.errors
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response(
            'rango/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)

def user_login(request):
    context = RequestContext(request)

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("Your Rango account is disabled.")
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            return HttpResponse("Invalid login details supplied.")

    else:
        return render_to_response('rango/login.html', {}, context)


def some_view(request):
    if not request.user.is_authenticated():
        return HttpResponse("You are logged in.")
    else:
        return HttpResponse("You are not logged in.")


def search(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)

    context_dict = {
        'cat_list': cat_list,
        'result_list': result_list
    }

    return render_to_response('rango/search.html', context_dict, context)


def get_category_list(max_results=0, starts_with=''):
        cat_list = []
        if starts_with:
                cat_list = Category.objects.filter(name__istartswith=starts_with)
        else:
                cat_list = Category.objects.all()

        if max_results > 0:
                if len(cat_list) > max_results:
                        cat_list = cat_list[:max_results]

        for cat in cat_list:
                cat.url = cat.name
        return cat_list


def suggest_category(request):
        context = RequestContext(request)
        cat_list = []
        starts_with = ''
        if request.method == 'GET':
                starts_with = request.GET['suggestion']

        cat_list = get_category_list(8, starts_with)
        context_dict = {
            'cat_list': cat_list
        }

        return render_to_response('rango/category_list.html', context_dict, context)



@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can access text which is restricted!")

@login_required
def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/rango/')




@login_required
def like_category(request):
    context = RequestContext(request)
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
            likes = category.likes + 1
            category.likes = likes
            category.save()

    return HttpResponse(likes)






