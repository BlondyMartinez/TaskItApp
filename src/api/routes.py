"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User, Task, StatusEnum, Address, Category, RoleEnum, Requester, TaskSeeker, Rating, Postulant
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from datetime import datetime

api = Blueprint('api', __name__)

# Allow CORS requests to this API
CORS(api)

# TASKS BELOW
@api.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify([task.serialize() for task in Task.query.all()]), 200


@api.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    title = data.get('title')
    description = data.get("description")
    delivery_location = data.get('delivery_location')
    delivery_lat = data.get('delivery_lat')
    delivery_lgt = data.get('delivery_lgt')
    pickup_location = data.get('pickup_location')
    pickup_lat = data.get('pickup_lat')
    pickup_lgt = data.get('pickup_lgt')
    due_date_str = data.get('due_date')
    requester_id = data.get('requester_id')
    category_id = data.get('category_id')
    budget = data.get('budget')

    if not all([title, description, due_date_str, requester_id, category_id, budget, delivery_location, delivery_lat, delivery_lgt, pickup_location, pickup_lat, pickup_lgt]):
            return jsonify({'error': 'Missing fields.'}), 400
    
    existing_requester = Requester.query.filter_by(user_id=requester_id).first()
    if not existing_requester: return jsonify({ 'error': 'Requester with given user ID not found.'}), 404

    existing_category = Category.query.get(category_id)
    if not existing_category: return jsonify({ 'error': 'Category not found.'}), 404
    
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid due date format"}), 400
    
    existing_delivery = Address.query.filter_by(address=delivery_location).first()
    if existing_delivery: delivery_address = existing_delivery
    else: 
        delivery_address = Address(address=delivery_location, latitude=delivery_lat, longitude=delivery_lgt)
        db.session.add(delivery_address)

    existing_pickup = Address.query.filter_by(address=pickup_location).first()
    if existing_pickup: pickup_address = existing_pickup
    else: 
        pickup_address = Address(address=pickup_location, latitude=pickup_lat, longitude=pickup_lgt)
        db.session.add(pickup_address)

    db.session.commit()
    
    new_task = Task(title=title, description=description, delivery_address=delivery_address, pickup_address=pickup_address, due_date=due_date, requester=existing_requester, category=existing_category, budget=budget)    
    
    db.session.add(new_task)
    db.session.commit()

    return jsonify({'message': 'Task posted successfully.'}), 201


@api.route('/tasks/<int:id>', methods=['GET'])
def get_task(id):
    task = Task.query.get(id)

    if not task: return jsonify({'error': 'Task not found.'}), 404

    return jsonify(task.serialize()), 200


