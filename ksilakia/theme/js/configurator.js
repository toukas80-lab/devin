(function () {
  var form = document.getElementById('ksilakia-configurator');
  if (!form) return;

  var full = document.getElementById('cfg-canvas-full');
  var zoom = document.getElementById('cfg-canvas-zoom');
  var cropCanvas = document.getElementById('cfg-crop-canvas');
  var dimLabel = document.getElementById('cfg-dim-label');
  var msg = form.querySelector('.form-msg');
  var fileInput = form.querySelector('[name="logo_file"]');
  var BURN = [92, 56, 22];
  var FONTS = {
    sans: 'bold 10px "Segoe UI", Arial, Helvetica, sans-serif',
    serif: 'bold 10px Georgia, "Times New Roman", serif',
    mono: 'bold 10px "Courier New", monospace',
    black: '900 10px Impact, "Arial Black", sans-serif'
  };
  var source = null;   // uploaded image (Image)
  var stamp = null;    // processed burn image (canvas)

  function val(name) { return form.querySelector('[name="' + name + '"]'); }
  function num(name, def) {
    var v = parseFloat(val(name).value);
    return isFinite(v) ? v : def;
  }
  function state() {
    var type = form.querySelector('[name="stick_type"]:checked').value;
    var s = {
      type: type,
      length: Math.min(MAX_LEN, Math.max(80, num('length', 215))),
      diameter: Math.min(5, Math.max(2, num('diameter', 4))),
      paddleWidth: PADDLE_W,
      paddleLength: PADDLE_L,
      point: val('point').value,
      mode: form.querySelector('[name="logo_mode"]:checked').value,
      text: val('logo_text').value.trim(),
      font: val('logo_font').value,
      pallets: Math.max(1, Math.round(num('pallets', 1)))
    };
    if (type === 'round') s.paddleLength = 0;
    return s;
  }

  // ---- stick geometry (mm; x=0 at handle end, tip at x=length, y centered) ----
  // VN configurator geometry: point length 10 mm; "Blunt point" is a truncated cone ending in a Ø1.6 mm flat.
  var TIP_LEN = 10, BLUNT_DIA = 1.6, MAX_LEN = 300, PADDLE_W = 10, PADDLE_L = 40;
  function tipLength(s) { return Math.min(TIP_LEN, s.length / 3); }
  function tipRadius(s) { return s.point === 'sharp' ? 0 : Math.min(BLUNT_DIA, s.diameter * 0.8) / 2; }
  function tipPath(ctx, s, k, ox, oy) {
    var L = s.length, tl = tipLength(s), tr = tipRadius(s);
    ctx.lineTo(ox + L * k, oy - tr * k);
    ctx.lineTo(ox + L * k, oy + tr * k);
  }
  function outline(ctx, s, k, ox, oy) {
    var L = s.length, d = s.diameter, r = d / 2, tl = tipLength(s);
    ctx.beginPath();
    if (s.type === 'paddle') {
      var pw = s.paddleWidth / 2, pl = s.paddleLength, c = Math.min(pw, 3);
      // Concave (inner) fillet paddle -> shaft: arc centre sits outside the wood at (pl+R, ±(r+R)).
      var R = Math.max(0.5, Math.min(pw - r, 8));
      ctx.moveTo(ox + c * k, oy - pw * k);
      ctx.lineTo(ox + pl * k, oy - pw * k);
      ctx.lineTo(ox + pl * k, oy - (r + R) * k);
      ctx.arc(ox + (pl + R) * k, oy - (r + R) * k, R * k, Math.PI, Math.PI / 2, true);
      ctx.lineTo(ox + (L - tl) * k, oy - r * k);
      tipPath(ctx, s, k, ox, oy);
      ctx.lineTo(ox + (L - tl) * k, oy + r * k);
      ctx.lineTo(ox + (pl + R) * k, oy + r * k);
      ctx.arc(ox + (pl + R) * k, oy + (r + R) * k, R * k, Math.PI * 1.5, Math.PI, true);
      ctx.lineTo(ox + pl * k, oy + pw * k);
      ctx.lineTo(ox + c * k, oy + pw * k);
      ctx.quadraticCurveTo(ox, oy + pw * k, ox, oy + (pw - c) * k);
      ctx.lineTo(ox, oy - (pw - c) * k);
      ctx.quadraticCurveTo(ox, oy - pw * k, ox + c * k, oy - pw * k);
    } else {
      ctx.moveTo(ox, oy - r * k);
      ctx.lineTo(ox + (L - tl) * k, oy - r * k);
      tipPath(ctx, s, k, ox, oy);
      ctx.lineTo(ox + (L - tl) * k, oy + r * k);
      ctx.lineTo(ox, oy + r * k);
    }
    ctx.closePath();
  }
  function paintWood(ctx, s, k, ox, oy) {
    var h = (s.type === 'paddle' ? s.paddleWidth : s.diameter) * k;
    var g = ctx.createLinearGradient(0, oy - h / 2, 0, oy + h / 2);
    g.addColorStop(0, '#e3c58f'); g.addColorStop(0.35, '#f1dcb0'); g.addColorStop(0.7, '#dcb97f'); g.addColorStop(1, '#c69c5f');
    ctx.save();
    outline(ctx, s, k, ox, oy);
    ctx.fillStyle = g; ctx.fill();
    ctx.clip();
    ctx.strokeStyle = 'rgba(120,80,35,.12)'; ctx.lineWidth = Math.max(1, k * 0.15);
    for (var i = 0; i < 9; i++) {
      var y = oy - h / 2 + h * ((i + 0.5) / 9) + Math.sin(i * 1.7) * k * 0.2;
      ctx.beginPath(); ctx.moveTo(ox, y); ctx.lineTo(ox + s.length * k, y + Math.cos(i) * k * 0.3); ctx.stroke();
    }
    ctx.restore();
    ctx.save();
    outline(ctx, s, k, ox, oy);
    ctx.strokeStyle = 'rgba(90,60,25,.45)'; ctx.lineWidth = Math.max(1, k * 0.08); ctx.stroke();
    ctx.restore();
  }

  // Branding zone (mm): x range and max height where the logo may sit.
  function zone(s) {
    if (s.type === 'paddle') return { x0: 1.5, x1: s.paddleLength - 1, h: s.paddleWidth * 0.85 };
    return { x0: 10, x1: s.length - tipLength(s) - 10, h: s.diameter * 0.8 };
  }
  // Logo box in mm: {x, y, w, h}
  function logoBox(s) {
    var z = zone(s), h = z.h * 0.8, w;
    if (s.mode === 'image' && stamp) w = h * stamp.width / stamp.height;
    else if (s.mode === 'text' && s.text) w = measureText(s, h);
    else return null;
    var maxW = z.x1 - z.x0;
    if (w > maxW) { h *= maxW / w; w = maxW; }
    var x = s.type === 'paddle' ? z.x0 + (maxW - w) / 2 : z.x0; // paddle: centered on the flat end; round: fixed near the base
    return { x: x, y: -h / 2, w: w, h: h };
  }
  var mctx = document.createElement('canvas').getContext('2d');
  function fontFor(s, px) { return FONTS[s.font].replace('10px', px + 'px'); }
  function measureText(s, h) {
    mctx.font = fontFor(s, 100);
    return mctx.measureText(s.text).width / 100 * h / 0.78;
  }
  function paintLogo(ctx, s, k, ox, oy) {
    var b = logoBox(s);
    if (!b) return;
    ctx.save();
    var cx = ox + (b.x + b.w / 2) * k, cy = oy;
    ctx.translate(cx, cy);
    ctx.globalAlpha = 0.92;
    if (s.mode === 'image' && stamp) {
      ctx.drawImage(stamp, -b.w * k / 2, -b.h * k / 2, b.w * k, b.h * k);
    } else {
      var px = b.h * k / 0.78;
      ctx.font = fontFor(s, px);
      ctx.fillStyle = 'rgb(' + BURN.join(',') + ')';
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.shadowColor = 'rgba(60,30,5,.5)'; ctx.shadowBlur = k * 0.15;
      ctx.fillText(s.text, 0, px * 0.04);
    }
    ctx.restore();
  }

  function paintBackground(ctx, w, h) {
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#f7f1e6'; ctx.fillRect(0, 0, w, h);
  }
  function drawFull(s) {
    var ctx = full.getContext('2d'), W = full.width, H = full.height;
    paintBackground(ctx, W, H);
    var k = (W - 80) / MAX_LEN, ox = 40, oy = H / 2;
    paintWood(ctx, s, k, ox, oy);
    paintLogo(ctx, s, k, ox, oy);
    // dimension line
    ctx.strokeStyle = '#8a7358'; ctx.fillStyle = '#5c4a35'; ctx.lineWidth = 1;
    var y = oy + Math.max(s.diameter, s.type === 'paddle' ? s.paddleWidth : 0) * k / 2 + 34;
    ctx.beginPath(); ctx.moveTo(ox, y); ctx.lineTo(ox + s.length * k, y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ox, y - 6); ctx.lineTo(ox, y + 6); ctx.moveTo(ox + s.length * k, y - 6); ctx.lineTo(ox + s.length * k, y + 6); ctx.stroke();
    ctx.font = '600 24px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    ctx.fillText(s.length + ' mm', ox + s.length * k / 2, y - 4);
  }
  function drawZoom(s) {
    var ctx = zoom.getContext('2d'), W = zoom.width, H = zoom.height;
    paintBackground(ctx, W, H);
    var b = logoBox(s), z = zone(s);
    var winMm = Math.max(b ? b.w + 16 : 40, s.type === 'paddle' ? s.paddleLength + 16 : 40);
    var k = Math.min((W - 60) / winMm, (H - 60) / Math.max(s.type === 'paddle' ? s.paddleWidth : s.diameter, 1) / 1.3);
    var center = b ? b.x + b.w / 2 : (z.x0 + z.x1) / 2;
    var ox = W / 2 - center * k, oy = H / 2;
    paintWood(ctx, s, k, ox, oy);
    paintLogo(ctx, s, k, ox, oy);
    ctx.fillStyle = '#5c4a35'; ctx.font = '600 24px system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    var label = b ? 'Λογότυπο ≈ ' + b.w.toFixed(1) + ' × ' + b.h.toFixed(1) + ' mm' : (s.mode === 'none' ? 'Χωρίς λογότυπο' : 'Γράψτε κείμενο ή ανεβάστε λογότυπο');
    ctx.fillText(label, 16, 14);
  }
  function render() {
    var s = state();
    form.querySelector('.cfg-mode-none').hidden = s.mode !== 'none';
    form.querySelector('.cfg-mode-text').hidden = s.mode !== 'text';
    form.querySelector('.cfg-mode-image').hidden = s.mode !== 'image';
    dimLabel.textContent = s.length + ' × ' + s.diameter + ' mm' + (s.type === 'paddle' ? ', κουπί ' + s.paddleLength + ' × ' + s.paddleWidth + ' mm' : '');
    drawFull(s);
    drawZoom(s);
  }

  // ---- image upload, crop and "burn" conversion ----
  function cropRect() {
    var l = num('crop_left', 0) / 100, r = num('crop_right', 0) / 100, t = num('crop_top', 0) / 100, b = num('crop_bottom', 0) / 100;
    var w = source.naturalWidth, h = source.naturalHeight;
    var x0 = Math.round(w * l), x1 = Math.max(x0 + 4, Math.round(w * (1 - r)));
    var y0 = Math.round(h * t), y1 = Math.max(y0 + 4, Math.round(h * (1 - b)));
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  }
  function drawCrop() {
    var ctx = cropCanvas.getContext('2d'), W = cropCanvas.width, H = cropCanvas.height;
    ctx.clearRect(0, 0, W, H);
    if (!source) return;
    var k = Math.min(W / source.naturalWidth, H / source.naturalHeight);
    var w = source.naturalWidth * k, h = source.naturalHeight * k, ox = (W - w) / 2, oy = (H - h) / 2;
    ctx.drawImage(source, ox, oy, w, h);
    var c = cropRect();
    ctx.fillStyle = 'rgba(0,0,0,.55)';
    ctx.fillRect(ox, oy, w, c.y * k);
    ctx.fillRect(ox, oy + (c.y + c.h) * k, w, h - (c.y + c.h) * k);
    ctx.fillRect(ox, oy + c.y * k, c.x * k, c.h * k);
    ctx.fillRect(ox + (c.x + c.w) * k, oy + c.y * k, w - (c.x + c.w) * k, c.h * k);
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(ox + c.x * k, oy + c.y * k, c.w * k, c.h * k);
  }
  function buildStamp() {
    if (!source) { stamp = null; return; }
    var c = cropRect(), max = 900, k = Math.min(1, max / Math.max(c.w, c.h));
    var cv = document.createElement('canvas');
    cv.width = Math.max(1, Math.round(c.w * k)); cv.height = Math.max(1, Math.round(c.h * k));
    var ctx = cv.getContext('2d');
    ctx.drawImage(source, c.x, c.y, c.w, c.h, 0, 0, cv.width, cv.height);
    var img = ctx.getImageData(0, 0, cv.width, cv.height), d = img.data;
    var burn = num('burn', 60) / 100, lo = 255 - 200 * burn, hi = Math.min(250, lo + 90);
    for (var i = 0; i < d.length; i += 4) {
      var lum = 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
      var a = (hi - lum) / (hi - lo);
      a = a < 0 ? 0 : a > 1 ? 1 : a;
      d[i] = BURN[0]; d[i + 1] = BURN[1]; d[i + 2] = BURN[2]; d[i + 3] = Math.round(d[i + 3] * a);
    }
    ctx.putImageData(img, 0, 0);
    stamp = cv;
  }
  fileInput.addEventListener('change', function () {
    var f = fileInput.files[0];
    source = null; stamp = null;
    form.querySelector('.cfg-crop').hidden = true;
    if (!f) { render(); return; }
    if (!/^image\/(png|jpeg|webp)$/.test(f.type) || f.size > 8 * 1024 * 1024) {
      setMsg('err', 'Δεκτά μόνο PNG/JPG/WebP έως 8 MB.');
      fileInput.value = '';
      render();
      return;
    }
    setMsg('', '');
    var img = new Image();
    img.onload = function () {
      source = img;
      ['crop_left', 'crop_right', 'crop_top', 'crop_bottom'].forEach(function (n) { val(n).value = 0; });
      form.querySelector('.cfg-crop').hidden = false;
      drawCrop(); buildStamp(); render();
      URL.revokeObjectURL(img.src);
    };
    img.onerror = function () { setMsg('err', 'Η εικόνα δεν μπόρεσε να διαβαστεί.'); };
    img.src = URL.createObjectURL(f);
  });

  form.addEventListener('input', function (e) {
    if (/^(crop_|burn)/.test(e.target.name)) { drawCrop(); buildStamp(); }
    render();
  });
  form.addEventListener('change', render);

  // ---- submit ----
  function setMsg(cls, text) { msg.className = 'form-msg' + (cls ? ' ' + cls : ''); msg.textContent = text; }
  function exportPreview() {
    var cv = document.createElement('canvas');
    cv.width = full.width; cv.height = full.height + zoom.height + 10;
    var ctx = cv.getContext('2d');
    ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.drawImage(full, 0, 0);
    ctx.drawImage(zoom, 0, full.height + 10);
    return new Promise(function (res) { cv.toBlob(res, 'image/png'); });
  }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var s = state();
    form.querySelectorAll('.cfg-invalid').forEach(function (el) { el.classList.remove('cfg-invalid'); });
    var missing = [];
    ['name', 'phone', 'email'].forEach(function (n) { if (!val(n).value.trim()) missing.push(val(n)); });
    if (val('email').value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(val('email').value)) missing.push(val('email'));
    if (s.mode === 'text' && !s.text) missing.push(val('logo_text'));
    if (s.mode === 'image' && !stamp) missing.push(fileInput);
    if (s.pallets < 1) missing.push(val('pallets'));
    if (missing.length) {
      missing.forEach(function (el) { el.closest('label').classList.add('cfg-invalid'); });
      setMsg('err', 'Συμπληρώστε τα υποχρεωτικά πεδία με αστερίσκο.');
      missing[0].focus();
      return;
    }
    var btn = form.querySelector('button[type="submit"]');
    btn.disabled = true;
    setMsg('', 'Αποστολή...');
    render();
    exportPreview().then(function (blob) {
      var fd = new FormData(form);
      fd.delete('logo_file');
      if (s.mode === 'image' && fileInput.files[0]) fd.append('logo_file', fileInput.files[0]);
      fd.append('preview', blob, 'preview.png');
      fd.append('config', JSON.stringify(s));
      fd.append('action', 'ksilakia_custom_quote');
      fd.append('nonce', ksilakia.quote_nonce);
      return fetch(ksilakia.ajax, { method: 'POST', body: fd, credentials: 'same-origin' });
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        btn.disabled = false;
        if (d.ok) {
          setMsg('ok', 'Λάβαμε το αίτημά σας (αρ. ' + d.id + '). Θα σας στείλουμε προσφορά στο ' + val('email').value + '.');
          form.querySelector('.cfg-contact').scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
          setMsg('err', d.error || 'Κάτι πήγε στραβά.');
        }
      })
      .catch(function () {
        btn.disabled = false;
        setMsg('err', 'Δεν έγινε αποστολή. Καλέστε μας ή στείλτε το λογότυπο με email.');
      });
  });

  if (document.fonts && document.fonts.ready) document.fonts.ready.then(render);
  render();
})();
