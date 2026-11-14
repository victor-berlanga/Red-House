'use strict';

// Browser observations only. No WebSocket replacement, route interception of WSS,
// fabricated product events, control endpoints, or global TLS bypass.
const fs = require('node:fs');
const path = require('node:path');
const readline = require('node:readline');
const assert = require('node:assert/strict');
const {chromium} = require(path.resolve(__dirname, '../.local/gcp-public/browser/node_modules/playwright'));

const pending = [];
const waiting = [];
const reader = readline.createInterface({input: process.stdin});
reader.on('line', line => {
  try {
    const value = JSON.parse(line);
    if (waiting.length) waiting.shift()(value);
    else pending.push(value);
  } catch {
    process.exitCode = 1;
    reader.close();
  }
});
const next = () => pending.length ? Promise.resolve(pending.shift()) : new Promise(resolve => waiting.push(resolve));
async function exchange(action) {
  process.stdout.write(JSON.stringify({action}) + '\n');
  const value = await next();
  assert.equal(value.action, action, 'Unexpected orchestration phase');
  return value;
}

(async () => {
  const input = await next();
  assert.equal(input.action, 'configure');
  input.scenario ||= 'replica_recovery';
  assert.ok(['replica_recovery', 'cursor_resync', 'logout_disconnected', 'logout_live', 'session_expiry'].includes(input.scenario));
  assert.match(input.spki, /^[A-Za-z0-9+/]{43}=$/);
  const output = input.output;
  const result = {
    passed: false, scenario: input.scenario, checks: [], states: [], sockets: [], pageErrors: [], authResponses: [],
    tls: 'Chrome SPKI exception restricted to the ephemeral test certificate; no OS CA acceptance',
    cartography: 'OSM tiles blocked to avoid bulk consumption; cartography is not accepted by this case',
  };
  const contexts = [];
  const pages = [];
  let stage = 'launch';
  const expectedSocket = input.base.replace('https:', 'wss:') + '/services/transporte/ws/v1/tracking/json';
  const subscriptions = new WeakMap(), upgrades = [], authReads = [];
  const nativeSockets = [], nativeSocketWatchers = new Set();
  const mapUrl = input.base + '/traslados/' + input.shipment + '/mapa';
  let terminating = false;
  process.once('SIGTERM', async () => {
    if (terminating) return;
    terminating = true;
    result.passed = false;
    result.failure = {stage, type: 'ParentTermination', category: 'orchestration'};
    await Promise.allSettled(contexts.map(value => value.close()));
    fs.writeFileSync(path.join(output, 'browser.json'), JSON.stringify(result, null, 2) + '\n');
    process.exit(143);
  });

  async function context(name) {
    const value = await chromium.launchPersistentContext(path.join(input.profiles, name), {
      channel: 'chrome', headless: true, viewport: {width: 1440, height: 1000},
      args: ['--ignore-certificate-errors-spki-list=' + input.spki],
    });
    contexts.push(value);
    // Only third-party image tiles are blocked. Product HTTP/WSS is unmodified.
    await value.route('https://tile.openstreetmap.org/**', route => route.abort());
    return value;
  }

  async function login(value, account) {
    const page = await value.newPage();
    pages.push(page);
    page.on('pageerror', error => result.pageErrors.push({name: error.name, stage}));
    assert.equal((await page.goto(input.base + '/login')).status(), 200);
    await page.locator('#login_email').fill(account);
    await page.locator('#password').fill(input.password);
    await Promise.all([
      page.waitForURL('**/panel'), page.locator('button[type="submit"]').click(),
    ]);
    return page;
  }

  async function state(page, name) {
    const value = await page.evaluate(() => ({
      status: document.querySelector('#tracking-status').textContent,
      lastEventId: document.querySelector('#tracking').dataset.lastEventId || '',
      rows: Array.from(document.querySelectorAll('#tracking-history tr'), row => row.dataset.eventId),
      rendered: window.gatewayRendered.slice(),
      pageInstance: performance.timeOrigin,
      recovery: document.querySelector('#tracking-recovery').textContent,
      coordinate: document.querySelector('#tracking-coordinate').textContent,
    }));
    result.states.push({phase: name, ...value});
    assert.equal(value.rows.length, new Set(value.rows).size, 'Duplicate event rows');
    await page.screenshot({path: path.join(output, name + '.png'), fullPage: true});
    return value;
  }

  async function rendered(page, eventId) {
    await page.waitForFunction(id =>
      window.gatewayRendered.some(event => event.event_id === id) &&
      Array.from(document.querySelectorAll('#tracking-history tr')).filter(row => row.dataset.eventId === id).length === 1,
    eventId, {timeout: 45000});
  }

  async function observe(page, profile) {
    await page.addInitScript(() => {
      window.gatewayRendered = [];
      document.addEventListener('redhouse:position-rendered', event => {
        window.gatewayRendered.push({event_id: event.detail.event_id, cursor: event.detail.cursor,
          received_at: event.detail.received_at, rendered_at: event.detail.rendered_at,
          receive_to_map_ms: event.detail.receive_to_map_ms});
      }, true);
    });
    page.on('websocket', socket => {
      // Install synchronously at creation, before awaiting any browser action.
      // Preserve the result so a fast subscribed frame cannot race its consumer.
      subscriptions.set(socket, socket.waitForEvent('framereceived', {
        predicate: frame => { try { return JSON.parse(String(frame.payload)).type === 'subscribed'; } catch { return false; } },
        timeout: 45000,
      }).then(() => true, () => false));
      const observed = {profile, url: socket.url().split('?')[0], events: [], closed: false};
      result.sockets.push(observed);
      nativeSockets.push({socket, observed});
      socket.on('framereceived', frame => {
        try {
          const value = JSON.parse(String(frame.payload));
          observed.events.push({type: value.type, event_id: value.position?.event_id,
            cursor: value.cursor, code: value.code});
        } catch { observed.events.push({type: 'non-json'}); }
        for (const notify of nativeSocketWatchers) notify();
      });
      socket.on('close', () => {
        observed.closed = true;
        for (const notify of nativeSocketWatchers) notify();
      });
    });
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Network.enable');
    cdp.on('Network.webSocketHandshakeResponseReceived', event => {
      upgrades.push({status: event.response.status});
    });
    page.on('response', response => {
      const target = new URL(response.url());
      const route = target.pathname.endsWith('/mapa/acceso') ? '/traslados/:id/mapa/acceso' : target.pathname;
      if (!['/sesion/estado', '/sesion/continuar', '/logout', '/traslados/:id/mapa/acceso'].includes(route)) return;
      const value = {profile, route, method: response.request().method(), status: response.status(), observed_at: Date.now()};
      result.authResponses.push(value);
      if (response.status() === 200 && ['/sesion/estado', '/sesion/continuar'].includes(route)) {
        authReads.push(response.json().then(data => {
          if (Number.isFinite(data.expires_at)) value.expires_at = data.expires_at;
          if (Number.isFinite(data.server_time)) value.server_time = data.server_time;
        }).catch(() => {}));
      }
    });
  }

  function waitForNewAuthorizedSocket(boundary, cursor) {
    return new Promise((resolve, reject) => {
      const check = () => {
        const found = nativeSockets.slice(boundary).find(entry =>
          entry.observed.profile === 'allowed' && !entry.observed.closed && !entry.socket.isClosed() &&
          entry.observed.events.some(event => event.type === 'authenticated') &&
          entry.observed.events.some(event => event.type === 'subscribed' && event.cursor === cursor));
        if (found) {
          clearTimeout(timer); nativeSocketWatchers.delete(check); resolve(found);
        }
      };
      const timer = setTimeout(() => {
        nativeSocketWatchers.delete(check);
        reject(new Error('No new live authorized subscribed socket after restoration'));
      }, 45000);
      nativeSocketWatchers.add(check);
      check();
    });
  }

  async function privacyEnded(page, name, timeout = 45000) {
    await page.waitForURL(target => target.origin === new URL(input.base).origin && target.pathname === '/login', {timeout});
    assert.equal(await page.locator('#tracking').count(), 0);
    assert.equal(await page.locator('#tracking-history tr').count(), 0);
    assert.equal(await page.locator('#tracking-map').count(), 0);
    await page.screenshot({path: path.join(output, name + '.png'), fullPage: true});
    result.checks.push(name + ': login visible; private tracking document removed');
  }

  async function realLogout(page) {
    stage = 'security-logout-form';
    const logoutTab = await page.context().newPage();
    pages.push(logoutTab);
    logoutTab.on('pageerror', error => result.pageErrors.push({name: error.name, stage}));
    await observe(logoutTab, 'logout-tab');
    assert.equal((await logoutTab.goto(input.base + '/panel')).status(), 200);
    const post = logoutTab.waitForResponse(response => {
      const target = new URL(response.url());
      return target.origin === new URL(input.base).origin && target.pathname === '/logout' && response.request().method() === 'POST';
    });
    await logoutTab.locator('form[action="/logout"]').first().locator('button').click();
    assert.equal((await post).status(), 302);
    await privacyEnded(page, 'security-private-data-cleared');
    await privacyEnded(logoutTab, 'security-logout-result');
  }

  function noLateFrames(eventIds) {
    const late = new Set(eventIds);
    assert.ok(result.sockets.filter(socket => socket.profile === 'transport')
      .every(socket => socket.events.every(event => !late.has(event.event_id))), 'Ended session received later positions');
  }

  async function securityScenario(transport, documentInstance) {
    stage = 'security-first-point';
    // Own synthetic cookies stay only in this process memory for an expired-cookie
    // replay probe. Never send them through protocol, errors or persisted results.
    const expiryCookies = input.scenario === 'session_expiry' ? await transport.context().cookies(input.base) : [];
    const first = await exchange('initial_publish');
    await rendered(transport, first.eventId);
    const before = await state(transport, 'security-01-live');
    assert.deepEqual(before.rows, [first.eventId]);
    if (input.scenario === 'cursor_resync') {
      stage = 'security-cursor-offline';
      result.networkFault = 'Playwright context.setOffline on observer profile only, plus real Transporte process cut; no WSS substitution';
      await transport.context().setOffline(true);
      await exchange('cursor_stop');
      await transport.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('Desconectado'));
      await state(transport, 'security-02-offline-retained');
      const gap = await exchange('cursor_gap');
      await transport.context().setOffline(false);
      await transport.waitForFunction(() => document.querySelector('#tracking-recovery').textContent.includes('cursor salió'), null, {timeout: 45000});
      await rendered(transport, gap.eventIds.at(-1));
      const recovered = await state(transport, 'security-03-resync-explicit-gap');
      assert.equal(recovered.pageInstance, documentInstance);
      assert.deepEqual(recovered.rows, [gap.eventIds.at(-1)]);
      assert.ok(result.sockets.some(socket => socket.events.some(event => event.type === 'resync.required')));
      result.omittedHistoryIds = gap.eventIds.slice(0, -1);
      stage = 'security-cursor-live-after-resync';
      const nextPoint = await exchange('cursor_continue');
      await rendered(transport, nextPoint.eventId);
      const continued = await state(transport, 'security-04-live-after-gap');
      assert.deepEqual(continued.rows, [gap.eventIds.at(-1), nextPoint.eventId]);
      assert.equal(continued.pageInstance, documentInstance);
      await exchange('restore_second');
      const both = await state(transport, 'security-05-both-restored');
      assert.deepEqual(both.rows, continued.rows);
      assert.equal(both.pageInstance, documentInstance);
      result.checks.push('Old real cursor rejected with resync.required; fresh authorized snapshot and explicit gap; no fabricated historical rows');
    } else if (input.scenario === 'logout_disconnected') {
      stage = 'security-authorized-comparison';
      const allowed = await login(await context('allowed'), 'transport1');
      await observe(allowed, 'allowed');
      assert.equal((await allowed.goto(mapUrl)).status(), 200);
      await rendered(allowed, first.eventId);
      const allowedBefore = await state(allowed, 'security-02-other-session-live');
      const socketBoundary = nativeSockets.length;
      result.recoverySocketBoundary = socketBoundary;
      await exchange('logout_stop');
      for (const page of [transport, allowed]) {
        await page.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('Desconectado'));
      }
      await state(transport, 'security-03-disconnected-before-logout');
      await realLogout(transport); // Portal network remains online throughout the WSS cut.
      await exchange('verify_logout');
      stage = 'security-authorized-recovery';
      await exchange('restore_authorized');
      const readySocket = await waitForNewAuthorizedSocket(socketBoundary, 1);
      const readyState = await state(allowed, 'security-04a-authorized-subscribed-before-publish');
      assert.equal(readyState.pageInstance, allowedBefore.pageInstance);
      assert.ok(!readySocket.observed.closed && !readySocket.socket.isClosed());
      result.authorizedRecovery = {
        socket_index: nativeSockets.indexOf(readySocket), boundary_before_cut: socketBoundary,
        authenticated: true, subscribed_cursor: 1, closed: false,
        original_page_instance: allowedBefore.pageInstance, recovered_page_instance: readyState.pageInstance,
        observed_at: Date.now(),
      };
      const recovery = await exchange('publish_for_authorized');
      await rendered(allowed, recovery.eventIds.at(-1));
      const allowedAfter = await state(allowed, 'security-04-other-session-recovered');
      assert.equal(allowedAfter.pageInstance, allowedBefore.pageInstance);
      assert.deepEqual(new Set(allowedAfter.rows), new Set(recovery.eventIds));
      noLateFrames(recovery.eventIds.slice(1));
      await privacyEnded(transport, 'security-05-revoked-stays-private');
      await exchange('restore_second');
      const both = await state(allowed, 'security-06-authorized-both-restored');
      assert.equal(both.pageInstance, allowedBefore.pageInstance);
      result.checks.push('Logout during total WSS outage revokes only its real browser session; independent authorized session recovers');
    } else if (input.scenario === 'logout_live') {
      await realLogout(transport);
      await exchange('verify_logout');
      const later = await exchange('publish_after_logout');
      noLateFrames(later.eventIds.slice(1));
      await privacyEnded(transport, 'security-02-live-logout-denied');
      await transport.goto(mapUrl);
      await privacyEnded(transport, 'security-03-protected-map-stays-denied');
      result.checks.push('Logout with live native WSS clears private document and denies protected map after real server revocation');
    } else {
      assert.equal(input.scenario, 'session_expiry');
      stage = 'security-natural-expiry';
      await exchange('await_expiry');
      // Laboratory inversion: 330 s access / 90 s fixed family. The unmodified
      // 300 s warning window naturally renews about every 30 s, not every second.
      await privacyEnded(transport, 'security-02-natural-session-expiry', 150000);
      await Promise.allSettled(authReads);
      const initialDeadline = result.authResponses.find(value => value.profile === 'transport' && value.route === '/sesion/estado' && value.status === 200 && Number.isFinite(value.expires_at));
      assert.ok(initialDeadline, 'Missing real initial expiry response');
      const renewal = result.authResponses.find(value => value.profile === 'transport' && value.route === '/sesion/continuar' && value.status === 200 && value.expires_at > initialDeadline.expires_at);
      assert.ok(renewal, 'No successful renewal with advanced access expiry was observed');
      const closeIndex = result.authResponses.findIndex(value => value.profile === 'transport' && value.status === 401);
      assert.ok(closeIndex >= 0, 'No actual 401 session closure was observed');
      const closing = result.authResponses[closeIndex];
      const beforeClosing = result.authResponses.slice(0, closeIndex).filter(value => value.profile === 'transport');
      const unexpected = beforeClosing.filter(value => value.status !== 200 &&
        !(value.status === 302 && value.route === '/traslados/:id/mapa/acceso'));
      assert.deepEqual(unexpected, [], 'Unexpected auth HTTP status before natural closure');
      assert.ok(beforeClosing.every(value => ![429, 503].includes(value.status)));
      assert.ok(initialDeadline.expires_at > closing.observed_at / 1000, 'Access deadline elapsed before the tested family closure');
      result.expiry = {initial_access_expires_at: initialDeadline.expires_at,
        renewed_access_expires_at: renewal.expires_at, renewal_server_time: renewal.server_time,
        first_401_observed_at: closing.observed_at,
        scope: 'Natural Redis/refresh-family expiry while announced access expiry is still in the future; not access-JWT expiry',
        unexpected_preclosure_auth_statuses: unexpected};
      const later = await exchange('verify_expiry');
      const familyExpiry = Date.parse(later.familyExpiresAt);
      assert.ok(Number.isFinite(familyExpiry));
      result.expiry.temporal_boundary = {
        sql_family_expires_at: later.familyExpiresAt,
        sql_family_expires_at_parsed_ms: familyExpiry,
        first_401_observed_at_ms: closing.observed_at,
        first_401_minus_sql_expiry_ms: closing.observed_at - familyExpiry,
        precision: 'SQL ISO keeps microseconds; Date.parse and Date.now compare milliseconds; Identity refresh expiry arithmetic uses integer seconds',
        limit: 'Strict observed401 >= parsed SQL expiry, without tolerance; a subsecond boundary discrepancy must be diagnosed separately, not hidden',
      };
      assert.ok(closing.observed_at >= familyExpiry, '401 closure preceded SQL family expiry');
      assert.ok(beforeClosing.filter(value => value.status === 302).every(value => value.observed_at >= familyExpiry));
      noLateFrames(later.eventIds.slice(1));
      // Python has already proved SQL/Redis family death and persisted both later
      // device points before restoring fixture configuration through a real login.
      await exchange('restore_fixture_identity');
      stage = 'security-expired-cookie-replay';
      const socketsBeforeReplay = result.sockets.length;
      const framesBeforeReplay = result.sockets.map(socket => socket.events.length);
      await transport.context().addCookies(expiryCookies);
      expiryCookies.length = 0;
      const protectedTarget = new URL(mapUrl);
      const initialResponse = transport.waitForResponse(response => {
        const target = new URL(response.url());
        return target.origin === protectedTarget.origin && target.pathname === protectedTarget.pathname &&
          response.request().method() === 'GET' && response.request().isNavigationRequest() &&
          response.request().frame() === transport.mainFrame();
      });
      const [initialProtected, replay] = await Promise.all([initialResponse, transport.goto(mapUrl)]);
      result.expiry.expired_cookie_replay_initial_status = initialProtected.status();
      // identify() returns Flask's actual default302 to public.login on failed auth.
      // A private200 followed by client-side redirect must fail this assertion.
      assert.equal(initialProtected.status(), 302, 'Protected map did not deny the initial expired-cookie GET');
      const location = await initialProtected.headerValue('location');
      assert.equal(typeof location, 'string');
      const deniedTarget = new URL(location, mapUrl);
      assert.equal(deniedTarget.origin, new URL(input.base).origin);
      assert.equal(deniedTarget.pathname, '/login');
      await privacyEnded(transport, 'security-03-expired-protected-map-denied');
      noLateFrames(later.eventIds.slice(1));
      assert.equal(result.sockets.length, socketsBeforeReplay, 'Expired-cookie replay opened a new tracking WebSocket');
      assert.ok(result.sockets.every((socket, index) => socket.events.length === framesBeforeReplay[index]), 'Tracking frames arrived after expired-cookie replay');
      result.expiry.expired_cookie_replay_result_status = replay.status();
      result.expiry.expired_cookie_replay_redirect_path = deniedTarget.pathname;
      result.expiry.expired_cookie_replay_private_data_absent = true;
      result.expiry.expired_cookie_replay_new_tracking_sockets = result.sockets.length - socketsBeforeReplay;
      result.expiry.expired_cookie_replay_new_tracking_frames = 0;
      result.expiry.expired_cookie_replay_denied_after_fixture_login = true;
      result.checks.push('Real renewal before fixed family expiry, without access expiry; later device ACKs persisted before fixture login; expired cookie replay remains denied');
    }
    assert.ok(result.sockets.every(socket => socket.url === expectedSocket));
    assert.ok(upgrades.some(value => value.status === 101));
    assert.deepEqual(result.pageErrors, []);
    const timings = new Map();
    for (const snapshot of result.states) {
      for (const event of snapshot.rendered) {
        assert.ok(Number.isFinite(event.receive_to_map_ms));
        assert.ok(Number.isFinite(Date.parse(event.received_at)));
        timings.set(event.event_id + ':' + event.rendered_at, event);
      }
    }
    assert.ok(timings.size >= 1);
    result.backendReceiveToMap = {
      observations: [...timings.values()],
      limit: 'Server receive to actual render; replay includes intentional offline/outage delay; no physical capture latency or SLA claim',
    };
    await Promise.allSettled(authReads);
    result.upgrades = upgrades;
    result.passed = true;
    process.stdout.write(JSON.stringify({action: 'complete'}) + '\n');
  }

  try {
    stage = 'transport-login';
    const transport = await login(await context('transport'), 'transport1');
    await observe(transport, 'transport');
    stage = 'map-open';
    assert.equal((await transport.goto(input.base + '/traslados/' + input.shipment + '/mapa')).status(), 200);
    await transport.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('Sin señal'), null, {timeout: 30000});
    assert.ok(result.sockets.length >= 1);
    assert.ok(result.sockets.every(socket => socket.url === expectedSocket));
    const initial = await state(transport, '01-map-open');
    const documentInstance = initial.pageInstance;

    if (input.scenario !== 'replica_recovery') {
      await securityScenario(transport, documentInstance);
      return;
    }

    stage = 'initial-point';
    const first = await exchange('initial_publish');
    await rendered(transport, first.eventId);
    await transport.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('En vivo'));
    const healthy = await state(transport, '02-live-two-replicas');
    assert.deepEqual(healthy.rows, [first.eventId]);

    stage = 'single-replica';
    await exchange('stop_one');
    await state(transport, '03-one-replica-stopped');
    // User action exercises a fresh native connection through the surviving upstream.
    const connectionsBefore = result.sockets.length;
    const newSocket = transport.waitForEvent('websocket', {timeout: 45000});
    await transport.locator('#tracking-retry').click();
    const replacement = await newSocket;
    assert.equal(await subscriptions.get(replacement), true, 'Replacement WSS did not subscribe');
    await transport.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('En vivo'), null, {timeout: 45000});
    assert.ok(result.sockets.length > connectionsBefore, 'No fresh native WSS after stopping A');
    const second = await exchange('single_publish');
    await rendered(transport, second.eventId);
    const single = await state(transport, '04-live-one-replica');
    assert.deepEqual(new Set(single.rows), new Set([first.eventId, second.eventId]));

    stage = 'all-replicas-down';
    await exchange('stop_all');
    await transport.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('Desconectado'), null, {timeout: 30000});
    const disconnected = await state(transport, '05-all-replicas-stopped');
    assert.deepEqual(disconnected.rows, single.rows, 'Outage lost existing point rows');
    assert.equal(disconnected.lastEventId, second.eventId);
    assert.equal(disconnected.pageInstance, documentInstance);

    stage = 'autonomous-appointment-login';
    const donor = await login(await context('donor'), 'donor1');
    stage = 'autonomous-appointment-goto';
    const cancellationUrl = input.base + '/citas/' + input.appointment + '/cancelar';
    result.mutation = {form_status: (await donor.goto(cancellationUrl)).status()};
    assert.equal(result.mutation.form_status, 200);
    stage = 'autonomous-appointment-submit';
    const cancellationTarget = new URL(cancellationUrl);
    const [mutationResponse] = await Promise.all([
      donor.waitForResponse(response => {
        const target = new URL(response.url());
        return target.origin === cancellationTarget.origin && target.pathname === cancellationTarget.pathname && response.request().method() === 'POST';
      }).then(response => {
        result.mutation.post_status = response.status();
        return response;
      }),
      donor.waitForURL(target => target.origin === cancellationTarget.origin && target.pathname === '/citas'),
      donor.getByRole('button', {name: 'Cancelar inscripción', exact: true}).click(),
    ]);
    assert.equal(mutationResponse.status(), 302);
    stage = 'autonomous-appointment-result';
    result.mutation.detail_status = (await donor.goto(input.base + '/citas/' + input.appointment)).status();
    assert.equal(result.mutation.detail_status, 200);
    assert.ok((await donor.locator('main').innerText()).includes('Cancelado'), 'Cancellation not visible in portal');
    await donor.screenshot({path: path.join(output, '06-appointment-cancelled-without-apis.png'), fullPage: true});
    await exchange('verify_mutation');
    const duringMutation = await state(transport, '07-map-preserved-during-mutation');
    assert.ok(duringMutation.status.includes('Desconectado'));
    assert.deepEqual(duringMutation.rows, single.rows);

    stage = 'automatic-recovery';
    const recovery = await exchange('restore');
    // No retry button or navigation: the original document reconnects automatically.
    await rendered(transport, recovery.eventIds[2]);
    await transport.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('En vivo'), null, {timeout: 45000});
    const restored = await state(transport, '08-recovered-same-map');
    assert.equal(restored.pageInstance, documentInstance);
    assert.deepEqual(new Set(restored.rows), new Set(recovery.eventIds));
    assert.equal(restored.lastEventId, recovery.eventIds[2]);
    assert.ok(restored.rendered.some(event => event.event_id === recovery.eventIds[2] && event.cursor === 3));
    stage = 'both-replicas-restored';
    await exchange('restore_second');
    const both = await state(transport, '09-both-replicas-restored-same-map');
    assert.equal(both.pageInstance, documentInstance);
    assert.deepEqual(both.rows, restored.rows);
    assert.equal(both.lastEventId, recovery.eventIds[2]);
    assert.ok(both.status.includes('En vivo'));
    assert.ok(result.sockets.every(socket => socket.url === expectedSocket), 'WSS left the real same-origin Nginx path');
    assert.ok(result.sockets.length >= 3);
    assert.ok(upgrades.filter(value => value.status === 101).length >= 3, 'Missing genuine WSS upgrades');
    result.upgrades = upgrades;
    assert.deepEqual(result.pageErrors, []);
    result.checks.push('Chrome native WSS same origin; real 101 handshakes',
      'One replica unavailable; new connection and persisted point through remaining replica',
      'Both replicas unavailable; disconnected map retains original IDs',
      'CSRF-protected appointment cancellation in autonomous monolith during total API outage',
      'Automatic recovery in same document; three unique event rows and observed rendered events',
      'Both upstream replicas restored; original open document preserves live state and point IDs');
    result.passed = true;
    process.stdout.write(JSON.stringify({action: 'complete'}) + '\n');
  } catch (error) {
    const category = error.name === 'AssertionError' ? 'assertion' :
      /strict mode|locator\(/i.test(error.message || '') ? 'locator' :
      error.name === 'TimeoutError' ? 'timeout' :
      /net::ERR_|navigation/i.test(error.message || '') ? 'navigation' : 'runtime';
    result.failure = {stage, type: error.name, category};
    // Do not serialize Playwright call logs, input values, credentials, or frame payloads.
    for (let i = 0; i < pages.length; i++) {
      try {
        if (!pages[i].url().endsWith('/login')) {
          await pages[i].screenshot({path: path.join(output, 'failure-page-' + i + '.png'), fullPage: true});
        }
      } catch { /* Preserve original failure. */ }
    }
    process.exitCode = 1;
    process.stdout.write(JSON.stringify({action: 'failed', stage, type: error.name}) + '\n');
  } finally {
    fs.writeFileSync(path.join(output, 'browser.json'), JSON.stringify(result, null, 2) + '\n');
    for (const value of contexts.reverse()) await value.close();
    reader.close();
  }
})().catch(() => { process.exitCode = 1; reader.close(); });