@api.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get(id)

    if not task: return jsonify({'error': 'Task not found.'}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({'message': 'Task deleted successfully.'}), 200


@api.route('/tasks/<int:id>', methods=['PUT'])
def edit_task(id):  
    task = Task.query.get(id)
    if not task: return jsonify({'error': 'Task not found.'}), 404

    data = request.json
    new_title = data.get('title')
    new_description = data.get("description")
    new_delivery_location = data.get('delivery_location')
    new_pickup_location = data.get('pickup_location')
    new_due_date_str = data.get('due_date')
    new_status = data.get('status')
    new_category_id = data.get('category_id')
    new_seeker_id = data.get('seeker_id')
    new_budget = data.get('budget')

    if new_due_date_str:
        try:
            new_due_date = datetime.strptime(new_due_date_str, '%Y-%m-%d')
            task.due_date = new_due_date
        except ValueError:
            return jsonify({"error": "Invalid due date format."}), 400

    if new_status:
        try:
            new_status_enum = StatusEnum(new_status)
            task.status = new_status_enum
        except ValueError:
            return jsonify({"error": "Invalid status value."}), 400

    if new_category_id:
        existing_category = Category.query.get(new_category_id)
        if not existing_category:
            return jsonify({'error': 'Category not found.'}), 404
        task.category = existing_category

    if new_seeker_id:
        existing_seeker = TaskSeeker.query.get(new_seeker_id)
        if not existing_seeker:
            return jsonify({'error': 'Task seeker not found.'}), 404
        task.seeker = existing_seeker

    if new_title: task.title = new_title
    if new_description: task.description = new_description
    if new_delivery_location:
        delivery_address = Address(address=new_delivery_location, latitude=data.get('delivery_lat'), longitude=data.get('delivery_lgt'))
        db.session.add(delivery_address)
        db.session.commit()
        task.delivery_location_id = delivery_address.id
    if new_pickup_location:
        pickup_address = Address(address=new_pickup_location, latitude=data.get('pickup_lat'), longitude=data.get('pickup_lgt'))
        db.session.add(pickup_address)
        db.session.commit()
        task.pickup_location_id = pickup_address.id
    if new_budget: task.budget = new_budget

    db.session.commit()

    return jsonify({'message': 'Task edited successfully.'}), 200

# ADDRESSES
@api.route('/addresses', methods=['GET'])
def get_addresses():
    all_addresses = Address.query.all()
    results = list(map(lambda address: address.serialize(), all_addresses))

    return jsonify(results), 200

@api.route('/addresses/<int:address_id>', methods=['GET'])
def get_address(address_id):
    address = Address.query.filter_by(id=address_id).first()
    return jsonify(address.serialize()), 200


@api.route('/addresses', methods=['POST'])
def create_address():
    data = request.json
    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    user_id = data.get('user_id')    

    if not address or not latitude or not longitude or not user_id:
        return jsonify({"error": "Missing fields."}), 400
    
    existing_user = User.query.get(user_id)
    if not existing_user:  return jsonify({"error": "User not found."}), 404
    
    address = Address(address=address, longitude=longitude, latitude=latitude, user=existing_user)
    
    db.session.add(address)
    db.session.commit()

    return jsonify({"message": "Address saved."}), 200

@api.route('/addresses/<int:id>', methods=['DELETE'])
def delete_address(id):
    # Buscar la direccion por su ID en la base de datos
    address = Address.query.get(id)

    # Si no se encuentra la dirección, devuelve un error 404
    if address is None:
        return jsonify({"error": "address not found"}), 404

    # Eliminar dirección de la base de datos
    db.session.delete(address)
    db.session.commit()

    # Devolver una respuesta exitosa
    return jsonify({"message": "Address successfully deleted"}), 200

@api.route('/addresses/<int:id>', methods=['PUT'])
def update_address(id):
    address = Address.query.get(id)
    if address is None:
        return jsonify({"error": "Address not found"}), 404

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    if "address" in data and data["address"] == "":
        return jsonify({"message": "The address cannot be empty"}), 400

    # Update address fields
    for key in data:
        if hasattr(address, key):
            setattr(address, key, data[key])

    db.session.commit()
    return jsonify({"message": "Address successfully updated"}), 200

# CATEGORIES
@api.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Name is required.'}), 400
    
    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()
    
    return jsonify({'message': 'Category created successfully'}), 201

@api.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    category = Category.query.get(id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    return jsonify({'category': category.serialize()}), 200

@api.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify({'categories': [category.serialize() for category in categories]}), 200

@api.route('/categories/<int:id>', methods=['PUT'])
def update_category(id):
    category = Category.query.get(id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    data = request.get_json()
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    category.name = name
    db.session.commit()
    
    return jsonify({'message': 'Category updated successfully'}), 200

@api.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    category = Category.query.get(id)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'message': 'Category deleted successfully'}), 200

# USERS
@api.route('/users', methods=['GET'])
def get_users():
    return jsonify([user.serialize() for user in User.query.all()]), 200


@api.route('/users', methods=['POST'])
def add_user():
    data = request.json
    username = data.get('username')
    email = data.get("email")
    password = data.get('password')
    full_name = data.get('full_name')
    description = data.get('description')
    
    if not username or not email or not password or not full_name:
        return jsonify({ 'error': 'Missing fields.'}), 400
    
    existing_email = User.query.filter_by(email=email).first()
    if existing_email: return jsonify({ 'error': 'Email already used.'}), 400

    new_user = User(username=username, email=email, password=password, full_name=full_name, description=description)
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully.'}), 201


@api.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)

    if not user: return jsonify({'error': 'User not found.'}), 404

    return jsonify(user.serialize()), 200

