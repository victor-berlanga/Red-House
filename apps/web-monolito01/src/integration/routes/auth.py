"""Rutas web: auth. Las reglas residen en las API propietarias."""

from .common import (
    BusinessError,
    ZONES,
    current_app,
    datetime,
    g,
    generate_csrf,
    jsonify,
    make_response,
    portal,
    public,
    redirect,
    render_template,
    request,
    session,
    sessions,
    timezone,
    url_for,
    urlsplit,
)


@public.get("/")
def index():
    return render_template("public.html", title="Una red que conecta vidas")


@public.route("/login", methods=["GET", "POST"])
def login():
    error, status = None, 200
    if request.method == "POST":
        try:
            sid = sessions.login(
                request.form.get("login_email", "").strip(),
                request.form.get("password", ""),
            )
            session.clear()
            response = redirect(url_for("portal.dashboard"))
            response.set_cookie(
                current_app.config["JWT_COOKIE_NAME"],
                sid,
                max_age=86400,
                httponly=True,
                secure=current_app.config["PRODUCTION"],
                samesite="Lax",
                path="/",
            )
            return response
        except BusinessError as exc:
            error, status = exc.message, exc.status
    return make_response(
        render_template("login.html", title="Acceso institucional", error=error), status
    )


@public.post("/logout")
def logout():
    sessions.logout(request.cookies.get(current_app.config["JWT_COOKIE_NAME"]))
    session.clear()
    response = redirect(url_for("public.login"))
    response.delete_cookie(current_app.config["JWT_COOKIE_NAME"])
    return response


@public.get("/recuperar-acceso")
def recovery():
    return render_template("recovery.html", title="Recuperar acceso")


@public.get("/health/live")
def live():
    return {"status": "alive", "component": "red-house-web", "backend": "microservices"}


@public.get("/sesion/estado")
def session_status():
    return jsonify(
        expires_at=g.web_session["expires_at"],
        server_time=datetime.now(timezone.utc).timestamp(),
    )


@public.post("/sesion/continuar")
def renew_session():
    try:
        result = sessions.renew(
            request.cookies.get(current_app.config["JWT_COOKIE_NAME"])
        )
        result["csrf_token"] = generate_csrf()
        return jsonify(result)
    except BusinessError as exc:
        return jsonify(message=exc.message), exc.status


@portal.post("/preferencias/horario")
def timezone_preference():
    zone = request.form.get("timezone")
    if zone not in ZONES:
        raise BusinessError("Zona horaria inválida.", 422)
    target = request.form.get("next", "/panel")
    parsed = urlsplit(target)
    if (
        parsed.scheme
        or parsed.netloc
        or not target.startswith("/")
        or target.startswith("//")
        or "\\" in target
        or any(ord(c) < 32 for c in target)
    ):
        target = "/panel"
    response = redirect(target)
    response.set_cookie(
        "display_timezone",
        zone,
        max_age=31536000,
        httponly=True,
        samesite="Lax",
        secure=request.is_secure,
    )
    return response
