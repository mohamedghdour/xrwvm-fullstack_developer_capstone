from django.contrib.auth.models import User
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .populate import initiate


logger = logging.getLogger(__name__)


@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    response_data = {"userName": username}
    if user is not None:
        login(request, user)
        response_data["status"] = "Authenticated"
    return JsonResponse(response_data)


def logout_user(request):
    data = {"userName": request.user.username}
    return JsonResponse(data)


@csrf_exempt
def registration(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    try:
        User.objects.get(username=username)
        username_exist = True
    except User.DoesNotExist:
        logger.debug("{} is new user".format(username))

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        login(request, user)
        response_data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(response_data)
    else:
        response_data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(response_data)


def get_cars(request):
    count = CarMake.objects.count()
    if count == 0:
        initiate()
    car_models = CarModel.objects.select_related('car_make')
    cars = [
        {"CarModel": car_model.name, "CarMake": car_model.car_make.name}
        for car_model in car_models
    ]
    return JsonResponse({"CarModels": cars})


def get_dealerships(request, state="All"):
    endpoint = "/fetchDealers/" if state != "All" else "/fetchDealers"
    endpoint += state
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchReviews/dealer/{}".format(dealer_id)
        reviews = get_request(endpoint)
        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            review_detail['sentiment'] = response['sentiment']
        return JsonResponse({"status": 200, "reviews": reviews})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = "/fetchDealer/{}".format(dealer_id)
        dealership = get_request(endpoint)
        return JsonResponse({"status": 200, "dealer": dealership})
    else:
        return JsonResponse({"status": 400, "message": "Bad Request"})


def add_review(request):
    if not request.user.is_anonymous:
        data = json.loads(request.body)
        try:
            post_review(data)
            return JsonResponse({"status": 200})
        except SomeSpecificException as e:
            return JsonResponse(
                {"status": 401,
                 "message": "Error in posting review"
                }
            )
    else:
        return JsonResponse({"status": 403, "message": "Unauthorized"+e})
