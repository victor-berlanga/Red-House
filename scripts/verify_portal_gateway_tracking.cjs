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
  assert.match(input.spki, /^[A-Za-z0-9+/]{43}=$/);
  const output = input.output;
  const result = {
    passed: false, checks: [], states: [], sockets: [], pageErrors: [],
    tls: 'Chrome SPKI exception restricted to the ephemeral test certificate; no OS CA acceptance',
    cartography: 'OSM tiles blocked to avoid bulk consumption; cartography is not accepted by this case',
  };
  const contexts = [];
  const pages = [];
  let stage = 'launch';
  const expectedSocket = input.base.replace('https:', 'wss:') + '/services/transporte/ws/v1/tracking/json';

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

  try {
    stage = 'transport-login';
    const transport = await login(await context('transport'), 'transport1');
    await transport.addInitScript(() => {
      window.gatewayRendered = [];
      document.addEventListener('redhouse:position-rendered', event => {
        window.gatewayRendered.push({event_id: event.detail.event_id, cursor: event.detail.cursor,
          rendered_at: event.detail.rendered_at});
      }, true);
    });
    const subscriptions = new WeakMap();
    transport.on('websocket', socket => {
      // Install synchronously at creation, before awaiting any browser action.
      // Preserve the result so a fast subscribed frame cannot race its consumer.
      subscriptions.set(socket, socket.waitForEvent('framereceived', {
        predicate: frame => { try { return JSON.parse(String(frame.payload)).type === 'subscribed'; } catch { return false; } },
        timeout: 45000,
      }).then(() => true, () => false));
      const observed = {url: socket.url().split('?')[0], events: [], closed: false};
      result.sockets.push(observed);
      socket.on('framereceived', frame => {
        try {
          const value = JSON.parse(String(frame.payload));
          observed.events.push({type: value.type, event_id: value.position?.event_id,
            cursor: value.cursor});
        } catch { observed.events.push({type: 'non-json'}); }
      });
      socket.on('close', () => { observed.closed = true; });
    });
    const cdp = await transport.context().newCDPSession(transport);
    const upgrades = [];
    await cdp.send('Network.enable');
    cdp.on('Network.webSocketHandshakeResponseReceived', event => {
      upgrades.push({status: event.response.status});
    });
    stage = 'map-open';
    assert.equal((await transport.goto(input.base + '/traslados/' + input.shipment + '/mapa')).status(), 200);
    await transport.waitForFunction(() => document.querySelector('#tracking-status').textContent.includes('Sin señal'), null, {timeout: 30000});
    assert.ok(result.sockets.length >= 1);
    assert.ok(result.sockets.every(socket => socket.url === expectedSocket));
    const initial = await state(transport, '01-map-open');
    const documentInstance = initial.pageInstance;

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
