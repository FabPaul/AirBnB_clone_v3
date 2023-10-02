#!/usr/bin/python3
"""Cities API actions"""

from flask import Flask, jsonify
from flask import abort, request, make_response
from api.v1.views import app_views
from models import storage, storage_t
from models.place import Place
from models.user import User


@app_views.route("/cities/<city_id>/places", methods=["GET"],
                 strict_slashes=False)
def get_places_by_city(city_id):
    """retrieve a list of all cities"""
    city = storage.get("City", city_id)
    if not city:
        abort(404)
    return jsonify([place.to_dict() for place in city.places])


@app_views.route("/places/<place_id>", methods=['GET'], strict_slashes=False)
def get_place_by_id(place_id):
    """CIty objects based on city id, else 404"""
    place = storage.get("Place", place_id)
    if place:
        result = place.to_dict()
        return jsonify(result)
    else:
        abort(404)


@app_views.route("/places/<place_id>", methods=['DELETE'],
                 strict_slashes=False)
def delete_place(place_id):
    """ CIty objects based on city id, else 404"""
    place = storage.get("Place", place_id)
    if place:
        storage.delete(place)
        storage.save()
        return jsonify({}), 200
    else:
        abort(404)


@app_views.route("/cities/<city_id>/places", methods=['POST'],
                 strict_slashes=False)
def create_place(city_id):
    """CIty objects based on state id, else 404"""
    if not request.get_json():
        abort(400, 'Not a JSON')
    if 'user_id' not in request.get_json():
        abort(400, 'Missing user_id')
    if 'name' not in request.get_json():
        abort(400, 'Missing name')

    # create a dictionary from the JSON data
    new_place_data = request.get_json()
    all_cities = storage.all("City").values()
    city_obj = [obj.to_dict() for obj in all_cities
                if obj.id == city_id]
    if city_obj == []:
        abort(404)
    places = []

    # use the data to create a new place object
    new_place = Place(name=new_place_data['name'],
                      user_id=new_place_data['user_id'], city_id=city_id)
    all_users = storage.all("User").values()
    user_obj = [obj.to_dict() for obj in all_users
                if obj.id == new_place.user_id]
    if user_obj == []:
        abort(404)
    storage.new(new_place)
    storage.save()
    places.append(new_place.to_dict())
    return jsonify(places[0]), 201


@app_views.route("/places/<place_id>", methods=['PUT'], strict_slashes=False)
def update_place(place_id):
    """ CIty objects based on city id, else 404"""
    place = storage.get("Place", place_id)
    if not place:
        abort(404)

    update = request.get_json()
    if not update:
        abort(400, "Not a JSON")

    keys_to_exclude = ["id", "city_id", "user_id", "created_at", "updated_at"]
    for key in keys_to_exclude:
        update.pop(key, None)

    for key, value in update.items():
        setattr(place, key, value)

    storage.save()
    result = place.to_dict()
    return make_response(jsonify(result), 200)


@app_views.route('/places_search', methods=['POST'])
def places_search():
    """
    places route to handle http method for request to search places
    """
    req_json = request.get_json()

    # Check if the request body is not valid JSON
    if req_json is None:
        abort(400, 'Not a JSON')

    # Extract the lists of states, cities, and amenities from the JSON
    states = req_json.get('states', [])
    cities = req_json.get('cities', [])
    amenities = req_json.get('amenities', [])

    # Retrieve all Place objects
    all_places = [place for place in storage.all('Place').values()]

    # Define a function to filter places based on amenities
    def filter_by_amenities(place):
        if not amenities:
            return True
        place_amenities = set([amenity.id for amenity in place.amenities])
        return all(amenity_id in place_amenities for amenity_id in amenities)

    # Filter places based on states and cities
    filtered_places = []
    for place in all_places:
        if (place.city_id in cities) or (place.city.state_id in states):
            filtered_places.append(place)

    # Filter places based on amenities
    filtered_places = [place for place in filtered_places if filter_by_amenities(place)]

    # Return the filtered places as JSON response
    result = [place.to_json() for place in filtered_places]
    return jsonify(result)
