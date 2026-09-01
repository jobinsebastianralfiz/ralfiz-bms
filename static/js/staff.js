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
  });
})();
