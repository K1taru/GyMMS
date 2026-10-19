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

async function widget({current = checkout(), saved = null, reducedMotion = false} = {}) {
    const ids = ['widget', 'overlay', 'dialog', 'floating', 'notice', 'minimize', 'cancel',
        'dismiss', 'title', 'summary', 'message', 'image-area', 'expiry', 'visual', 'autoclose', 'close-label'];
    const elements = Object.fromEntries(ids.map(id => [id, element()]));
    const root = elements.widget;
    root.dataset.userId = 'staff';
    const background = element();
    const document = Object.assign(element(), {
        hidden: false, body: Object.assign(element(), {children: [root, background]}),
        activeElement: element(), getElementById: id => id === 'gymqr-widget' ? root : elements[id.replace('gymqr-', '')],
        querySelector: () => ({value: 'csrf-fixture'}), createElement: () => element(),
    });
    const states = [], events = [], calls = [], intervals = new Map(), storage = new Map(), timers = new Map();
    let clock = 0, timerId = 0;
    if (saved) storage.set(prefix + 'attempt', saved.id);
    const server = {current, detail: saved, cancel: null, created: checkout(), cancelError: null, dropCancelResponse: false};
    const window = Object.assign(element(), {
        dispatchEvent(event) { states.push(event.detail); events.push(event); },
        matchMedia: () => ({matches: reducedMotion}),
    });
    runInNewContext(source, {
        document, window, crypto: {randomUUID}, URL, Date,
        localStorage: {
            getItem: key => storage.get(key) ?? null,
            setItem: (key, value) => storage.set(key, String(value)),
            removeItem: key => storage.delete(key),
        },
        CustomEvent: class { constructor(type, options) { this.type = type; this.detail = options.detail; } },
        setInterval: (fn, ms) => intervals.set(ms, fn),
        setTimeout: (fn, ms) => { const id = ++timerId; timers.set(id, {fn, at:clock + ms}); return id; },
        clearTimeout: id => timers.delete(id),
        fetch: async (url, options) => {
            calls.push({url, options});
            let attempt;
            if (url.endsWith('/cancel/')) {
                if (server.cancelError) throw new Error(server.cancelError);
                attempt = server.cancel;
                server.current = (attempt.blocks_checkout ?? attempt.is_unresolved) ? attempt : null;
                server.detail = attempt;
                if (server.dropCancelResponse) throw new Error('Response lost');
            } else if (url.endsWith('/current/')) attempt = server.current;
            else if (url === '/payments/qrph/attempts/') attempt = server.current = server.created;
            else attempt = server.detail;
            return {ok: true, json: async () => ({success: true, attempt})};
        },
    });
    await document.emit('DOMContentLoaded');
    return {elements, window, document, storage, server, calls, states, events, background,
        advance: async ms => {
            const target = clock + ms;
            while (true) {
                const next = [...timers].filter(([, timer]) => timer.at <= target).sort((a, b) => a[1].at - b[1].at)[0];
                if (!next) break;
                clock = next[1].at; timers.delete(next[0]); next[1].fn(); await flush();
            }
            clock = target;
        },
        poll: async () => { await intervals.get(3000)(); await flush(); }};
}

test('confirmed cancellation clears modal, floating badge and storage, and permits a fresh checkout', async () => {
    const w = await widget();
    assert.equal(w.window.GymQRPayment.unresolved, true);
    w.server.cancel = {...w.server.current, status: 'cancelled', is_unresolved: false, can_cancel: false};
    await w.elements.cancel.emit('click');
    await w.advance(180);
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
    await w.advance(180);
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.elements.floating.hidden, true);
});

