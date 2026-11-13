def identify():
    if request.endpoint in ('regional.shipment_files', 'regional.document_new'):
        request.max_content_length = 11 * 1024 * 1024
    g.correlation_id, g.principal, g.access_token = (uuid4(), None, None)
    public = {'public.index', 'public.login', 'public.recovery', 'public.recovery_complete', 'public.live', 'public.logout', 'public.renew_session', 'static'}
    if not request.endpoint or request.endpoint in public:
        return
    sid = request.cookies.get(app.config['JWT_COOKIE_NAME'])
    try:
        user = sessions.authenticate(sid)
    except BusinessError as exc:
        if exc.status != 401:
            raise
        user = None
    if not user:
        if request.endpoint == 'public.session_status':
            return (jsonify(message='Tu sesión terminó. Inicia sesión nuevamente.'), 401)
        response = redirect(url_for('public.login'))
        response.delete_cookie(app.config['JWT_COOKIE_NAME'])
        return response
    cache = app.extensions.setdefault('institution_names', {})
    cached = cache.get(user['region_id'])
    if cached and cached['until'] > time.monotonic():
        g.institutions = cached['names']
    else:
        names, page = ({}, 1)
        try:
            while True:
                institutions = call('identidad_acceso', '/api/v1/institutions', params={'page_size': 100, 'page': page})
                names.update({row['id']: institution_label(row['name']) for row in institutions['items']})
                if page * 100 >= institutions['total'] or not institutions['items']:
                    break
                page += 1
            cache[user['region_id']] = {'until': time.monotonic() + 30, 'names': names}
            g.institutions = names
        except BusinessError as exc:
            if exc.status != 503:
                raise
            g.institutions = cached['names'] if cached else {}
    g.principal = RemotePrincipal(UUID(user['id']), user['username'], user['role'], ROLES[user['role']], UUID(user['tenant_id']), app.config.get('REGION_NAME', 'Nuevo León'), g.institutions.get(user['tenant_id'], 'Institución'))