@api.route('/users/<string:username>', methods=['GET'])
def get_user_by_username(username):
    user = User.query.filter_by(username=username).first()

    if not user: return jsonify({'error': 'User not found.'}), 404

    return jsonify(user.serialize()), 200


@api.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)

    if not user: return jsonify({'error': 'User not found.'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully.'}), 200


@api.route('/users/<int:id>', methods=['PUT'])
def edit_user(id):  
    user = User.query.get(id)

    if not user: return jsonify({'error': 'User not found.'}), 404

    data = request.json
    new_username = data.get('username')
    new_email = data.get("email")
    new_password = data.get('password')
    new_full_name = data.get('full_name')
    new_role_str = data.get('role')
    new_description = data.get('description')
        
    if new_role_str:
        try:
            new_role = RoleEnum(new_role_str)
            user.role = new_role
        except ValueError:
            return jsonify({"error": "Invalid role value."}), 400

    if new_username: user.username = new_username
    if new_email: user.email = new_email
    if new_password: user.password = new_password
    if new_full_name: user.full_name = new_full_name
    if new_description: user.new_description = new_description

    db.session.commit()

    return jsonify({'message': 'User edited successfully.'}), 200

# REQUESTERS
@api.route('/requesters', methods=['GET'])
def get_requesters():
    return jsonify([requester.serialize() for requester in Requester.query.all()]), 200

@api.route('/requesters/user_id/<int:id>', methods=['GET'])
def get_requester_by_username(id):
    requester = Requester.query.filter_by(user_id=id).first()

    if not requester: return jsonify({'error': 'Requester not found.'}), 404

    return jsonify(requester.serialize()), 200

@api.route('/requesters', methods=['POST'])
def add_requester():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({ 'error': 'Missing user id.'}), 400
    
    existing_user = User.query.get(user_id)
    if not existing_user: return jsonify({ 'error': 'User not found.'}), 404

    if existing_user.role == RoleEnum.REQUESTER or existing_user.role == RoleEnum.BOTH:
        return jsonify({'error': 'User already has requester role.'}), 400

    new_requester = Requester(user=existing_user)
    if existing_user.role == RoleEnum.NONE: existing_user.role = RoleEnum.REQUESTER
    else: existing_user.role = RoleEnum.BOTH

    db.session.add(new_requester)
    db.session.commit()

    return jsonify({'message': 'Requester role successfully added to user.'}), 201


@api.route('/requesters/<int:id>', methods=['GET'])
def get_requester(id):
    requester = Requester.query.get(id)

    if not requester: return jsonify({'error': 'Requester not found.'}), 404

    return jsonify(requester.serialize()), 200


@api.route('/requesters/<int:id>', methods=['DELETE'])
def delete_requester(id):
    requester = Requester.query.get(id)

    if not requester: return jsonify({'error': 'Requester not found.'}), 404
    
    user = User.query.get(requester.user_id)
    if user.role == RoleEnum.REQUESTER: user.role = RoleEnum.NONE
    else: user.role = RoleEnum.TASK_SEEKER

    db.session.delete(requester)
    db.session.commit()

    return jsonify({'message': 'Removed requester role successfully.'}), 200


@api.route('/requesters/<int:id>', methods=['PUT'])
def edit_requester(id):  
    requester = Requester.query.get(id)

    if not requester: return jsonify({'error': 'Requester not found.'}), 404

    data = request.json
    new_overall_rating = data.get("overall_rating")
    new_total_requested_tasks = data.get("total_requested_tasks")
    new_total_reviews = data.get("total_reviews")
    new_average_budget = data.get("average_budget")

    if new_overall_rating: requester.overall_rating = new_overall_rating
    if new_total_requested_tasks: requester.total_requested_tasks = new_total_requested_tasks
    if new_total_reviews: requester.total_reviews = new_total_reviews
    if new_average_budget: requester.average_budget = new_average_budget

    db.session.commit()

    return jsonify({'message': 'Requested info edited successfully.'}), 200

# TASK SEEKERS
@api.route('/task-seekers', methods=['GET'])
def get_seekers():
    return jsonify([seeker.serialize() for seeker in TaskSeeker.query.all()]), 200


@api.route('/task-seekers', methods=['POST'])
def add_seeker():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({ 'error': 'Missing user id.'}), 400
    
    existing_user = User.query.get(user_id)
    if not existing_user: return jsonify({ 'error': 'User not found.'}), 404

    if existing_user.role == RoleEnum.TASK_SEEKER or existing_user.role == RoleEnum.BOTH:
        return jsonify({'error': 'User already has requester role.'}), 400

    new_seeker = TaskSeeker(user=existing_user)
    if existing_user.role == RoleEnum.NONE: existing_user.role = RoleEnum.TASK_SEEKER
    else: existing_user.role = RoleEnum.BOTH

    db.session.add(new_seeker)
    db.session.commit()

    return jsonify({'message': 'Task seeker role successfully added to user.'}), 201


@api.route('/task-seekers/<int:id>', methods=['GET'])
def get_seeker(id):
    seeker = TaskSeeker.query.get(id)

    if not seeker: return jsonify({'error': 'Seeker not found.'}), 404

    return jsonify(seeker.serialize()), 200

@api.route('/task-seekers/user_id/<int:id>', methods=['GET'])
def get_seeker_by_username(id):
    seeker = TaskSeeker.query.filter_by(user_id=id).first()

    if not seeker: return jsonify({'error': 'Seeker not found.'}), 404

    return jsonify(seeker.serialize()), 200

@api.route('/task-seekers/<int:id>', methods=['DELETE'])
def delete_seeker(id):
    seeker = TaskSeeker.query.get(id)

    if not seeker: return jsonify({'error': 'Seeker not found.'}), 404
    
    user = User.query.get(seeker.user_id)
    if user.role == RoleEnum.TASK_SEEKER: user.role = RoleEnum.NONE
    else: user.role = RoleEnum.REQUESTER

    db.session.delete(seeker)
    db.session.commit()

    return jsonify({'message': 'Removed seeker role successfully.'}), 200


@api.route('/task-seekers/<int:id>', methods=['PUT'])
def edit_seeker(id):  
    seeker = TaskSeeker.query.get(id)

    if not seeker: return jsonify({'error': 'Seeker not found.'}), 404

    data = request.json
    new_overall_rating = data.get("overall_rating")
    new_total_requested_tasks = data.get("total_requested_tasks")
    new_total_reviews = data.get("total_reviews")

    if new_overall_rating: seeker.overall_rating = new_overall_rating
    if new_total_requested_tasks: seeker.total_requested_tasks = new_total_requested_tasks
    if new_total_reviews: seeker.total_reviews = new_total_reviews

    db.session.commit()

    return jsonify({'message': 'Seeker info edited successfully.'}), 200

# ratings

@api.route('/ratings', methods=['POST'])
def add_rating():
    data = request.json
    stars = data.get('stars')
    seeker_id = data.get('seeker_id')
    requester_id = data.get('requester_id')
    task_id = data.get('task_id')

    if not all([stars, task_id]) or (not seeker_id and not requester_id) or (seeker_id and requester_id):
        return jsonify({'error': 'Invalid fields'}), 400

    if stars < 1 or stars > 5:
        return jsonify({'error': 'Stars must be between 1 and 5'}), 400

    if seeker_id:
        seeker = User.query.get(seeker_id)
        if not seeker:
            return jsonify({'error': 'Seeker ID does not exist'}), 400

    if requester_id:
        requester = User.query.get(requester_id)
        if not requester:
            return jsonify({'error': 'Requester ID does not exist'}), 400

    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task ID does not exist'}), 400

    new_rating = Rating(stars=stars, seeker_id=seeker_id, requester_id=requester_id, task_id=task_id)
    db.session.add(new_rating)
    db.session.commit()
    return jsonify(new_rating.serialize()), 201

@api.route('/ratings', methods=['GET'])
def get_ratings():
    ratings = Rating.query.all()
    return jsonify([rating.serialize() for rating in ratings]), 200

@api.route('/ratings/<int:rating_id>', methods=['GET'])
def get_rating(rating_id):
    rating = Rating.query.get(rating_id)
    if rating is None:
        return jsonify({'error': 'Rating not found'}), 404
    return jsonify(rating.serialize()), 200

@api.route('/ratings/<int:rating_id>', methods=['PUT'])
def update_rating(rating_id):
    rating = Rating.query.get(rating_id)
    if not rating:
        return jsonify({'error': 'Rating not found'}), 404

    data = request.json
    stars = data.get('stars')

    if stars:
        rating.stars = stars
    
    db.session.commit()
    return jsonify({'message': 'Rating updated successfully'}), 200

@api.route('/ratings/<int:rating_id>', methods=['DELETE'])
def delete_rating(rating_id):
    rating = Rating.query.get(rating_id)
    if not rating:
        return jsonify({'error': 'Rating not found'}), 404

    db.session.delete(rating)
    db.session.commit()
    return jsonify({'message': 'Rating deleted successfully'}), 200


# POSTULANT

@api.route('/postulants', methods=['GET'])
def get_postulants():
    all_postulants = Postulant.query.all()
    print(all_postulants)
    results = list(map(lambda postulant: postulant.serialize(), all_postulants))
    print(results)


    return jsonify(results), 200


@api.route('/postulants/<int:postulant_id>', methods=['GET'])
def get_postulant(postulant_id):
    postulant = Postulant.query.filter_by(id=postulant_id).first()
    if not postulant:
        return jsonify({'error': 'Postulant not found'}), 404
    return jsonify(postulant.serialize()), 200


@api.route('/postulants', methods=['POST'])
def create_postulant():
    data = request.json
    status = data.get('status')
    seeker_id = data.get('seeker_id')
    price=data.get('price')
    task_id = data.get('task_id')

    if not status or not seeker_id or not price: 
        return jsonify({ 'error': 'Missing fields.'}), 400
    
    existing_seeker = TaskSeeker.query.filter_by(user_id=seeker_id).first()
    if not existing_seeker: return jsonify({ 'error': 'Task seeker with given user ID not found.'}), 404

    existing_task = Task.query.get(task_id)
    if not existing_task: return jsonify({ 'error': 'Task ID not found.'}), 404
    
    postul = Postulant(status=status, seeker=existing_seeker, price=price, task=existing_task)
    db.session.add(postul)
    db.session.commit()

    response_body = {
        "message": "Postulant created"
    }

    return jsonify(response_body), 200

@api.route('/postulants/<int:id>', methods=['PUT'])
def update_postulant(id):
    postulant = Postulant.query.get(id)
    if postulant is None:
        return jsonify({"error": "Postulant not found"}), 404

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    for key in data:
        if hasattr(postulant, key):
            setattr(postulant, key, data[key])

    db.session.commit()
    return jsonify({"message": "Postulant successfully updated"}), 200

@api.route('/postulants/<int:id>', methods=['DELETE'])
def delete_postulant(id):
    postulant = Postulant.query.get(id)

    if not postulant:
        return jsonify({'error': 'Postulant not found.'}), 404

    db.session.delete(postulant)
    db.session.commit()

    return jsonify({'message': 'Postulant deleted successfully.'}), 200