test('staff cancellation closes immediately while PayMongo remains unresolved and permits retry', async () => {
    const w = await widget({current:checkout({test_mode:false, qr_image:'data:image/png;base64,YQ=='})});
    assert.ok(w.elements['image-area'].children.length);
    w.server.cancel = {...w.server.current, status:'cancel_requested', is_unresolved:true,
        blocks_checkout:false, staff_cancelled_at:'2026-10-19T12:00:00Z', can_cancel:false};
    await w.elements.cancel.emit('click');
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.elements['image-area'].children.length, 0);
    assert.equal(w.elements.floating.hidden, true);
    assert.equal(w.storage.has(prefix + 'attempt'), false);
    assert.match(w.elements.notice.textContent, /Payment process cancelled\. You can process another payment\./);
    assert.match(w.elements.notice.textContent, /Do not use the old QR/);
    await w.advance(180);
    assert.equal(w.elements.overlay.hidden, true);
    await w.poll();
    assert.equal(w.elements.overlay.hidden, true);
    await w.window.GymQRPayment.start(new FormData());
    assert.equal(w.window.GymQRPayment.unresolved, true);
    assert.equal(w.states.at(-1).id, w.server.created.id);
});

test('a cancellation network failure retains recovery until the server confirms it', async () => {
    const w = await widget();
    const id = w.server.current.id;
    w.server.cancelError = 'Connection interrupted';
    await w.elements.cancel.emit('click');
    assert.equal(w.window.GymQRPayment.unresolved, true);
    assert.equal(w.storage.get(prefix + 'attempt'), id);
    assert.equal(w.elements.overlay.hidden, false);
    assert.match(w.elements.notice.textContent, /Cancellation was not confirmed by GyMMS/);
    await w.window.GymQRPayment.start(new FormData());
    assert.equal(w.calls.filter(call => call.url === '/payments/qrph/attempts/').length, 0);
});

test('a lost cancellation response is recovered by reading the cancelled attempt', async () => {
    const w = await widget();
    w.server.cancel = {...w.server.current, status:'cancel_requested', blocks_checkout:false,
        staff_cancelled_at:'2026-10-19T12:00:00Z', can_cancel:false};
    w.server.dropCancelResponse = true;
    await w.elements.cancel.emit('click');
    assert.equal(w.window.GymQRPayment.unresolved, true);
    await w.poll();
    await w.advance(180);
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.storage.has(prefix + 'attempt'), false);
});

test('locally cancelled attempts stay closed after reload even with a late receipt under review', async () => {
    for (const status of ['cancel_requested', 'completed']) {
        const saved = checkout({status, blocks_checkout:false, staff_cancelled_at:'2026-10-19T12:00:00Z',
            review_required:true, payment:status === 'completed' ? {id:'late-receipt'} : null});
        const w = await widget({current:null, saved});
        await w.advance(5180);
        assert.equal(w.elements.overlay.hidden, true);
        assert.equal(w.elements.floating.hidden, true);
        assert.equal(w.window.GymQRPayment.unresolved, false);
        assert.equal(w.storage.has(prefix + 'attempt'), false);
        assert.equal(w.events.filter(event => event.type === 'gymms:payment-completed').length, 0);
    }
});

test('cancellation in another tab is verified without restoring its badge or blocking cash', async () => {
    const w = await widget();
    w.server.detail = {...w.server.current, status:'cancel_requested', blocks_checkout:false,
        staff_cancelled_at:'2026-10-19T12:00:00Z'};
    w.server.current = null;
    w.storage.delete(prefix + 'attempt');
    await w.window.emit('storage', {key:prefix + 'attempt', newValue:null});
    await w.advance(180);
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.elements.floating.hidden, true);
    assert.equal(w.window.GymQRPayment.unresolved, false);
    assert.equal(w.window.GymQRPayment.showResult({success:true, message:'Cash received.'}), true);
});

