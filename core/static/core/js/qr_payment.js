/* The server owns payment state. Storage contains only a user-scoped attempt UUID and display preference. */
document.addEventListener('DOMContentLoaded', () => {
    'use strict';
    const root = document.getElementById('gymqr-widget');
    if (!root) return;
    const el = id => document.getElementById(`gymqr-${id}`);
    const prefix = `gymms:qrph:${root.dataset.userId}:`;
    const read = key => { try { return localStorage.getItem(prefix + key); } catch (_) { return null; } };
    const save = (key, value) => { try { value === null ? localStorage.removeItem(prefix + key) : localStorage.setItem(prefix + key, value); } catch (_) { /* Storage is optional. */ } };
    const uuid = value => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value || '');
    let attempt = null, busy = false, starting = false, minimized = read('minimized') === 'true';
    let returnFocus = null, previousOverflow = '', noticeTimer, terminalAnnounced = null, generation = 0;
    let inertElements = [], serverOffset = 0;
    let closeTimer, resultTimer, resultKey = null, resultDeadline = 0, visualKey = null, imageKey = null, localResult = false;
    const reducedMotion = () => window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const canAutoClose = a => a && !a.is_unresolved && !a.review_required && ['completed', 'failed'].includes(a.status);
    function resetResult() {
        clearTimeout(resultTimer); resultKey = null; resultDeadline = 0;
        el('autoclose').hidden = true;
    }
    function scheduleResult(a) {
        if (!canAutoClose(a)) { resetResult(); return; }
        const key = `${a.id || generation}:${a.status}`;
        if (resultKey === key) return;
        resetResult(); resultKey = key; resultDeadline = Date.now() + 5000;
        el('autoclose').hidden = false;
        if (el('autoclose').getAnimations) el('autoclose').getAnimations({subtree:true}).forEach(animation => { animation.currentTime = 0; });
        el('close-label').textContent = 'Closing in 5 seconds';
        resultTimer = setTimeout(() => { if (resultKey === key) clearAttempt(); }, 5000);
    }
    const labels = {preparing:'Preparing QR', ready:'QR Ph ready', processing:'Confirming payment', cancel_requested:'Cancelling payment', needs_review:'Owner help required', completed:'Payment completed', cancelled:'Payment cancelled', expired:'QR expired', failed:'Payment failed'};
    function notice(message) { el('notice').textContent = message; clearTimeout(noticeTimer); noticeTimer = setTimeout(() => { el('notice').textContent = ''; }, 8000); }
    function open() {
        clearTimeout(closeTimer); el('overlay').dataset.closing = 'false';
        minimized = false; save('minimized', 'false');
        if (el('overlay').hidden) { returnFocus = document.activeElement; previousOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden';
            inertElements = [...document.body.children].filter(node => node !== root && !node.contains(root) && !['SCRIPT','STYLE','LINK'].includes(node.tagName)).map(node => [node, node.inert]);
            inertElements.forEach(([node]) => { node.inert = true; });
        }
        el('overlay').hidden = false; el('floating').hidden = true; el('minimize').focus();
    }
    function minimize() {
        minimized = true; save('minimized', 'true');
        if (!el('overlay').hidden && el('overlay').dataset.closing !== 'true') {
            el('overlay').dataset.closing = 'true';
            const finish = () => {
                el('overlay').hidden = true; el('overlay').dataset.closing = 'false';
                document.body.style.overflow = previousOverflow;
                inertElements.forEach(([node, previous]) => { node.inert = previous; }); inertElements = [];
                if (returnFocus && returnFocus.isConnected) returnFocus.focus();
                render();
            };
            if (reducedMotion()) finish(); else closeTimer = setTimeout(finish, 180);
        }
        el('floating').hidden = !attempt && !starting;
    }
    function clearAttempt() {
        generation++;
        resetResult(); localResult = false;
        attempt = null; save('attempt', null);
        minimize(); render();
    }
    function csrf() { const field = document.querySelector('[name=csrfmiddlewaretoken]'); return field ? field.value : decodeURIComponent((document.cookie.match(/(?:^|; )csrftoken=([^;]*)/) || [,''])[1]); }
    async function request(url, options = {}) {
        const response = await fetch(url, {credentials:'same-origin', ...options});
        const data = await response.json();
        if (!response.ok || !data.success) { const error = new Error(data.message || data.error || 'Unable to update payment.'); error.attempt = data.attempt; error.status = response.status; throw error; }
        return data;
    }
    function safeProviderURL(value) {
        try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password && (url.hostname === 'paymongo.com' || url.hostname.endsWith('.paymongo.com')) ? url.href : null; } catch (_) { return null; }
    }
    function titleFor(a) {
        if (a.status === 'completed' && a.review_required) return 'Payment received — Owner review required';
        if (a.status === 'completed' && a.test_mode && !a.payment) return 'Test simulation completed';
        return labels[a.status] || 'QR Ph payment';
    }
    function updateCountdown() {
        if (resultDeadline) el('close-label').textContent = `Closing in ${Math.max(1, Math.ceil((resultDeadline - Date.now()) / 1000))} seconds`;
        if (!attempt || !attempt.is_unresolved || !attempt.expires_at) { el('expiry').textContent = ''; return; }
        const remaining = Math.ceil((Date.parse(attempt.expires_at) - Date.now() - serverOffset) / 1000);
        el('expiry').textContent = remaining > 0 ? `QR expires in ${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, '0')}. Final status is confirmed by the provider.` : 'QR time elapsed — awaiting provider confirmation. Do not collect another payment until the status is confirmed.';
    }
    function render() {
        const a = attempt;
        // Keep the result visible throughout its exit animation.
        if (el('overlay').dataset.closing === 'true') {
            el('floating').hidden = !minimized || (!a && !starting);
            window.dispatchEvent(new CustomEvent('gymms:qr-state', {detail:a}));
            return;
        }
        const state = a ? a.review_required || a.status === 'needs_review' ? 'review' : a.status : 'preparing';
        const nextVisualKey = `${a ? a.id || generation : ''}:${state}`;
        const previousHeight = visualKey !== nextVisualKey && !el('overlay').hidden && el('dialog').getBoundingClientRect ? el('dialog').getBoundingClientRect().height : 0;
        el('autoclose').hidden = !canAutoClose(a);
        if (visualKey !== nextVisualKey) {
            visualKey = nextVisualKey;
            el('visual').dataset.state = state;
            el('dialog').dataset.state = state;
            if (el('visual').animate && !reducedMotion()) el('visual').animate([{opacity:0, transform:'translateY(6px) scale(.92)'}, {opacity:1, transform:'translateY(0) scale(1)'}], {duration:280, easing:'cubic-bezier(.2,.8,.2,1)'});
        }
        el('dialog').dataset.result = String(!!a && ['completed', 'failed', 'needs_review'].includes(a.status));
        el('title').textContent = a ? titleFor(a) : 'Preparing QR';
        el('summary').textContent = a ? [a.customer_name, a.plan_label, a.amount ? `${a.currency || 'PHP'} ${a.amount}` : ''].filter(Boolean).join(' · ') : '';
        el('message').textContent = a ? a.status === 'needs_review' ? `${a.message || 'Payment status is uncertain.'} Ask an Owner to review this payment before trying again.` : a.message || (a.status === 'ready' ? 'Scan using GCash, GoTyme, Maya, or another QR Ph app.' : '') : 'Please wait while we prepare your payment.';
        if (a && a.status === 'completed' && a.test_mode && !a.payment) el('message').textContent = 'TEST MODE simulation complete. No payment receipt, membership extension, check-in, or revenue was recorded.';
        else if (a && a.review_required && a.status === 'completed') el('message').textContent = `${a.message || 'Payment was received but membership fulfillment requires review.'} Ask an Owner for help. Membership renewal is not confirmed.`;
        const nextImageKey = JSON.stringify(a && a.status === 'ready' ? [a.id, a.test_mode, a.test_url, a.qr_image] : null);
        if (imageKey !== nextImageKey) {
            imageKey = nextImageKey;
            el('image-area').replaceChildren();
            if (a && a.status === 'ready') {
                if (a.test_mode) {
                    const box = document.createElement('div'); box.className = 'gymqr-test'; box.textContent = 'TEST MODE — no QR code is displayed. Use the payment simulator.';
                    const safe = safeProviderURL(a.test_url);
                    if (safe) { const link = document.createElement('a'); link.href = safe; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Open TEST payment simulator'; box.append(link); }
                    el('image-area').append(box);
                } else {
                    const safe = /^data:image\/png;base64,[A-Za-z0-9+/]+={0,2}$/.test(a.qr_image || '') ? a.qr_image : safeProviderURL(a.qr_image);
                    if (safe) { const img = document.createElement('img'); img.src = safe; img.alt = 'QR Ph payment code'; el('image-area').append(img); }
                    else el('message').textContent = 'QR image unavailable. Ask an Owner for help; do not collect a second payment.';
                }
            }
        }
        updateCountdown();
        el('cancel').hidden = !a || !a.is_unresolved || a.can_cancel !== true || !!a.payment || !!a.provider_payment_id || a.status === 'cancel_requested';
        el('cancel').disabled = busy || starting;
        el('dismiss').hidden = starting || !!(a && a.is_unresolved);
        el('floating').textContent = a ? `${titleFor(a)} — ${a.customer_name || 'Customer'} — ${a.currency || 'PHP'} ${a.amount || ''}` : 'Preparing QR';
        el('floating').hidden = !minimized || (!a && !starting);
        if (previousHeight && el('dialog').animate && !reducedMotion()) {
            const height = el('dialog').getBoundingClientRect().height;
            if (Math.abs(height - previousHeight) > 1) el('dialog').animate([{height:`${previousHeight}px`}, {height:`${height}px`}], {duration:240, easing:'cubic-bezier(.2,.8,.2,1)'});
        }
        window.dispatchEvent(new CustomEvent('gymms:qr-state', {detail:a}));
    }
    function update(a) {
        if (!a) return;
        if (attempt && attempt.is_unresolved && attempt.id !== a.id && !a.is_unresolved) return;
        if (!a.is_unresolved && !a.review_required && ['cancelled', 'expired'].includes(a.status)) {
            clearAttempt(); notice(titleFor(a));
            return;
        }
        const previous = attempt;
        if (a.server_time && Number.isFinite(Date.parse(a.server_time))) serverOffset = Date.parse(a.server_time) - Date.now();
        attempt = a; save('attempt', a.id);
        if (canAutoClose(a) && (!previous || previous.id !== a.id || previous.status !== a.status)) open();
        render();
        scheduleResult(a);
        if ((!previous || previous.status !== a.status) && ['ready','completed','needs_review'].includes(a.status)) notice(titleFor(a));
        if (a.status === 'completed' && a.payment && terminalAnnounced !== a.id) {
            terminalAnnounced = a.id;
            window.dispatchEvent(new CustomEvent('gymms:payment-completed', {detail:a}));
        }
    }
    async function refresh() {
        if (busy || starting || localResult || document.hidden) return;
        busy = true;
        const refreshGeneration = generation;
        try {
            const data = await request('/payments/qrph/current/');
            if (refreshGeneration !== generation) return;
            if (data.attempt) update(data.attempt);
            else { const id = attempt ? attempt.id : read('attempt'); if (uuid(id)) { const last = await request(`/payments/qrph/attempts/${id}/`); if (refreshGeneration === generation) update(last.attempt); } }
            if (attempt && !minimized && el('overlay').hidden) open();
        } catch (_) { if (attempt && attempt.is_unresolved) { el('message').textContent = 'Connection interrupted. Payment remains pending; checking again automatically.'; } }
        finally { busy = false; el('cancel').disabled = starting; }
    }
    window.GymQRPayment = {
        async start(formData) {
            if (starting || (attempt && attempt.is_unresolved)) { open(); return; }
            // Let the API serialize concurrent requests and return the account's unresolved attempt.
            generation++; resetResult(); localResult = false; starting = true; attempt = null; open(); render();
            if (!formData.get('request_key')) formData.set('request_key', crypto.randomUUID());
            try { update((await request('/payments/qrph/attempts/', {method:'POST', body:formData, headers:{'X-CSRFToken':csrf()}})).attempt); }
            catch (error) {
                if (!error.attempt && error.status === 409) { try { error.attempt = (await request('/payments/qrph/current/')).attempt; } catch (_) { /* Next poll retries restoration. */ } }
                if (error.attempt) update(error.attempt); else { el('title').textContent = 'Unable to prepare QR'; el('message').textContent = error.message; el('dismiss').hidden = false; notice(error.message); } }
            finally { starting = false; if (attempt) render(); el('dismiss').hidden = !!(attempt && attempt.is_unresolved); }
        },
        showResult({success, message, customerName = '', amount = ''}) {
            if (starting || (attempt && attempt.is_unresolved)) return false;
            generation++; resetResult(); localResult = true;
            attempt = {status:success ? 'completed' : 'failed', is_unresolved:false, message,
                customer_name:customerName, amount, currency:'PHP'};
            open(); render(); scheduleResult(attempt);
            return true;
        }, minimize, reopen:open,
        get unresolved() { return starting || !!(attempt && attempt.is_unresolved); }
    };
    el('minimize').addEventListener('click', minimize);
    el('floating').addEventListener('click', open);
    el('overlay').addEventListener('click', event => { if (event.target === el('overlay')) minimize(); });
    el('dialog').addEventListener('keydown', event => {
        if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); minimize(); }
        if (event.key === 'Tab') {
            const focusable = [...el('dialog').querySelectorAll('button:not([hidden]):not(:disabled), a[href]')];
            const first = focusable[0], last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
        }
    });
    el('dismiss').addEventListener('click', () => { if (attempt && attempt.is_unresolved) return; clearAttempt(); });
    el('cancel').addEventListener('click', async () => {
        if (!attempt || !attempt.is_unresolved || attempt.can_cancel !== true || attempt.payment || attempt.provider_payment_id || busy || starting) return;
        busy = true; render();
        try { update((await request(`/payments/qrph/attempts/${attempt.id}/cancel/`, {method:'POST', headers:{'X-CSRFToken':csrf()}})).attempt); }
        catch (error) { if (error.attempt) update(error.attempt); notice(error.message + ' Payment remains unresolved until confirmed.'); }
        finally { busy = false; render(); }
    });
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
    window.addEventListener('storage', event => {
        if (!event.key || !event.key.startsWith(prefix)) return;
        if (event.key === prefix + 'attempt' && event.newValue === null && attempt && !attempt.is_unresolved) clearAttempt();
        minimized = read('minimized') === 'true';
        if (minimized && !el('overlay').hidden) minimize();
        refresh();
    });
    setInterval(updateCountdown, 1000);
    setInterval(refresh, 3000);
    refresh();
});
