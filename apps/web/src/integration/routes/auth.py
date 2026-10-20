"""Rutas web: auth. Las reglas residen en las API propietarias."""

from zoneinfo import ZoneInfo

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
    error = None
    try:
        sessions.logout(request.cookies.get(current_app.config["JWT_COOKIE_NAME"]))
    except BusinessError as exc:
        error = exc
    session.clear()
    response = (
        make_response(
            render_template(
                "login.html", title="Acceso institucional", error=error.message
            ),
            error.status,
        )
        if error
        else redirect(url_for("public.login"))
    )
    response.delete_cookie(current_app.config["JWT_COOKIE_NAME"])
    return response


@public.get("/recuperar-acceso")
def recovery():
    return redirect(url_for("public.login", help="access", _anchor="access-help"))


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
    if request.headers.get("X-Timezone-Update") == "1":
        origin = request.form.get("_timezone")
        values = request.form.getlist("date_values")
        if origin not in ZONES or len(values) > 100:
            raise BusinessError("Horario de origen o fechas inválidos.", 422)
        converted = []
        try:
            for value in values:
                if not value:
                    converted.append("")
                    continue
                captured = datetime.fromisoformat(value)
                if captured.tzinfo is not None:
                    raise ValueError()
                converted.append(
                    captured.replace(tzinfo=ZoneInfo(origin))
                    .astimezone(ZoneInfo(zone))
                    .strftime("%Y-%m-%dT%H:%M")
                )
        except (ValueError, OverflowError):
            raise BusinessError(
                "Revisa las fechas antes de cambiar el horario.", 422
            ) from None
        response = jsonify(timezone=zone, label=ZONES[zone], date_values=converted)
    else:
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
