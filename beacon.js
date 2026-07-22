// Site beacon. Reports a pageview to the analytics collector, routed through the
// ngrok gateway at /collect. The server adds IP + UA + time; the client sends
// path + referrer only. Fails silently if the collector (desktop) is unreachable.
(function () {
  var COLLECT = 'https://herring-chatty-acetone.ngrok-free.dev/collect';
  try {
    fetch(COLLECT, {
      method: 'POST', keepalive: true,
      headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': '1' },
      body: JSON.stringify({
        kind: 'pageview', source: 'site',
        path: location.pathname, ref: document.referrer || ''
      })
    }).catch(function () {});
  } catch (e) {}
})();
