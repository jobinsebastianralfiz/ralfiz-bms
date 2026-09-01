/* Staff portal runtime.
 *
 * Every write goes to the existing DRF endpoints under /api/employees/ using
 * session auth + CSRF, so attendance/leave/face rules are never duplicated here.
 */
(function () {
  'use strict';

  var SF = window.SF || {};
  window.SF = SF;

  SF.csrf = window.SF_CSRF || '';

  // --- API -----------------------------------------------------------

  SF.api = function (url, opts) {
    opts = opts || {};
    var headers = { 'X-CSRFToken': SF.csrf, 'X-Requested-With': 'XMLHttpRequest' };
    var body = opts.body;

    if (body && !(body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(body);
    }

    return fetch(url, {
      method: opts.method || 'GET',
      headers: headers,
      body: body,
      credentials: 'same-origin'
    }).then(function (res) {
      return res.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = { detail: text }; }
        return { ok: res.ok, status: res.status, data: data };
      });
    });
  };

  /* Pull a human message out of a DRF error body, whatever shape it took. */
  SF.errorText = function (data, fallback) {
    if (!data) return fallback || 'Something went wrong. Please try again.';
    if (typeof data === 'string') return data;
    if (data.error) return data.error;
    if (data.detail) return data.detail;
    var keys = Object.keys(data);
    for (var i = 0; i < keys.length; i++) {
      var v = data[keys[i]];
      if (Array.isArray(v) && v.length) return keys[i] + ': ' + v[0];
      if (typeof v === 'string') return keys[i] + ': ' + v;
    }
    return fallback || 'Something went wrong. Please try again.';
  };

  // --- Toast ---------------------------------------------------------

  SF.toast = function (msg, kind) {
    var el = document.createElement('div');
    el.className = 'sf-alert sf-alert-' + (kind || 'info');
    el.textContent = msg;
    el.style.cssText = 'position:fixed;left:16px;right:16px;top:calc(12px + env(safe-area-inset-top));z-index:90;box-shadow:0 8px 30px rgba(0,0,0,.5)';
    document.body.appendChild(el);
    setTimeout(function () {
      el.style.transition = 'opacity .3s';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 300);
    }, kind === 'error' ? 5200 : 3200);
  };

  // --- Geolocation ---------------------------------------------------

  SF.getLocation = function () {
    return new Promise(function (resolve, reject) {
      if (!navigator.geolocation) {
        reject(new Error('This browser cannot share your location.'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        function (pos) {
          resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
        },
        function (err) {
          if (err.code === 1) {
            reject(new Error('Location permission denied. On iPhone: Settings > Safari > Location, or tap "aA" in the address bar > Website Settings.'));
          } else if (err.code === 3) {
            reject(new Error('Could not get a location fix. Move near a window and try again.'));
          } else {
            reject(new Error('Could not read your location. Please try again.'));
          }
        },
        { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
      );
    });
  };

  // --- Modal ---------------------------------------------------------

  function openModal(title) {
    var back = document.createElement('div');
    back.className = 'sf-modal-backdrop';
    back.innerHTML =
      '<div class="sf-modal-head">' +
        '<div class="sf-modal-title"></div>' +
        '<button type="button" class="sf-modal-close" aria-label="Close"><i class="fas fa-xmark"></i></button>' +
      '</div>' +
      '<div class="sf-modal-body"></div>';
    back.querySelector('.sf-modal-title').textContent = title;
    document.body.appendChild(back);
    document.body.style.overflow = 'hidden';

    return {
      el: back,
      body: back.querySelector('.sf-modal-body'),
      setTitle: function (t) { back.querySelector('.sf-modal-title').textContent = t; },
      onClose: null,
      close: function () {
        back.remove();
        document.body.style.overflow = '';
      },
      bindClose: function (fn) {
        back.querySelector('.sf-modal-close').addEventListener('click', fn);
      }
    };
  }

  SF.openModal = openModal;

  // --- Camera helpers -------------------------------------------------

  function stopStream(stream) {
    if (!stream) return;
    stream.getTracks().forEach(function (t) { t.stop(); });
  }

  function cameraErrorText(err) {
    var name = err && err.name;
    if (name === 'NotAllowedError' || name === 'SecurityError') {
      return 'Camera permission denied. On iPhone tap "aA" in the address bar > Website Settings > Camera > Allow, then reload.';
    }
    if (name === 'NotFoundError' || name === 'OverconstrainedError') {
      return 'No usable camera found on this device.';
    }
    if (name === 'NotReadableError') {
      return 'The camera is being used by another app. Close it and try again.';
    }
    if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
      return 'The camera needs a secure (https) connection.';
    }
    return 'Could not start the camera. Please try again.';
  }

  SF.cameraErrorText = cameraErrorText;

  /* Capture a selfie. Resolves with a JPEG Blob, or rejects if cancelled. */
  SF.captureSelfie = function (modal, prompt) {
    return new Promise(function (resolve, reject) {
      modal.body.innerHTML =
        '<div class="sf-cam sf-cam-selfie"><video playsinline muted autoplay></video></div>' +
        '<p class="sf-muted" style="text-align:center;margin:0 0 14px">' + (prompt || 'Position your face in the frame.') + '</p>' +
        '<button type="button" class="sf-btn" id="sfShoot"><i class="fas fa-camera"></i> Capture</button>';

      var video = modal.body.querySelector('video');
      var stream = null;

      navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 1280 } },
        audio: false
      }).then(function (s) {
        stream = s;
        video.srcObject = s;
        video.setAttribute('playsinline', '');   // iOS: play inline, not fullscreen
        video.muted = true;
        return video.play();
      }).catch(function (err) {
        stopStream(stream);
        reject(new Error(cameraErrorText(err)));
      });

      modal.body.querySelector('#sfShoot').addEventListener('click', function () {
        if (!video.videoWidth) {
          SF.toast('Camera is still starting, try again in a moment.', 'warning');
          return;
        }
        var size = Math.min(video.videoWidth, video.videoHeight);
        var canvas = document.createElement('canvas');
        canvas.width = size;
        canvas.height = size;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(
          video,
          (video.videoWidth - size) / 2, (video.videoHeight - size) / 2, size, size,
          0, 0, size, size
        );
        stopStream(stream);
        canvas.toBlob(function (blob) {
          if (blob) resolve(blob);
          else reject(new Error('Could not read the photo from the camera.'));
        }, 'image/jpeg', 0.9);
      });

      modal.onClose = function () { stopStream(stream); };
    });
  };

  /* Scan the office QR. Resolves with the decoded string. */
  SF.scanQR = function (modal) {
    return new Promise(function (resolve, reject) {
      modal.body.innerHTML =
        '<div id="sfQrReader"></div>' +
        '<p class="sf-muted" style="text-align:center;margin:14px 0">Point the camera at the office QR sticker.</p>' +
        '<div class="sf-field">' +
          '<label class="sf-label" for="sfQrManual">Camera not working? Enter the code</label>' +
          '<input class="sf-input" id="sfQrManual" autocomplete="off" autocapitalize="off" spellcheck="false" placeholder="Office code">' +
        '</div>' +
        '<button type="button" class="sf-btn sf-btn-ghost" id="sfQrManualGo">Use this code</button>';

      var scanner = null;
      var settled = false;

      function finish(value) {
        if (settled) return;
        settled = true;
        var done = scanner ? scanner.stop().catch(function () {}) : Promise.resolve();
        done.then(function () { resolve(value); });
      }

      modal.body.querySelector('#sfQrManualGo').addEventListener('click', function () {
        var val = modal.body.querySelector('#sfQrManual').value.trim();
        if (!val) {
          SF.toast('Enter the office code first.', 'warning');
          return;
        }
        finish(val);
      });

      if (!window.Html5Qrcode) {
        modal.body.querySelector('#sfQrReader').innerHTML =
          '<div class="sf-alert sf-alert-warning">Scanner unavailable offline — enter the code below.</div>';
        return;
      }

      scanner = new window.Html5Qrcode('sfQrReader', { verbose: false });
      scanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 230, height: 230 } },
        function (decoded) { finish(decoded); },
        function () { /* per-frame decode misses are normal */ }
      ).catch(function (err) {
        modal.body.querySelector('#sfQrReader').innerHTML =
          '<div class="sf-alert sf-alert-warning">' + cameraErrorText(err) + '</div>';
      });

      modal.onClose = function () {
        settled = true;
        if (scanner) scanner.stop().catch(function () {});
        reject(new Error('cancelled'));
      };
    });
  };

  // --- "More" sheet ---------------------------------------------------

  function initSheet() {
    var btn = document.getElementById('sfMoreBtn');
    var sheet = document.getElementById('sfSheet');
    var backdrop = document.getElementById('sfSheetBackdrop');
    if (!btn || !sheet || !backdrop) return;

    function open() {
      sheet.hidden = false;
      backdrop.hidden = false;
      btn.setAttribute('aria-expanded', 'true');
    }
    function close() {
      sheet.hidden = true;
      backdrop.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
    }

    btn.addEventListener('click', function () {
      if (sheet.hidden) open(); else close();
    });
    backdrop.addEventListener('click', close);

    // The sheet sits above the tab bar, so "More" can't be tapped again to
    // dismiss it -- the grip is the affordance users reach for instead.
    var grip = sheet.querySelector('.sf-sheet-grip');
    if (grip) grip.addEventListener('click', close);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !sheet.hidden) close();
    });
  }

  // --- Install to home screen -----------------------------------------

  var deferredPrompt = null;

  function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }

  function isIOS() {
    // iPadOS 13+ reports as MacIntel, so touch points are the reliable tell.
    return /iphone|ipad|ipod/i.test(navigator.userAgent) ||
           (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  }

  SF.isStandalone = isStandalone;

  function dismissed() {
    try { return localStorage.getItem('sf-install-dismissed') === '1'; }
    catch (e) { return false; }
  }

  function rememberDismissed() {
    try { localStorage.setItem('sf-install-dismissed', '1'); } catch (e) { /* private mode */ }
  }

  /* The how-to. iOS Safari has no install API at all, so the only thing we can
     do there is show the user exactly which buttons to tap. */
  SF.showInstallHelp = function () {
    if (isStandalone()) {
      SF.toast('This is already installed on your home screen.', 'success');
      return;
    }

    var modal = SF.openModal('Add to Home Screen');
    modal.bindClose(function () { modal.close(); });

    if (deferredPrompt) {
      modal.body.innerHTML =
        '<p class="sf-muted" style="margin-top:0">Install this as an app so it opens ' +
        'full screen, straight from your home screen.</p>' +
        '<button type="button" class="sf-btn" id="sfDoInstall">' +
          '<i class="fas fa-download"></i> Install app</button>';
      modal.body.querySelector('#sfDoInstall').addEventListener('click', function () {
        modal.close();
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then(function (choice) {
          if (choice.outcome === 'accepted') SF.toast('Installing…', 'success');
          deferredPrompt = null;
          hideBanner();
        });
      });
      return;
    }

    if (isIOS()) {
      modal.body.innerHTML =
        '<p class="sf-muted" style="margin-top:0">Two taps in Safari and this sits on ' +
        'your home screen like any other app.</p>' +
        '<div class="sf-steps" style="margin-bottom:16px">' +
          '<div class="sf-step active">' +
            '<span class="sf-step-num">1</span>' +
            '<div class="sf-step-body">' +
              '<div class="sf-step-title">Tap Share ' +
                '<i class="fas fa-arrow-up-from-bracket" style="color:var(--sf-teal)"></i></div>' +
              '<div class="sf-step-hint">In the bar at the bottom of Safari</div>' +
            '</div>' +
          '</div>' +
          '<div class="sf-step active">' +
            '<span class="sf-step-num">2</span>' +
            '<div class="sf-step-body">' +
              '<div class="sf-step-title">Choose "Add to Home Screen" ' +
                '<i class="fas fa-square-plus" style="color:var(--sf-teal)"></i></div>' +
              '<div class="sf-step-hint">Scroll down the share list to find it</div>' +
            '</div>' +
          '</div>' +
          '<div class="sf-step active">' +
            '<span class="sf-step-num">3</span>' +
            '<div class="sf-step-body">' +
              '<div class="sf-step-title">Tap Add</div>' +
              '<div class="sf-step-hint">The Ralfiz icon appears on your home screen</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div class="sf-alert">Use <strong>Safari</strong>. On iPhone only Safari can ' +
        'make a real full-screen app -- other browsers either hide the option or add a ' +
        'plain shortcut. If you opened this from a chat, tap the menu and choose ' +
        '<strong>Open in Safari</strong> first.</div>';
      return;
    }

    // Android. Chrome usually gives us beforeinstallprompt and we never get
    // here, but Brave and Firefox often withhold it, so spell out the menu.
    var isAndroid = /android/i.test(navigator.userAgent);
    if (isAndroid) {
      modal.body.innerHTML =
        '<p class="sf-muted" style="margin-top:0">Three taps and this sits on your ' +
        'home screen like any other app.</p>' +
        '<div class="sf-steps" style="margin-bottom:16px">' +
          '<div class="sf-step active">' +
            '<span class="sf-step-num">1</span>' +
            '<div class="sf-step-body">' +
              '<div class="sf-step-title">Tap the menu ' +
                '<i class="fas fa-ellipsis-vertical" style="color:var(--sf-teal)"></i></div>' +
              '<div class="sf-step-hint">Three dots, bottom-right in Brave, top-right in Chrome</div>' +
            '</div>' +
          '</div>' +
          '<div class="sf-step active">' +
            '<span class="sf-step-num">2</span>' +
            '<div class="sf-step-body">' +
              '<div class="sf-step-title">Choose "Add to Home screen"</div>' +
              '<div class="sf-step-hint">Some versions call it "Install app"</div>' +
            '</div>' +
          '</div>' +
          '<div class="sf-step active">' +
            '<span class="sf-step-num">3</span>' +
            '<div class="sf-step-body">' +
              '<div class="sf-step-title">Tap Add</div>' +
              '<div class="sf-step-hint">The Ralfiz icon appears on your home screen</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div class="sf-alert">In-app browsers (WhatsApp, Instagram) cannot install ' +
        'apps. If you opened this from a chat, tap the menu and choose ' +
        '<strong>Open in browser</strong> first.</div>';
      return;
    }

    modal.body.innerHTML =
      '<p class="sf-muted" style="margin-top:0">Open your browser menu and choose ' +
      '<strong>Install app</strong> or <strong>Add to Home screen</strong>.</p>' +
      '<div class="sf-alert">If you do not see it, your browser may not support installing ' +
      'web apps. The portal still works normally in the browser.</div>';
  };

  function hideBanner() {
    var banner = document.getElementById('sfInstallBanner');
    if (banner) banner.hidden = true;
  }

  function initInstall() {
    var banner = document.getElementById('sfInstallBanner');

    // Already installed: no banner, and drop the menu entry too.
    if (isStandalone()) {
      var entry = document.getElementById('sfInstallEntry');
      if (entry) entry.hidden = true;
      return;
    }

    window.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();          // keep Chrome's own mini-infobar out of the way
      deferredPrompt = e;
      if (banner && !dismissed()) banner.hidden = false;
    });

    window.addEventListener('appinstalled', function () {
      deferredPrompt = null;
      hideBanner();
    });

    // Bind the button FIRST. The login page has one but no banner, so binding
    // after the banner check left it dead on exactly the page most people see.
    var open = document.getElementById('sfInstallOpen');
    if (open) open.addEventListener('click', SF.showInstallHelp);

    if (!banner) return;

    // iOS never fires beforeinstallprompt, so offer the banner directly.
    if (isIOS() && !dismissed()) banner.hidden = false;

    var no = document.getElementById('sfInstallDismiss');
    if (no) no.addEventListener('click', function () {
      rememberDismissed();
      hideBanner();
    });
  }

  // --- Service worker -------------------------------------------------

  function initServiceWorker() {
    if (!('serviceWorker' in navigator)) return;
    if (location.protocol !== 'https:' && location.hostname !== 'localhost') return;
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/staff/sw.js', { scope: '/staff/' })
        .catch(function () { /* offline shell is a bonus, never a blocker */ });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initSheet();
    initServiceWorker();
    initInstall();

    var entry = document.getElementById('sfInstallEntry');
    if (entry) entry.addEventListener('click', function (e) {
      e.preventDefault();
      var sheet = document.getElementById('sfSheet');
      var backdrop = document.getElementById('sfSheetBackdrop');
      if (sheet) sheet.hidden = true;
      if (backdrop) backdrop.hidden = true;
      SF.showInstallHelp();
    });
  });
})();
