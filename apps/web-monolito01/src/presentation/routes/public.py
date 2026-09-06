from flask import Blueprint, current_app, flash, g, make_response, redirect, render_template, request, session, url_for

from ...business.services import auth

bp = Blueprint("public", __name__)


@bp.get("/")
def index():
    return render_template("public.html", title="Una red que conecta vidas")


@bp.route("/login", methods=["GET", "POST"])
def login():
    error, status = None, 200
    if request.method == "POST":
        email = request.form.get("login_email", "").strip().lower()[:180]
        password = request.form.get("password", "")
        if len(password) > 128 or not email or not password:
            error, status = "Revisa tus credenciales e inténtalo de nuevo.", 401
        else:
            token, error, status = auth.login(email, password, request.remote_addr or "unknown")
            if token:
                session.clear()
                response = redirect(url_for("portal.dashboard"))
                response.set_cookie(current_app.config["JWT_COOKIE_NAME"], token,
                                    max_age=current_app.config["JWT_LIFETIME_SECONDS"], httponly=True,
                                    secure=current_app.config["PRODUCTION"], samesite="Lax", path="/")
                return response
    response = make_response(render_template("login.html", title="Acceso institucional", error=error), status)
    if status == 429:
        response.headers["Retry-After"] = "900"
    return response


@bp.post("/logout")
def logout():
    auth.logout(g.principal, g.session_id)
    session.clear()
    response = redirect(url_for("public.login"))
    response.delete_cookie(current_app.config["JWT_COOKIE_NAME"], path="/")
    return response


@bp.get("/recuperar-acceso")
def recovery():
    return render_template("recovery.html", title="Recuperar acceso")


@bp.get("/health/live")
def live():
    return {"status": "alive", "component": "red-house-monolith"}
