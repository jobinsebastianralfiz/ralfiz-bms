/* Proctored online test (staff portal).

   Before the test: camera on, one screen only, then Start goes fullscreen and
   fetches the questions (the gate page never holds them).

   During the test it locks (server decides, via eventUrl) when the intern
   switches tab, switches to another window/app/browser, leaves fullscreen,
   turns the camera off or connects a second screen. Reloading is caught on the
   server: the questions can only be fetched once.

   The webcam takes a still every 30 s and whenever something is flagged; face
   tracking (MediaPipe, from jsDelivr) flags no face, more than one face, and
   looking away. Flags don't lock; HR reviews them with the stills.

   A browser can't see other devices or what is outside it: this catches the
   usual ways of cheating, and the stills cover the rest. */
(function () {
  'use strict';
  var MP = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14';
  var MODEL = 'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite';
  var SNAP_EVERY = 30000, FACE_EVERY = 1500;

  function $(id) { return document.getElementById(id); }

  function init(cfg) {
    var stream = null, detector = null, test = null;
    var running = false, ended = false, lastFaces = null;
    var canFullscreen = !!(document.documentElement.requestFullscreen);
    var video = $('pcVideo');

    function showError(msg) { var e = $('pcError'); if (e) { e.textContent = msg; e.hidden = !msg; } }
    function check(id, ok) {
      var li = $(id); if (!li) return;
      li.className = ok ? 'ok' : 'bad';
      li.querySelector('i').className = ok ? 'fas fa-circle-check' : 'fas fa-circle-xmark';
    }
    function extended() { return !!(window.screen && window.screen.isExtended); }

    // ---------------- Events to the server ----------------
    function snapshotBlob() {
      return new Promise(function (resolve) {
        var v = $('pcThumbVideo');
        if (!stream || !v || !v.videoWidth) { resolve(null); return; }
        var c = document.createElement('canvas');
        c.width = 320; c.height = Math.round(320 * v.videoHeight / v.videoWidth) || 240;
        c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
        c.toBlob(function (b) { resolve(b); }, 'image/jpeg', 0.6);
      });
    }
    function send(kind, detail, withImage) {
      var fd = test ? test.formData() : new FormData();
      fd.set('csrfmiddlewaretoken', cfg.csrf);
      fd.set('kind', kind);
      fd.set('detail', detail || '');
      if (lastFaces !== null) fd.set('faces', String(lastFaces));
      var go = function (blob) {
        if (blob) fd.set('image', blob, 'snap.jpg');
        return fetch(cfg.eventUrl, { method: 'POST', body: fd, credentials: 'same-origin', keepalive: !blob || blob.size < 60000 })
          .then(function (r) { return r.json(); })
          .then(function (d) { if (d.locked || d.redirect) lockScreen(detail || kind, d.redirect); return d; })
          .catch(function () { return {}; });
      };
      return withImage === false ? go(null) : snapshotBlob().then(go);
    }

    var LABELS = {
      tab_hidden: 'You switched tab or minimised the browser.',
      window_blur: 'You switched to another window or app.',
      fullscreen_exit: 'You left fullscreen.',
      camera_off: 'Your camera was turned off.',
      second_screen: 'A second screen was connected.'
    };
    var lastStrike = 0;
    function violation(kind, detail) {
      if (!running || ended) return;
      if (test && test.state.submitting) return;   // submitting navigates away; that's fine
      // One switch fires several events (blur + hidden + fullscreen): count it once.
      if (Date.now() - lastStrike < 4000) return;
      lastStrike = Date.now();
      // Hidden tabs may not get the reply; send first, then wait for it.
      send(kind, detail || LABELS[kind] || kind, kind !== 'tab_hidden');
    }
    function lockScreen(msg, url) {
      if (ended) return;
      ended = true; running = false;
      if (test) test.stop();
      var l = $('pcLock');
      if (l) { $('pcLockMsg').textContent = LABELS[msg] || msg; l.hidden = false; }
      if (stream) stream.getTracks().forEach(function (t) { t.stop(); });
      if (document.fullscreenElement && document.exitFullscreen) document.exitFullscreen().catch(function () {});
      setTimeout(function () { window.location.href = url || cfg.resultUrl; }, 1800);
    }

    // ---------------- Camera + checks ----------------
    function startCamera() {
      showError('');
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('This browser cannot use the camera. Use Chrome on a laptop or phone.');
        return;
      }
      navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }, audio: false })
        .then(function (s) {
          stream = s;
          video.srcObject = s; $('pcThumbVideo').srcObject = s;
          $('pcCamMsg').hidden = true;
          check('pcChkCam', true);
          $('pcCamBtn').hidden = true;
          s.getVideoTracks()[0].addEventListener('ended', function () { violation('camera_off'); });
          loadFaces();
          refreshChecks();
        }, function () {
          check('pcChkCam', false);
          showError('Camera permission was refused. Allow the camera for this site (the icon in the address bar) and try again.');
        });
    }
    function refreshChecks() {
      var oneScreen = !extended();
      check('pcChkScreen', oneScreen);
      check('pcChkFull', canFullscreen);
      if ($('pcChkFull') && !canFullscreen) {
        $('pcChkFull').className = 'ok';
        $('pcChkFull').innerHTML = '<i class="fas fa-circle-info"></i> This browser has no fullscreen; leaving the page still locks the test';
      }
      var ready = !!stream && oneScreen;
      $('pcStart').hidden = !ready;
      if (stream && !oneScreen) showError('Disconnect the second screen (or set it to mirror) and the Start button will appear.');
      else showError('');
    }
    if (window.screen && 'onchange' in window.screen) {
      window.screen.addEventListener('change', function () {
        if (running && extended()) violation('second_screen');
        else if (!running && stream) refreshChecks();
      });
    }

    // ---------------- Face tracking ----------------
    function loadFaces() {
      if (detector) return;
      import(MP + '/vision_bundle.mjs').then(function (mp) {
        return mp.FilesetResolver.forVisionTasks(MP + '/wasm').then(function (fs) {
          return mp.FaceDetector.createFromOptions(fs, {
            baseOptions: { modelAssetPath: MODEL, delegate: 'CPU' }, runningMode: 'VIDEO', minDetectionConfidence: 0.5
          });
        });
      }).then(function (d) { detector = d; }, function () {
        detector = false;
        if (running) send('face_tracking_off', 'Face tracking could not load', false);
      });
    }
    var noFace = 0, many = 0, away = 0, flagged = {};
    function flagOnce(kind, detail, active) {
      if (active && !flagged[kind]) { flagged[kind] = true; send(kind, detail, true); }
      if (!active) flagged[kind] = false;
    }
    function faceTick() {
      if (!running) return;
      var v = $('pcThumbVideo');
      if (detector && v.videoWidth) {
        try {
          var dets = detector.detectForVideo(v, performance.now()).detections || [];
          lastFaces = dets.length;
          noFace = dets.length === 0 ? noFace + 1 : 0;
          many = dets.length > 1 ? many + 1 : 0;
          if (dets.length === 1) {
            var b = dets[0].boundingBox, cx = (b.originX + b.width / 2) / v.videoWidth,
                cy = (b.originY + b.height / 2) / v.videoHeight;
            away = (cx < 0.2 || cx > 0.8 || cy < 0.15 || cy > 0.85) ? away + 1 : 0;
          } else { away = 0; }
          flagOnce('no_face', 'No face for a few seconds', noFace >= 4);
          flagOnce('multiple_faces', dets.length + ' faces in view', many >= 2);
          flagOnce('looking_away', 'Face near the edge of the camera', away >= 4);
        } catch (e) { /* a bad frame; try the next one */ }
      }
      setTimeout(faceTick, FACE_EVERY);
    }

    // ---------------- Watching the page ----------------
    var blurTimer = null;
    function watch() {
      document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'hidden') violation('tab_hidden');
      });
      window.addEventListener('blur', function () {
        clearTimeout(blurTimer);
        // Give the browser a moment: some UI (the fullscreen hint, a file
        // picker) blurs briefly without the intern going anywhere.
        blurTimer = setTimeout(function () { if (!document.hasFocus()) violation('window_blur'); }, 1500);
      });
      window.addEventListener('focus', function () { clearTimeout(blurTimer); });
      document.addEventListener('fullscreenchange', function () {
        if (canFullscreen && !document.fullscreenElement) violation('fullscreen_exit');
      });
      window.addEventListener('pagehide', function () { violation('tab_hidden', 'Left or reloaded the page'); });
      var testBox = $('pcTest');
      testBox.addEventListener('paste', function (e) {
        e.preventDefault();
        send('paste_blocked', 'Paste blocked', false);
      });
      testBox.addEventListener('contextmenu', function (e) { e.preventDefault(); });
      testBox.addEventListener('copy', function (e) { if (!e.target.closest('textarea')) e.preventDefault(); });
      testBox.addEventListener('dragstart', function (e) { e.preventDefault(); });
      testBox.addEventListener('drop', function (e) { e.preventDefault(); });
      setInterval(function () { if (running) send('periodic', '', true); }, SNAP_EVERY);
      faceTick();
    }

    // ---------------- Start ----------------
    function begin() {
      var startBtn = $('pcStart');
      startBtn.disabled = true;
      // Fullscreen must be asked for inside the tap itself.
      var fs = (cfg.needsCamera && canFullscreen) ? document.documentElement.requestFullscreen({ navigationUI: 'hide' }).catch(function () {
        throw new Error('fullscreen');
      }) : Promise.resolve();
      fs.then(function () {
        var fd = new FormData();
        fd.set('csrfmiddlewaretoken', cfg.csrf);
        return fetch(cfg.beginUrl, { method: 'POST', body: fd, credentials: 'same-origin' }).then(function (r) { return r.json(); });
      }).then(function (d) {
        if (d.redirect) { window.location.href = d.redirect; return; }
        if (d.error) throw new Error(d.error);
        $('pcGate').hidden = true;
        var box = $('pcTest');
        box.innerHTML = d.html;
        box.hidden = false;
        $('pcThumb').hidden = false;
        window.scrollTo(0, 0);
        test = window.TestTake.init({ warnOnLeave: false });
        running = true;
        watch();
        send('periodic', 'Started', true);
      }).catch(function (err) {
        startBtn.disabled = false;
        if (document.fullscreenElement) document.exitFullscreen().catch(function () {});
        showError(err.message === 'fullscreen' ? 'Fullscreen was blocked. Tap Start again and allow it.'
          : (err.message || 'Could not start the test. Check your internet and try again.'));
      });
    }

    if ($('pcCamBtn')) $('pcCamBtn').addEventListener('click', startCamera);
    $('pcStart').addEventListener('click', begin);
    if (cfg.needsCamera) {
      check('pcChkScreen', !extended());
      check('pcChkFull', canFullscreen);
    }
  }

  window.Proctor = { init: init };
})();
