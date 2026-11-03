import asyncio
import os
from playwright.async_api import async_playwright, Browser, Page
from typing import Optional, List, Dict
from .interceptor import NetworkInterceptor, NetworkRequest, NetworkResponse

# HTTP/2 pseudo-headers surfaced by CDP but not useful in API docs
_H2_PSEUDO_DROP = {":method", ":path", ":scheme"}


class BrowserRecorder:
    def __init__(self, url: str, filter_static: bool = True, exclude_patterns: Optional[List[str]] = None, output_dir: str = "."):
        self.url = url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        self.interceptor = NetworkInterceptor(filter_static=filter_static, additional_exclude_patterns=exclude_patterns)
        self.playwright = None
        self._done_event: Optional[asyncio.Event] = None
        self.output_dir = output_dir
        self._recording = False
        self._record_count = 0
        self._batch_id: Optional[str] = None  # 批次号，格式：日期_编号

        # CDP correlation state. Playwright's request.headers/response.headers
        # deliberately omit Cookie, Accept-Encoding, Host, Connection, etc.; the
        # Network.*ExtraInfo CDP events contain those. We buffer extra headers
        # by URL and merge them in the Playwright handlers.
        #
        # Order of CDP events for a given request is not guaranteed:
        # Network.requestWillBeSentExtraInfo may fire BEFORE Network.requestWillBeSent
        # (so the URL isn't known yet). We buffer the extras by requestId until
        # the URL arrives, then flush into the URL bucket.
        self._cdp_session = None
        self._cdp_rid_to_url: Dict[str, str] = {}
        self._cdp_pending_request_extras: Dict[str, Dict[str, str]] = {}
        self._cdp_pending_response_extras: Dict[str, Dict[str, str]] = {}
        self._request_extras_by_url: Dict[str, Dict[str, str]] = {}
        self._response_extras_by_url: Dict[str, Dict[str, str]] = {}

        # Stable request id assigned at request time, paired to response via
        # the Playwright Request object identity. Sequential, JSON-safe, no
        # reliance on Python id() which is not stable across GC.
        self._next_request_id = 0
        self._request_to_id: Dict[object, str] = {}

    @staticmethod
    def _normalize_extra_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """Lowercase keys, drop HTTP/2 pseudo-headers, map :authority -> host."""
        out: Dict[str, str] = {}
        for k, v in headers.items():
            kl = k.lower()
            if kl in _H2_PSEUDO_DROP:
                continue
            if kl == ":authority":
                out["host"] = v
            else:
                out[kl] = v
        return out

    # --- CDP event handlers -------------------------------------------------

    def _on_cdp_request_will_be_sent(self, params):
        rid = params["requestId"]
        url = params["request"]["url"]
        self._cdp_rid_to_url[rid] = url
        # If requestWillBeSentExtraInfo arrived first, flush it now.
        pending = self._cdp_pending_request_extras.pop(rid, None)
        if pending:
            bucket = self._request_extras_by_url.setdefault(url, {})
            bucket.update(pending)

    def _on_cdp_request_will_be_sent_extra_info(self, params):
        rid = params.get("requestId", "")
        extras = params.get("headers") or {}
        url = self._cdp_rid_to_url.get(rid)
        if url:
            bucket = self._request_extras_by_url.setdefault(url, {})
            bucket.update(extras)
        else:
            # requestWillBeSent hasn't fired yet for this rid. Buffer by rid
            # so it can be flushed when the URL becomes known.
            bucket = self._cdp_pending_request_extras.setdefault(rid, {})
            bucket.update(extras)

    def _on_cdp_response_received_extra_info(self, params):
        rid = params.get("requestId", "")
        extras = params.get("headers") or {}
        url = self._cdp_rid_to_url.get(rid)
        if url:
            bucket = self._response_extras_by_url.setdefault(url, {})
            bucket.update(extras)
        else:
            bucket = self._cdp_pending_response_extras.setdefault(rid, {})
            bucket.update(extras)

    # --- Playwright event handlers ------------------------------------------

    async def _handle_request(self, request):
        if not self._recording:
            return
        if request.resource_type not in ("xhr", "fetch"):
            return

        url = str(request.url)
        method = request.method

        # Playwright gives us some headers (e.g. user-agent) but omits the
        # restricted ones (cookie, accept-encoding, host, ...). The CDP extra
        # info (requestWillBeSentExtraInfo) is the source of truth for those,
        # but it fires AFTER the Playwright 'request' event in CDP's ordering,
        # so we cannot pop and merge here. Instead we save the partial headers
        # and merge the extras in _handle_response (which fires after both
        # requestWillBeSentExtraInfo and responseReceivedExtraInfo have landed).
        headers = {k.lower(): v for k, v in request.headers.items()}

        body = None
        if method in ("POST", "PUT", "PATCH"):
            pd = request.post_data
            if pd:
                if isinstance(pd, str):
                    body = pd
                elif isinstance(pd, bytes):
                    body = pd.decode("utf-8", errors="replace")
                else:
                    body = str(pd)

        ts = 0.0
        # request.timing is a Playwright ResourceTiming object (not a dict);
        # accessing .get() on it raises AttributeError, which the old
        # hasattr(...) check silently swallowed.
        timing = getattr(request, "timing", None)
        if timing is not None:
            start = getattr(timing, "start_time", None)
            if isinstance(start, (int, float)):
                ts = float(start)

        rid = f"req_{self._next_request_id}"
        self._next_request_id += 1
        self._request_to_id[request] = rid

        req = NetworkRequest(
            id=rid,
            method=method,
            url=url,
            headers=headers,
            body=body,
            timestamp=ts,
        )
        self.interceptor.on_request(req)

    async def _handle_response(self, response):
        url = response.url

        # By the time the Playwright 'response' event fires, both CDP
        # requestWillBeSentExtraInfo and responseReceivedExtraInfo have
        # already populated the per-URL buckets. This is the safe point to
        # pop and merge both.
        request_extras = self._request_extras_by_url.pop(url, {})
        response_extras = self._response_extras_by_url.pop(url, {})

        # Find the request we created in _handle_request and back-fill the
        # late-arriving request extras into its headers.
        request_id = self._request_to_id.get(response.request, "")
        for req in self.interceptor.requests:
            if req.id == request_id:
                if request_extras:
                    for k, v in self._normalize_extra_headers(request_extras).items():
                        req.headers[k] = v
                break

        resp_headers = {k.lower(): v for k, v in response.headers.items()}
        resp_headers.update(self._normalize_extra_headers(response_extras))

        body = None
        try:
            body = await response.text()
        except Exception:
            pass

        ts = 0.0
        timing = getattr(response.request, "timing", None)
        if timing is not None:
            start = getattr(timing, "response_start", None)
            if isinstance(start, (int, float)):
                ts = float(start)

        resp = NetworkResponse(
            request_id=request_id,
            status=response.status,
            headers=resp_headers,
            body=body,
            timestamp=ts,
        )
        self.interceptor.on_response(resp)

    # --- Lifecycle events ---------------------------------------------------

    async def _on_page_close(self):
        if self._done_event and not self._done_event.is_set():
            self._done_event.set()

    async def _on_context_close(self):
        if self._done_event and not self._done_event.is_set():
            self._done_event.set()

    # --- Public API used by the floating ball -------------------------------

    def start_recording(self):
        self._recording = True
        self._record_count += 1

    def stop_recording_and_save(self) -> tuple:
        if not self._recording:
            return (0, 0)
        self._recording = False
        if self._record_count <= 0:
            return (0, 0)
        record_index = self._record_count
        filename = f"raw{record_index:02d}.json"
        # Directory structure: output_dir/batch_id/rawNN.json
        record_dir = os.path.join(self.output_dir, self._batch_id)
        os.makedirs(record_dir, exist_ok=True)
        output_path = os.path.join(record_dir, filename)
        count = self.interceptor.save_flows_to_file(output_path)
        self.interceptor.clear()
        return (count, record_index)

    def save_current_recording(self) -> tuple:
        if self._recording and self._record_count > 0:
            record_index = self._record_count
            filename = f"raw{record_index:02d}.json"
            # Directory structure: output_dir/batch_id/rawNN.json
            record_dir = os.path.join(self.output_dir, self._batch_id)
            os.makedirs(record_dir, exist_ok=True)
            output_path = os.path.join(record_dir, filename)
            count = self.interceptor.save_flows_to_file(output_path)
            self.interceptor.clear()
            return (count, record_index)
        return (0, 0)

    def get_recording_state(self) -> dict:
        state = {
            "is_recording": self._recording,
            "record_count": self._record_count,
        }
        print(f"[PCR] get_recording_state returning: {state}")
        return state

    # --- Browser lifecycle --------------------------------------------------

    async def _setup_browser(self, cdp_port: int = 9222):
        """Launch browser, create context+page, wire up network handlers.

        Used by start() and by integration tests. Does not navigate.
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[f"--remote-debugging-port={cdp_port}"],
        )
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self._done_event = asyncio.Event()

        # CDP session for the headers that Playwright's events omit
        self._cdp_session = await self.context.new_cdp_session(self.page)
        await self._cdp_session.send("Network.enable")
        self._cdp_session.on("Network.requestWillBeSent", self._on_cdp_request_will_be_sent)
        self._cdp_session.on("Network.requestWillBeSentExtraInfo", self._on_cdp_request_will_be_sent_extra_info)
        self._cdp_session.on("Network.responseReceivedExtraInfo", self._on_cdp_response_received_extra_info)

        self.page.on("request", self._handle_request)
        self.page.on("response", self._handle_response)
        self.page.on("close", self._on_page_close)
        self.context.on("close", self._on_context_close)

    async def start(self, cdp_port: int = 9222):
        # Generate batch_id at startup, format: date_sequence (e.g., 20260608_01)
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        # Find next sequence number for today
        seq = 1
        while True:
            batch_id = f"{date_str}_{seq:02d}"
            test_path = os.path.join(self.output_dir, batch_id)
            if not os.path.exists(test_path):
                break
            seq += 1
        self._batch_id = batch_id
        
        await self._setup_browser(cdp_port=cdp_port)

        # Add init script to inject floating ball on EVERY page navigation
        # This runs BEFORE page content loads, so we use load event to inject
        init_script = '''
(function() {
    // Only create ball in top-level window, not in iframes
    if (window !== window.top) return;

    window.__pcr_start_recording = window.__pcr_start_recording || null;
    window.__pcr_stop_recording = window.__pcr_stop_recording || null;

    function createBall() {
        var container = document.createElement('div');
        container.id = 'pcr-floating-ball';
        container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:999999;display:flex;gap:5px;';

        // REC button
        var recBtn = document.createElement('div');
        recBtn.id = 'pcr-rec-btn';
        recBtn.textContent = 'REC';
        recBtn.style.cssText = 'height:36px;padding:0 16px;background:#F44336;border-radius:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,0.3);font-family:Arial,sans-serif;font-size:12px;color:white;user-select:none;font-weight:bold;white-space:nowrap;';

        // STP button
        var stpBtn = document.createElement('div');
        stpBtn.id = 'pcr-stp-btn';
        stpBtn.textContent = 'STP';
        stpBtn.style.cssText = 'height:36px;padding:0 16px;background:#9E9E9E;border-radius:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 10px rgba(0,0,0,0.3);font-family:Arial,sans-serif;font-size:12px;color:white;user-select:none;font-weight:bold;white-space:nowrap;opacity:0.5;';

        // Track recording state in JS (persists across page navs via exposed functions)
        var recordingState = { isRecording: false, recordCount: 0 };

        function updateUIFromState() {
            if (recordingState.isRecording) {
                recBtn.style.background = '#D32F2F';
                recBtn.style.boxShadow = '0 0 15px rgba(244,67,54,0.8)';
                stpBtn.style.opacity = '1';
                stpBtn.style.background = '#F44336';
            } else {
                recBtn.style.background = '#F44336';
                recBtn.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
                stpBtn.style.opacity = '0.5';
                stpBtn.style.background = '#9E9E9E';
            }
        }

        var isDragging = false;
        var hasMoved = false;
        var startX, startY, initX, initY;

        container.addEventListener('mousedown', function(e) {
            if (e.target === container) return;
            isDragging = true;
            hasMoved = false;
            startX = e.clientX;
            startY = e.clientY;
            var rect = container.getBoundingClientRect();
            initX = rect.left;
            initY = rect.top;
            container.style.cursor = 'move';
        });

        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            var dx = e.clientX - startX;
            var dy = e.clientY - startY;
            if (Math.abs(dx) > 5 || Math.abs(dy) > 5) hasMoved = true;
            var x = initX + dx;
            var y = initY + dy;
            x = Math.max(0, Math.min(x, window.innerWidth - container.offsetWidth));
            y = Math.max(0, Math.min(y, window.innerHeight - container.offsetHeight));
            container.style.left = x + 'px';
            container.style.top = y + 'px';
            container.style.right = 'auto';
        });

        document.addEventListener('mouseup', function() {
            isDragging = false;
            container.style.cursor = 'default';
        });

        // REC button click
        recBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            if (hasMoved) return;
            if (window.__pcr_start_recording) {
                window.__pcr_start_recording();
            }
            recordingState.isRecording = true;
            recordingState.recordCount += 1;
            updateUIFromState();
        });

        // STP button click
        stpBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            if (hasMoved) return;
            if (window.__pcr_stop_recording) {
                var result = window.__pcr_stop_recording();
                if (result && result.count !== undefined && result.count > 0) {
                    window.__pcr_last_saved_index = result.recordIndex;
                    alert('Saved ' + result.count + ' requests to raw' + result.recordIndex.toString().padStart(2, '0') + '.json');
                }
            }
            recordingState.isRecording = false;
            updateUIFromState();
        });

        window.__pcr_sync_state = function(state) {
            console.log('[PCR] __pcr_sync_state called with:', JSON.stringify(state));
            recordingState.isRecording = state.is_recording;
            recordingState.recordCount = state.record_count;
            updateUIFromState();
            console.log('[PCR] __pcr_sync_state completed, isRecording:', recordingState.isRecording);
        };

        container.appendChild(recBtn);
        container.appendChild(stpBtn);
        return container;
    }

    async function ensureBall() {
        var existingBall = document.getElementById('pcr-floating-ball');
        if (existingBall) {
            // Ball already exists from previous navigation - sync state if possible
            console.log('[PCR] Ball exists, attempting state sync...');
            if (window.__pcr_get_state && window.__pcr_sync_state) {
                try {
                    // exposed functions return promises, must await
                    var state = await window.__pcr_get_state();
                    console.log('[PCR] Got state from Python:', JSON.stringify(state));
                    await window.__pcr_sync_state(state);
                    console.log('[PCR] State synced successfully');
                } catch(e) {
                    console.log('[PCR] State sync failed:', e.message);
                }
            } else {
                console.log('[PCR] Exposed functions not ready yet');
            }
            return;
        }
        if (!document.body) return;
        console.log('[PCR] Creating new ball');
        document.body.appendChild(createBall());
    }

    // Wait for page load complete before injecting
    window.addEventListener('load', function() {
        console.log('[PCR] Page load event fired');
        ensureBall();

        // Sync recording state from Python on page load (for SPA navigation)
        // Retry a few times since exposed functions may not be ready immediately
        async function trySyncState() {
            console.log('[PCR] trySyncState called');
            if (window.__pcr_get_state && window.__pcr_sync_state) {
                try {
                    // exposed functions return promises, must await
                    var state = await window.__pcr_get_state();
                    console.log('[PCR] Got state from Python:', JSON.stringify(state));
                    await window.__pcr_sync_state(state);
                } catch(e) {
                    console.log('[PCR] State sync error:', e.message);
                }
            } else {
                console.log('[PCR] Functions not available:', {
                    get_state: !!window.__pcr_get_state,
                    sync_state: !!window.__pcr_sync_state
                });
            }
        }
        trySyncState();
        setTimeout(trySyncState, 100);
        setTimeout(trySyncState, 300);
        setTimeout(trySyncState, 500);

        // MutationObserver to keep ball alive on DOM changes
        var observer = new MutationObserver(function(mutations) {
            ensureBall();
        });
        observer.observe(document.documentElement, { childList: true, subtree: true });

        // Listen for history changes (SPA navigation)
        var originalPushState = window.history.pushState;
        window.history.pushState = function() {
            originalPushState.apply(this, arguments);
            setTimeout(function() { ensureBall(); }, 300);
            setTimeout(function() { trySyncState(); }, 500);
        };
        var originalReplaceState = window.history.replaceState;
        window.history.replaceState = function() {
            originalReplaceState.apply(this, arguments);
            setTimeout(function() { ensureBall(); }, 300);
            setTimeout(function() { trySyncState(); }, 500);
        };
        window.addEventListener('popstate', function() {
            setTimeout(function() { ensureBall(); }, 300);
            setTimeout(function() { trySyncState(); }, 500);
        });
    });
})();
'''
        await self.context.add_init_script(init_script)

        # Expose functions for floating ball to call
        # __pcr_click_done is no-op since snap functionality is removed
        await self.page.expose_function("__pcr_click_done", lambda: None)
        await self.page.expose_function("__pcr_start_recording", self.start_recording)
        await self.page.expose_function("__pcr_stop_recording", self.stop_recording_and_save)
        await self.page.expose_function("__pcr_save_current", self.save_current_recording)
        await self.page.expose_function("__pcr_get_state", self.get_recording_state)

        # Navigate to target URL
        await self.page.goto(self.url)
        await self.page.wait_for_load_state("networkidle")

        # Wait for done event
        await self._done_event.wait()

        # Shutdown
        await self.shutdown()

    async def shutdown(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

def start_recording(url: str):
    recorder = BrowserRecorder(url)
    asyncio.run(recorder.start())
