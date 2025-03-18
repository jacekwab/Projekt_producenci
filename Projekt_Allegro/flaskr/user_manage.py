from flask import request, jsonify, render_template, flash, redirect, url_for,session
from werkzeug.security import check_password_hash, generate_password_hash
from db import db, User
import re
import random
import string


def is_valid_email(email):
    """Sprawdza poprawność adresu e-mail"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email)


def register_user():
    data = request.json
    login = data.get("login")
    email = data.get("email")
    password = data.get("password")

    if not login or not email or not password:
        return jsonify({"error": "Wszystkie pola są wymagane"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Nieprawidłowy adres e-mail"}), 400

    if User.query.filter_by(login=login).first() or User.query.filter_by(email=email).first():
        return jsonify({"error": "Użytkownik o podanym loginie lub e-mailu już istnieje"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(login=login, email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Rejestracja zakończona sukcesem"}), 201


def login_user():
    if request.method == 'GET':
        return render_template('login.html', active_menu='login')
    else:
        if request.method == "POST":
            login = request.form.get("login")
            password = request.form.get("password")

            user = User.query.filter_by(login=login).first()

            if user and check_password_hash(user.password_hash, password):
                if not user.is_active:
                    flash("Konto jest nieaktywne", "danger")
                    return redirect(url_for("login_user"))

                session["user_id"] = user.id
                session["user_login"] = user.login
                session["is_admin"] = user.is_admin

                flash("Zalogowano pomyślnie", "success")
                return redirect(url_for("search_form_display"))  # Przekierowanie na stronę główną użytkownika

            flash("Nieprawidłowy login lub hasło", "danger")
            return redirect(url_for("login_user"))

        return redirect(url_for("login_user"))


def change_password():
    data = request.json
    login = data.get("login")
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    user = User.query.filter_by(login=login).first()

    if not user or not check_password_hash(user.password_hash, old_password):
        return jsonify({"error": "Nieprawidłowe dane logowania"}), 403

    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"message": "Hasło zostało zmienione"}), 200


def admin_update_user():
    data = request.json
    login = data.get("login")
    new_email = data.get("email")
    is_admin = data.get("is_admin")
    is_active = data.get("is_active")

    user = User.query.filter_by(login=login).first()

    if not user:
        return jsonify({"error": "Użytkownik nie istnieje"}), 404

    if new_email:
        if not is_valid_email(new_email):
            return jsonify({"error": "Nieprawidłowy e-mail"}), 400
        user.email = new_email

    if is_admin is not None:
        user.is_admin = bool(is_admin)

    if is_active is not None:
        user.is_active = bool(is_active)

    db.session.commit()
    return jsonify({"message": "Dane użytkownika zostały zaktualizowane"}), 200


def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))


def reset_password():
    data = request.json
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Użytkownik o podanym e-mailu nie istnieje"}), 404

    new_password = generate_random_password()
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Nowe hasło zostało wygenerowane i wysłane na e-mail"}), 200
