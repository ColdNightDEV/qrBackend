from flask import Flask, request, jsonify, send_from_directory, session, redirect, render_template, sessions
from flask_bcrypt import Bcrypt
from flask_session import Session
from config import ApplicationConfig
from models import db, User, Referral
import qrcode
from flask_cors import CORS
from io import BytesIO
import requests
import string
import random
import base64
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)
server_session = Session(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'profile_images')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://enairafrontend.vercel.app'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(image, user_id):
    filename = secure_filename(image.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(save_path)

    # Read the saved image file
    with open(save_path, 'rb') as file:
        image_data = file.read()

    # Encode the image data as base64
    base64_image = base64.b64encode(image_data).decode('utf-8')

    # Update the user's profile_image field with the base64 encoded image
    user = User.query.filter_by(id=user_id).first()
    user.profile_image = base64_image
    db.session.commit()

    return filename

db.init_app(app)

with app.app_context():
    db.create_all()
    
@app.route("/")
def homepage():
    return render_template("homepage.html")

@app.route("/okay")
def okay():
    return render_template("okay.html")

@app.route("/update_profile_image", methods=["POST"])
def update_profile_image():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    profile_image = request.files.get("profile_image")

    # Process profile image upload
    if profile_image:
        profile_image_filename = save_profile_image(profile_image, user.id)
        user.profile_image = profile_image_filename
        db.session.commit()
    else:
        return jsonify({"error": "No profile image provided"}), 400

    # Read the image file and encode it as Base64
    try:
        with open(profile_image_filename, "rb") as file:
            encoded_image = base64.b64encode(file.read()).decode("utf-8")
    except Exception as e:
        return jsonify({"error": "Failed to read and encode profile image"}), 500

    # Remove the image file if needed
    # os.remove(profile_image_filename)

    response = {
        "id": user.id,
        "email": user.email,
        "qr_code": user.qr_code,
        "paid": user.paid,
        "payment_reference": user.payment_reference,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "state_of_origin": user.state_of_origin,
        "date_of_birth": user.date_of_birth,
        "local_government": user.local_government,
        "gender": user.gender,
        "next_of_kin": user.next_of_kin,
        "referral_code": user.referral_code,
        "referral_id": user.referral_id,
        "referral_link": user.referral_link,
        "profile_image": encoded_image if user.profile_image else None,
        "earnings": user.earnings,
    }

    return redirect("https://enairafrontend.vercel.app/dashboard")

@app.route("/profile_images/<filename>")
def serve_profile_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/@me')
def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    referred_users = User.query.join(Referral, Referral.referred_id == User.id).filter(Referral.referrer_id == user.id).all()

    referred_user_data = []
    for referred_user in referred_users:
        referred_user_data.append({
            "id": referred_user.id,
            "email": referred_user.email,
            "has_paid": referred_user.paid
        })

    response = {
        "id": user.id,
        "email": user.email,
        "qr_code": user.qr_code,
        "paid": user.paid,
        "payment_reference": user.payment_reference,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "state_of_origin": user.state_of_origin,
        "date_of_birth": user.date_of_birth,
        "local_government": user.local_government,
        "gender": user.gender,
        "earnings": user.earnings,
        "next_of_kin": user.next_of_kin,
        "referral_code": user.referral_code,
        "referral_id": user.referral_id,
        "referral_link": user.referral_link,
        "referred_users": referred_user_data,
        "profile_image": user.profile_image,
        "account_number": user.account_number,
        "bank_name": user.bank_name
    }

    response = jsonify(response)
    session["user_id"] = user.id

    return response, 201




def generate_referral_id():
    characters = string.ascii_letters + string.digits
    referral_id = ''.join(random.choices(characters, k=8))
    existing_user = User.query.filter_by(referral_id=referral_id).first()
    if existing_user:
        return generate_referral_id()  # Regenerate if the referral ID already exists
    return referral_id


@app.route("/register", methods=["POST"])
def register_user():
    email = request.json["email"]
    password = request.json["password"]
    first_name = request.json["first_name"]
    last_name = request.json["last_name"]
    phone_number = request.json["phone_number"]
    state_of_origin = request.json["state_of_origin"]
    date_of_birth = request.json["date_of_birth"]
    local_government = request.json["local_government"]
    gender = request.json["gender"]
    next_of_kin = request.json["next_of_kin"]
    account_number = request.json.get("account_number")
    bank_name = request.json.get("bank_name")
    referral_code = request.json.get("referral_code", None)  # Optional field, set to None if not provided
    earnings = request.json.get("earnings", 0.0)  # Optional field, set to 0.0 if not provided
    profile_image = request.files.get("profile_image")

    user_exists = User.query.filter_by(email=email).first() is not None

    if user_exists:
        return jsonify({"error": "A user with these credentials already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password)

    # Generate the qr code
    data = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
        "state_of_origin": state_of_origin,
        "date_of_birth": date_of_birth,
        "local_government": local_government,
        "gender": gender,
        "next_of_kin": next_of_kin,
        "account_number": account_number,
        "bank_name": bank_name,
        "referral_code": referral_code,
        "profile_image": profile_image
    }
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer)
    img_str = base64.b64encode(buffer.getvalue()).decode()

    referral_id = generate_referral_id()

    # Create the referral link
    referral_link = f"https://enairafrontend.vercel.app/invite/{referral_id}"

    new_user = User(
        email=email,
        password=hashed_password,
        qr_code=img_str,
        paid=False,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        state_of_origin=state_of_origin,
        date_of_birth=date_of_birth,
        local_government=local_government,
        gender=gender,
        next_of_kin=next_of_kin,
        referral_code=referral_code,
        referral_id=referral_id,
        referral_link=referral_link,
        account_number=account_number,
        bank_name=bank_name,
        earnings=earnings,
        profile_image=None  # Set to None initially, will be updated later if provided
    )

    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.id

    # Process profile image upload
    if profile_image:
        profile_image_filename = save_profile_image(profile_image, new_user.id)
        new_user.profile_image = profile_image_filename
        db.session.commit()

    response = {
        "id": new_user.id,
        "email": new_user.email,
        "qr_code": new_user.qr_code,
        "paid": new_user.paid,
        "payment_reference": new_user.payment_reference,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "phone_number": new_user.phone_number,
        "state_of_origin": new_user.state_of_origin,
        "date_of_birth": new_user.date_of_birth,
        "local_government": new_user.local_government,
        "gender": new_user.gender,
        "next_of_kin": new_user.next_of_kin,
        "referral_code": new_user.referral_code,
        "referral_id": referral_id,
        "referral_link": new_user.referral_link,
        "account_number": new_user.account_number,
        "bank_name": new_user.bank_name,
        "profile_image":  f"https://qrbackend.onrender.com/profile_images/{new_user.profile_image}" if new_user.profile_image else None,
        "earnings": new_user.earnings
    }
    

    return jsonify(response), 201



@app.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401

    session["user_id"] = user.id
    db.session.commit()
    

    response = {
        "id": user.id,
        "email": user.email,
        "qr_code": user.qr_code,
        "paid": user.paid,
        "payment_reference": user.payment_reference,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "state_of_origin": user.state_of_origin,
        "date_of_birth": user.date_of_birth,
        "local_government": user.local_government,
        "gender": user.gender,
        "next_of_kin": user.next_of_kin,
        "referral_code": user.referral_code,
        "referral_id": user.referral_id,
        "referral_link": user.referral_link
    }

    response = jsonify(response)
    response.set_cookie("session_id", str(user.id), domain=".onrender.com")

    return response, 201


@app.route("/pay/<user_id>", methods=["POST"])
def pay_for_qr_code(user_id):
    # Retrieve the user from the database
    user = User.query.filter_by(id=user_id).first()

    # Check if the user exists
    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        # Prepare the data payload
        payload = {
            "data": {
                "public_key": "MSFT_test_40M0277A5ADIAQPHIB6WIPYW7K00QUH",
                "request_type": "test",
                "merchant_tx_ref": "ref_123456789",
                "redirect_url": f"https://qrbackend.onrender.com/pay/{user_id}/verify",  # Update the redirect_url
                "name": user.first_name,
                "email_address": user.email,
                "phone_number": user.phone_number,
                "amount": "500",
                "currency": "NGN",
                "user_bear_charge": "no",
                "preferred_payment_option": "card",
                "description": "payment"
            }
        }

        # Make a payment request to Marasoft API to initiate payment
        response = requests.post(
            "https://checkout.marasoftpay.live/initiate_transaction",
            json=payload,
            headers={
                "Content-Type": "application/json",
            }
        )

        data = response.json()
        print("Marasoft API Response:", data)

        if response.status_code == 200 and data.get("status") == "success":
            payment_url = data["url"]  # Update this line to access the payment URL

            # Update the user's payment reference in the database
            user.payment_reference = payment_url
            db.session.commit()

            return jsonify({"payment_url": payment_url})
        else:
            error_message = data.get("error") if data.get("error") else "Payment initiation failed"
            print("Payment initiation failed:", error_message)
            return jsonify({"error": error_message}), 500

    except Exception as e:
        print("Payment initiation failed:", str(e))
        return jsonify({"error": "Payment initiation failed"}), 500


@app.route("/pay/<user_id>/verify", methods=["GET"])
def verify_payment(user_id):
    # Retrieve the query parameters from the callback URL
    status = request.args.get("status")
    transaction_reference = request.args.get("txn_ref")
    payment_reference = request.args.get("msft_ref")

    # Check if the required parameters are missing
    if not status or not transaction_reference or not payment_reference:
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        # Check if the payment was successful
        if status.lower() == "successful":
            # Retrieve the user from the database based on the user ID
            user = User.query.get(user_id)

            if not user:
                return jsonify({"error": "User not found"}), 404

            # Update the user's payment status if the payment is successful
            user.paid = True
            user.payment_reference = transaction_reference  # Set the payment reference as the transaction reference
            db.session.commit()

            # Check if the user was referred by another user
            referral = Referral.query.filter_by(referred_id=user.id).first()
            if referral:
                referrer = User.query.get(referral.referrer_id)
                if referrer:
                    # Update the referred user's payment status to indicate that the referrer's referred user has paid
                    referral.referred_user_paid = True
                    db.session.commit()

                    # Update the referrer's earnings
                    referrer.earnings += 100.0  # Add 100 to the referrer's earnings for every successful payment
                    db.session.commit()

            # Redirect to the desired URL
            return redirect("https://enairafrontend.vercel.app/dashboard")

        # Return a response indicating the payment was not successful
        response = {
            "paid": False,
            "user_id": user_id,
        }
        response = jsonify(response)
        response.set_cookie("session_id", str(user.id), domain=".onrender.com")

        return response, 201

    except Exception as e:
        print("Payment verification failed:", str(e))
        return jsonify({"error": "Payment verification failed"}), 500

    
    
@app.route("/register/<referral_id>", methods=["GET", "POST"])
def handle_referral_registration(referral_id):
    # Check if the referral ID exists
    referrer = User.query.filter_by(referral_id=referral_id).first()
    if not referrer:
        return jsonify({"error": "Invalid referral ID"}), 404

    if request.method == "GET":
        return jsonify({"referrer_id": referrer.id}), 200

    # Parse request data for new user registration
    email = request.json.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Check if the email already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already exists"}), 409

    password = request.json.get("password")
    first_name = request.json.get("first_name")
    last_name = request.json.get("last_name")
    phone_number = request.json.get("phone_number")
    state_of_origin = request.json.get("state_of_origin")
    date_of_birth = request.json.get("date_of_birth")
    local_government = request.json.get("local_government")
    gender = request.json.get("gender")
    next_of_kin = request.json.get("next_of_kin")
    account_number = request.json.get("account_number")
    bank_name = request.json.get("bank_name")
    earnings = request.json.get("earnings")

    # Generate the qr code
    
    
    new_referral_id = generate_referral_id()
    # Create the referral link
    new_referral_link = f"https://enairafrontend.vercel.app/invite/{new_referral_id}"
    
    data = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
        "state_of_origin": state_of_origin,
        "date_of_birth": date_of_birth,
        "local_government": local_government,
        "gender": gender,
        "next_of_kin": next_of_kin,
        "account_number": account_number,
        "bank_name": bank_name
    }
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer)
    img_str = base64.b64encode(buffer.getvalue()).decode()

    # Create the new user
    new_user = User(
        email=email,
        password=bcrypt.generate_password_hash(password),
        qr_code=img_str,
        paid=False,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        state_of_origin=state_of_origin,
        date_of_birth=date_of_birth,
        local_government=local_government,
        gender=gender,
        next_of_kin=next_of_kin,
        referral_code=None,
        referral_id=new_referral_id,
        referral_link=new_referral_link,
        account_number=account_number,
        bank_name=bank_name,
        earnings=earnings
    )

    # Add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    # Record referral if referrer exists
    referral = Referral(referrer_id=referrer.id, referred_id=new_user.id)
    db.session.add(referral)
    db.session.commit()

    # Update the referral information for the referrer
    referrer.referrals_made.append(referral)
    db.session.commit()

    response = {
        "id": new_user.id,
        "email": new_user.email,
        "qr_code": new_user.qr_code,
        "paid": new_user.paid,
        "first_name": new_user.first_name,
        "last_name": new_user.last_name,
        "phone_number": new_user.phone_number,
        "state_of_origin": new_user.state_of_origin,
        "date_of_birth": new_user.date_of_birth,
        "local_government": new_user.local_government,
        "gender": new_user.gender,
        "next_of_kin": new_user.next_of_kin,
        "referral_code": new_user.referral_code,
        "referral_id": new_user.referral_id,
        "referral_link": new_user.referral_link,
        "account_number": new_user.account_number,
        "bank_name": new_user.bank_name,
        "earnings": new_user.earnings
        }

    response.set_cookie("session_id", str(new_user.id), domain=".onrender.com")

    return jsonify(response), 201


@app.route("/logout", methods=["POST"])
def logout():
    # Check if the user is logged in
    if "user_id" in session:
        # Clear the session
        session.clear()
        return jsonify({"message": "Logged out successfully"}), 200
    else:
        return jsonify({"message": "No user is currently logged in"}), 200

# ...




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
