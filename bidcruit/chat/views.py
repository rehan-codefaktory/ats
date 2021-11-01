from django.shortcuts import render, HttpResponse, redirect
from .models import  Friends, Messages
from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from rest_framework.parsers import JSONParser
from chat.serializers import MessageSerializer
from accounts.models import User
from candidate.models import CandidateSEO,CandidateProfile,Profile
from company.models import CompanyProfile

def getFriendsList(id):
    """
    Get the list of friends of the  user
    :param: user id
    :return: list of friends
    """
    try:
        user = User.objects.get(id=id)
        ids = list(user.friends_set.all())
        friends = []
        for id in ids:
            num = str(id)
            fr = User.objects.get(id=int(num))
            friends.append(fr)
        return friends
    except:
        return []


def getUserId(email):
    """
    Get the user id by the username
    :param username:
    :return: int
    """
    use = User.objects.get(email=email)
    id = use.id
    return id


def index(request):
    """
    Return the home page
    :param request:
    :return:
    """
    user_list = []
    if request.user.is_candidate:
        if request.user.is_candidate:
            messages = Messages.objects.filter(receiver_name=request.user.id, status=True)
            print('\n\nmessages>>>>>>>>>>>',messages)
            if messages:
                for mess in messages:
                    user_list.append(User.objects.get(id=mess.sender_name.id))
        print('user_list >>>>>>>>',user_list)
    else:
        messages = Messages.objects.filter(sender_name=request.user.id, status=True)
        if messages:
            for mess in messages:
                user_list.append(User.objects.get(id=mess.receiver_name.id))
    user_list=list(set(user_list))
    seo={}
    if request.user.is_candidate:
        seo = CandidateSEO.objects.get(candidate_id=request.user.id)
        profile_get=Profile.objects.get(candidate_id=request.user.id,active=True)
        userdata=CandidateProfile.objects.get(candidate_id=request.user.id,profile_id=profile_get.id)
    if request.user.is_company:
        userdata=CompanyProfile.objects.get(company_id=request.user.id)
    return render(request, "chat/Base.html", {'userdata':userdata,'seo':seo,'friends': user_list})


def search(request):
    """
    Search users page
    :param request:
    :return:
    """
    users = list(User.objects.all())
    for user in users:
        if user.email == request.user.email:
            users.remove(user)
            break
    if request.method == "POST":
        print("SEARCHING!!")
        query = request.POST.get("search")
        user_ls = []
        for user in users:
            if query in user.first_name or query in user.email:
                user_ls.append(user)
        return render(request, "chat/search.html", {'users': user_ls, })
    try:
        users = users[:10]
    except:
        users = users[:]
    id = User.objects.filter(email=email)
    friends = getFriendsList(id)
    seo={}
    if request.user.is_candidate:
        seo = CandidateSEO.objects.get(candidate_id=request.user.id)
        profile_get=Profile.objects.get(candidate_id=request.user.id,active=True)
        userdata=CandidateProfile.objects.get(candidate_id=request.user.id,profile_id=profile_get.id)
    if request.user.is_company:
        userdata=CompanyProfile.objects.get(company_id=request.user.id)
    return render(request, "chat/search.html", {'userdata':userdata,'seo':seo,'users': users, 'friends': friends})


def addFriend(request, email):
    """
    Add a user to the friend's list
    :param request:
    :param name:
    :return:
    """
    email = request.user.email
    id = User.objects.get(email=email)
    friend = User.objects.get(email=email)
    curr_user = User.objects.get(id=id)
    print(curr_user.first_name)
    ls = curr_user.friends_set.all()
    flag = 0
    for username in ls:
        if username.friend == friend.id:
            flag = 1
            break
    if flag == 0:
        print("Friend Added!!")
        curr_user.friends_set.create(friend=friend.id)
        friend.friends_set.create(friend=id)
    return redirect("chat:search")


def chat(request, email):
    """
    Get the chat between two users.
    :param request:
    :param username:
    :return:
    """
    friend = User.objects.get(email=email)
    id = getUserId(request.user.email)
    curr_user = User.objects.get(id=id)
    messages = Messages.objects.filter(sender_name=id, receiver_name=friend.id) | Messages.objects.filter(sender_name=friend.id, receiver_name=id)

    if request.method == "GET":
        user_list = []
        if request.user.is_candidate:
            if request.user.is_candidate:
                messages_obj = Messages.objects.filter(receiver_name=request.user.id, status=True)
                print('\n\nmessages>>>>>>>>>>>', messages)
                if messages:
                    for mess in messages_obj:
                        user_list.append(User.objects.get(id=mess.sender_name.id))
            print('user_list >>>>>>>>', user_list)
        else:
            messages_obj = Messages.objects.filter(sender_name=request.user.id, status=True)
            if messages:
                for mess in messages_obj:
                    user_list.append(User.objects.get(id=mess.receiver_name.id))
        user_list=list(set(user_list))
    seo={}
    if request.user.is_candidate:
        seo = CandidateSEO.objects.get(candidate_id=request.user.id)
        profile_get=Profile.objects.get(candidate_id=request.user.id,active=True)
        userdata=CandidateProfile.objects.get(candidate_id=request.user.id,profile_id=profile_get.id)
    if request.user.is_company:
        userdata=CompanyProfile.objects.get(company_id=request.user.id)
    return render(request, "chat/messages.html",{'userdata':userdata,'seo':seo,'messages': messages,'friends': user_list,'curr_user': curr_user,
                                                     'friend': friend})


@csrf_exempt
def message_list(request, sender=None, receiver=None):
    if request.method == 'GET':
        messages = Messages.objects.filter(sender_name=sender, receiver_name=receiver, seen=False)
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        for message in messages:
            message.seen = True
            message.save()
        return JsonResponse(serializer.data, safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

