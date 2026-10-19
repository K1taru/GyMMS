// Run with: node --test --test-isolation=none tests/js/qr_payment.test.cjs
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {runInNewContext} = require('node:vm');
const {randomUUID} = require('node:crypto');
const test = require('node:test');

const source = readFileSync(resolve(__dirname, '../../core/static/core/js/qr_payment.js'), 'utf8');
const prefix = 'gymms:qrph:staff:';
const flush = () => new Promise(resolve => setImmediate(resolve));

function element() {
    const listeners = new Map();
    return {
        hidden: true, disabled: false, textContent: '', style: {}, dataset: {}, children: [],
        isConnected: true, inert: false, tagName: 'DIV',
        addEventListener(type, handler) {
            if (!listeners.has(type)) listeners.set(type, []);
            listeners.get(type).push(handler);
        },
        async emit(type, event = {}) {
            await Promise.all((listeners.get(type) || []).map(handler => handler(event)));
            await flush();
        },
        focus() { this.focused = true; },
        contains() { return false; },
        replaceChildren(...nodes) { this.children = nodes; },
        append(node) { this.children.push(node); },
    };
}

function checkout(changes = {}) {
    return {id: randomUUID(), status: 'ready', is_unresolved: true, review_required: false,
        customer_name: 'Test member', plan_label: 'Daily', currency: 'PHP', amount: '1.00',
        can_cancel: true, payment: null, test_mode: true, message: 'Ready', ...changes};
}

async function widget({current = checkout(), saved = null} = {}) {
    const ids = ['widget', 'overlay', 'dialog', 'floating', 'notice', 'minimize', 'cancel',
        'dismiss', 'title', 'summary', 'message', 'image-area', 'expiry'];
    const elements = Object.fromEntries(ids.map(id => [id, element()]));
    const root = elements.widget;
    root.dataset.userId = 'staff';
    const background = element();
    const document = Object.assign(element(), {
        hidden: false, body: Object.assign(element(), {children: [root, background]}),
        activeElement: element(), getElementById: id => id === 'gymqr-widget' ? root : elements[id.replace('gymqr-', '')],
        querySelector: () => ({value: 'csrf-fixture'}), createElement: () => element(),
    });
    const states = [], calls = [], intervals = new Map(), storage = new Map();
    if (saved) storage.set(prefix + 'attempt', saved.id);
    const server = {current, detail: saved, cancel: null, created: checkout()};
    const window = Object.assign(element(), {
        dispatchEvent(event) { states.push(event.detail); },
    });
    runInNewContext(source, {
        document, window, crypto: {randomUUID}, URL, Date,
        localStorage: {
            getItem: key => storage.get(key) ?? null,
            setItem: (key, value) => storage.set(key, String(value)),
            removeItem: key => storage.delete(key),
        },
        CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
        setInterval: (fn, ms) => intervals.set(ms, fn), setTimeout: () => 1, clearTimeout() {},
        fetch: async (url, options) => {
            calls.push({url, options});
            let attempt;
            if (url.endsWith('/cancel/')) {
                attempt = server.cancel;
                server.current = attempt.is_unresolved ? attempt : null;
                server.detail = attempt;
            } else if (url.endsWith('/current/')) attempt = server.current;
            else if (url === '/payments/qrph/attempts/') attempt = server.current = server.created;
            else attempt = server.detail;
            return {ok: true, json: async () => ({success: true, attempt})};
        },
    });
    await document.emit('DOMContentLoaded');
    return {elements, window, document, storage, server, calls, states, background,
        poll: async () => { await intervals.get(3000)(); await flush(); }};
}

test('confirmed cancellation clears modal, floating badge and storage, and permits a fresh checkout', async () => {
    const w = await widget();
    assert.equal(w.window.GymQRPayment.unresolved, true);
    w.server.cancel = {...w.server.current, status: 'cancelled', is_unresolved: false, can_cancel: false};
    await w.elements.cancel.emit('click');
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.elements.floating.hidden, true);
    assert.equal(w.background.inert, false);
    assert.equal(w.storage.has(prefix + 'attempt'), false);
    assert.equal(w.states.at(-1), null);
    assert.equal(w.elements.notice.textContent, 'Payment cancelled');
    await w.poll();
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.elements.floating.hidden, true);
    const data = new FormData();
    await w.window.GymQRPayment.start(data);
    assert.ok(data.get('request_key'));
    assert.equal(w.states.at(-1).id, w.server.created.id);
    assert.equal(w.elements.overlay.hidden, false);
});

test('unconfirmed cancellation stays unresolved until worker confirms cancellation', async () => {
    const w = await widget();
    w.server.cancel = {...w.server.current, status: 'cancel_requested', message: 'Waiting for PayMongo'};
    await w.elements.cancel.emit('click');
    assert.equal(w.window.GymQRPayment.unresolved, true);
    assert.equal(w.elements.overlay.hidden, false);
    assert.equal(w.elements.title.textContent, 'Cancelling payment');
    assert.equal(w.elements.dismiss.hidden, true);
    await w.window.GymQRPayment.start(new FormData());
    assert.equal(w.calls.filter(call => call.url === '/payments/qrph/attempts/').length, 0);
    w.server.detail = {...w.server.current, status: 'cancelled', is_unresolved: false, can_cancel: false};
    w.server.current = null;
    await w.poll();
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.elements.floating.hidden, true);
});

test('provider-confirmed expiry clears a minimized cancellation after polling', async () => {
    const w = await widget({current: checkout({status: 'cancel_requested', can_cancel: false})});
    w.window.GymQRPayment.minimize();
    assert.equal(w.elements.floating.hidden, false);
    w.server.detail = {...w.server.current, status: 'expired', is_unresolved: false};
    w.server.current = null;
    await w.poll();
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.elements.floating.hidden, true);
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.storage.has(prefix + 'attempt'), false);
});

test('a saved cancelled attempt is removed on page reload', async () => {
    const saved = checkout({status: 'cancelled', is_unresolved: false, can_cancel: false});
    const w = await widget({current: null, saved});
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.elements.floating.hidden, true);
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.storage.has(prefix + 'attempt'), false);
});

test('a payment that wins the cancellation race keeps its completed receipt visible', async () => {
    const w = await widget();
    w.server.cancel = {...w.server.current, status: 'completed', is_unresolved: false,
        can_cancel: false, payment: {id: 'receipt'}, test_mode: false};
    await w.elements.cancel.emit('click');
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.elements.overlay.hidden, false);
    assert.equal(w.elements.title.textContent, 'Payment completed');
    assert.equal(w.elements.dismiss.hidden, false);
    assert.equal(w.storage.get(prefix + 'attempt'), w.server.cancel.id);
});