test('provider-confirmed expiry clears a minimized cancellation after polling', async () => {
    const w = await widget({current: checkout({status: 'cancel_requested', can_cancel: false})});
    w.window.GymQRPayment.minimize();
    await w.advance(180);
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

test('success stays visible for five seconds across polls, then fades out and restores focus', async () => {
    const w = await widget();
    w.server.current = {...w.server.current, status:'completed', is_unresolved:false, payment:{id:'receipt'}};
    await w.poll();
    assert.equal(w.elements.visual.dataset.state, 'completed');
    assert.equal(w.elements.autoclose.hidden, false);
    await w.advance(3000);
    await w.poll();
    await w.advance(1999);
    assert.equal(w.elements.overlay.dataset.closing, 'false');
    await w.advance(1);
    assert.equal(w.elements.overlay.hidden, false);
    assert.equal(w.elements.overlay.dataset.closing, 'true');
    assert.equal(w.elements.title.textContent, 'Payment completed');
    assert.equal(w.background.inert, true);
    await w.advance(180);
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.background.inert, false);
    assert.equal(w.document.activeElement.focused, true);
    assert.equal(w.elements.floating.hidden, true);
    assert.equal(w.storage.has(prefix + 'attempt'), false);
    assert.equal(w.events.filter(event => event.type === 'gymms:payment-completed').length, 1);
    w.server.current = null;
    await w.poll();
    assert.equal(w.elements.overlay.hidden, true);
});

test('confirmed failure auto-closes; unresolved failure and owner review stay available', async () => {
    for (const changes of [
        {status:'failed', is_unresolved:false, review_required:false},
        {status:'failed', is_unresolved:true, review_required:false},
        {status:'completed', is_unresolved:false, review_required:true},
        {status:'needs_review', is_unresolved:true, review_required:true},
    ]) {
        const w = await widget({current:checkout(changes)});
        const shouldClose = changes.status === 'failed' && !changes.is_unresolved;
        assert.equal(w.elements.autoclose.hidden, !shouldClose);
        await w.advance(5180);
        assert.equal(w.elements.overlay.hidden, shouldClose);
        assert.equal(w.storage.has(prefix + 'attempt'), !shouldClose);
    }
});

test('polling preserves the QR image node', async () => {
    const w = await widget({current:checkout({test_mode:false, qr_image:'data:image/png;base64,YQ=='})});
    const image = w.elements['image-area'].children[0];
    assert.ok(image);
    await w.poll();
    assert.equal(w.elements['image-area'].children[0], image);
});

test('reopening during exit cancels hiding and preserves background isolation', async () => {
    const w = await widget();
    w.window.GymQRPayment.minimize();
    await w.advance(90);
    w.window.GymQRPayment.reopen();
    await w.advance(180);
    assert.equal(w.elements.overlay.hidden, false);
    assert.equal(w.elements.overlay.dataset.closing, 'false');
    assert.equal(w.background.inert, true);
});

test('a fresh checkout cancels the previous result timer', async () => {
    const w = await widget({current:checkout({status:'completed', is_unresolved:false})});
    await w.advance(4000);
    await w.window.GymQRPayment.start(new FormData());
    await w.advance(1180);
    assert.equal(w.window.GymQRPayment.unresolved, true);
    assert.equal(w.elements.overlay.hidden, false);
    assert.equal(w.elements.title.textContent, 'QR Ph ready');
});

test('cash results use the same timer without polling historical QR attempts', async () => {
    const w = await widget({current:null});
    assert.equal(w.window.GymQRPayment.showResult({success:false, message:'Payment could not be processed.'}), true);
    assert.equal(w.elements.visual.dataset.state, 'failed');
    const count = w.calls.length;
    await w.poll();
    assert.equal(w.calls.length, count);
    await w.advance(5180);
    assert.equal(w.elements.overlay.hidden, true);
});

test('cash results cannot replace an unresolved QR payment', async () => {
    const w = await widget();
    assert.equal(w.window.GymQRPayment.showResult({success:true, message:'Cash received.'}), false);
    assert.equal(w.elements.title.textContent, 'QR Ph ready');
    assert.equal(w.window.GymQRPayment.unresolved, true);
});

test('reduced motion closes immediately after the five-second result period', async () => {
    const w = await widget({current:checkout({status:'completed', is_unresolved:false}), reducedMotion:true});
    await w.advance(4999);
    assert.equal(w.elements.overlay.hidden, false);
    await w.advance(1);
    assert.equal(w.elements.overlay.hidden, true);
    assert.equal(w.background.inert, false);
});

test('a terminal result reopens a minimized QR payment for its result animation', async () => {
    const w = await widget();
    w.window.GymQRPayment.minimize();
    await w.advance(180);
    w.server.current = {...w.server.current, status:'failed', is_unresolved:false};
    await w.poll();
    assert.equal(w.elements.overlay.hidden, false);
    assert.equal(w.elements.visual.dataset.state, 'failed');
    assert.equal(w.elements.autoclose.hidden, false);
    assert.equal(w.elements.floating.hidden, true);
    await w.advance(5180);
    assert.equal(w.elements.overlay.hidden, true);
});
