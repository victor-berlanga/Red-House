"""Rutas web: auth. Las reglas residen en las API propietarias."""

from zoneinfo import ZoneInfo
from ..forms import prepare_fields, attach_errors

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
    field,
    call,
)


@public.get("/")
def index():
    content, unavailable = {}, []
    for service, kind in (
        ("identidad_acceso", "institutions"),
        ("donantes", "campaigns"),
    ):
        try:
            content[kind] = call(service, "/api/v1/public/" + kind, token="")["items"]
        except BusinessError:
            content[kind] = []
            unavailable.append(kind)
    return render_template(
        "public.html",
        title="Una red que conecta vidas",
        publications=content,
        unavailable=unavailable,
    )


@public.route("/login", methods=["GET", "POST"])
def login():
    error, status, field_errors = None, 200, []
    fields = prepare_fields(
        [
            field("username", "Cuenta institucional"),
            field("password", "Contraseña", "password"),
        ],
        "identidad_acceso",
        "/api/v1/auth/login",
        "POST",
    )
    if request.method == "POST":
        try:
            sid = sessions.login(
                request.form.get("login_email", "").strip(),
                request.form.get("password", ""),
                request.form.get("otp", "").strip() or None,
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
            field_errors = attach_errors(fields, exc)
            for item in fields:
                if item["name"] == "username":
                    item["name"] = "login_email"
    return make_response(
        render_template(
            "login.html",
            title="Acceso institucional",
            error=error,
            field_errors=field_errors,
        ),
        status,
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


@public.route("/recuperar-acceso", methods=["GET", "POST"])
def recovery():
    error, message, status = None, None, 200
    if request.method == "POST":
        try:
            call(
                "identidad_acceso",
                "/api/v1/auth/recovery",
                "POST",
                data={"username": request.form.get("username", "").strip()},
                token="",
            )
            message = "Si la cuenta tiene correo verificado, recibirá un token de un uso. Revisa tu correo; vence en 15 minutos."
        except BusinessError as exc:
            error, status = exc.message, exc.status
    return render_template(
        "integration/recovery.html",
        title="Recuperar acceso",
        error=error,
        message=message,
        complete=False,
    ), status


@public.route("/recuperar-acceso/confirmar", methods=["GET", "POST"])
def recovery_complete():
    error, message, status = None, None, 200
    if request.method == "POST":
        try:
            if request.form.get("password") != request.form.get("confirmation"):
                raise BusinessError("Las contraseñas no coinciden.", 422)
            call(
                "identidad_acceso",
                "/api/v1/auth/recovery/complete",
                "POST",
                data={
                    "token": request.form.get("token", ""),
                    "password": request.form.get("password", ""),
                },
                token="",
            )
            message = "Contraseña actualizada. Las sesiones anteriores se han revocado. Inicia sesión con la contraseña nueva."
        except BusinessError as exc:
            error, status = exc.message, exc.status
    return render_template(
        "integration/recovery.html",
        title="Confirmar recuperación",
        error=error,
        message=message,
        complete=True,
    ), status


@public.get("/health/live")
def live():
    return {"status": "alive", "component": "red-house-web", "backend": current_app.config["BACKEND_MODE"]}


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
