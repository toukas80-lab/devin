(function () {
  var t = document.querySelector('.menu-toggle'), n = document.querySelector('.site-header nav');
  if (t && n) {
    t.addEventListener('click', function () {
      var open = n.classList.toggle('open');
      t.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  var f = document.getElementById('ksilakia-contact');
  if (f) {
    var m = f.querySelector('.form-msg');
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      m.className = 'form-msg';
      m.textContent = 'Αποστολή...';
      var fd = new FormData(f);
      fd.append('action', 'ksilakia_contact');
      fd.append('nonce', ksilakia.nonce);
      fetch(ksilakia.ajax, { method: 'POST', body: fd, credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          m.className = 'form-msg ' + (d.ok ? 'ok' : 'err');
          m.textContent = d.ok ? 'Ευχαριστούμε! Θα επικοινωνήσουμε σύντομα.' : (d.error || 'Κάτι πήγε στραβά.');
          if (d.ok) f.reset();
        })
        .catch(function () {
          m.className = 'form-msg err';
          m.textContent = 'Δεν έγινε αποστολή. Καλέστε μας ή στείλτε WhatsApp.';
        });
    });
  }

  // ΑΦΜ lookup (VIES/ΑΑΔΕ) → autofill company fields. Works on registration + checkout.
  function byName(name) {
    return document.getElementById(name) || document.querySelector('[name="' + name + '"]');
  }
  function initAfm(input) {
    if (input.dataset.afmInit) return;
    input.dataset.afmInit = '1';
    var status = input.parentNode.parentNode.querySelector('.afm-status');
    if (!status) {
      status = document.createElement('span');
      status.className = 'afm-status';
      status.setAttribute('aria-live', 'polite');
      input.closest('p, .form-row').appendChild(status);
    }
    var map = {};
    (input.dataset.afmMap || '').split(',').forEach(function (pair) {
      var kv = pair.split(':');
      if (kv[1]) map[kv[0]] = kv[1];
    });
    var timer, last = '';
    function fill(key, val) {
      var f = map[key] && byName(map[key]);
      if (f && val && !f.value) {
        f.value = val;
        f.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
    input.addEventListener('input', function () {
      var afm = input.value.replace(/\D/g, '');
      if (afm !== input.value) input.value = afm;
      clearTimeout(timer);
      if (afm.length !== 9) { status.textContent = ''; status.className = 'afm-status'; return; }
      if (afm === last) return;
      status.textContent = 'Αναζήτηση στοιχείων…';
      status.className = 'afm-status loading';
      timer = setTimeout(function () {
        last = afm;
        var fd = new FormData();
        fd.append('action', 'ksilakia_afm');
        fd.append('nonce', ksilakia.afm_nonce);
        fd.append('afm', afm);
        fetch(ksilakia.ajax, { method: 'POST', body: fd, credentials: 'same-origin' })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (res.success && res.data) {
              var d = res.data;
              fill('name', d.name); fill('doy', d.doy); fill('activity', d.activity);
              fill('address', d.address); fill('postcode', d.postcode); fill('city', d.city);
              status.textContent = '✓ Βρέθηκε (' + d.source + ')' + (d.doy ? '' : ' — συμπληρώστε ΔΟΥ');
              status.className = 'afm-status ok';
              if (window.jQuery) jQuery(document.body).trigger('update_checkout');
            } else {
              status.textContent = (res.data && res.data.msg) || 'Δεν βρέθηκε';
              status.className = 'afm-status err';
            }
          })
          .catch(function () {
            status.textContent = 'Σφάλμα σύνδεσης — συμπληρώστε χειροκίνητα.';
            status.className = 'afm-status err';
          });
      }, 400);
    });
  }
  function initAfmAll() {
    document.querySelectorAll('[data-afm-lookup]').forEach(initAfm);
  }

  // Checkout: Απόδειξη / Τιμολόγιο toggle.
  function toggleInvoice() {
    var sel = document.querySelector('input[name="billing_invoice_type"]:checked');
    if (!sel) return;
    var inv = sel.value === 'invoice';
    document.querySelectorAll('.invoice-field').forEach(function (row) {
      row.style.display = inv ? '' : 'none';
      var required = inv && row.id !== 'billing_activity_field';
      row.classList.toggle('validate-required', required);
      var input = row.querySelector('input');
      if (input) {
        input.required = required;
        input.setAttribute('aria-required', required ? 'true' : 'false');
      }
      var lab = row.querySelector('label');
      if (!lab) return;
      var optional = lab.querySelector('.optional');
      if (optional) optional.hidden = required;
      var marker = lab.querySelector('.required');
      if (required && !marker) {
        lab.insertAdjacentHTML('beforeend', ' <abbr class="required" title="απαιτείται">*</abbr>');
      } else if (!required && marker) {
        marker.remove();
      }
    });
  }
  function initCheckout() {
    initAfmAll();
    toggleInvoice();
    document.querySelectorAll('input[name="billing_invoice_type"]').forEach(function (r) {
      if (!r.dataset.init) { r.dataset.init = '1'; r.addEventListener('change', toggleInvoice); }
    });
  }
  initCheckout();
  if (window.jQuery) {
    jQuery(document.body).on('updated_checkout country_to_state_changed', initCheckout);
  }

  var registration = document.querySelector('form.woocommerce-form-register');
  if (registration) {
    var b2b = registration.querySelector('input[name="ksilakia_b2b"]');
    var fields = registration.querySelectorAll('input[required], input[data-b2b-required]');
    var submitted = registration.querySelector('.b2b-fields').dataset.registrationSubmitted === 'true';

    function validateField(field) {
      var invalid = field.required && !field.validity.valid;
      var row = field.closest('.form-row');
      var error = row.querySelector('.registration-field-error');
      row.classList.toggle('registration-invalid', invalid);
      if (invalid) {
        field.setAttribute('aria-invalid', 'true');
        error.textContent = field.validity.valueMissing
          ? 'Συμπληρώστε αυτό το υποχρεωτικό πεδίο.'
          : (field.type === 'email' ? 'Συμπληρώστε μια έγκυρη διεύθυνση email.' : field.validationMessage);
      } else {
        field.removeAttribute('aria-invalid');
        error.textContent = '';
      }
      error.hidden = !invalid;
    }

    fields.forEach(function (field) {
      var error = document.createElement('small');
      error.id = (field.id || field.name) + '-error';
      error.className = 'registration-field-error';
      error.hidden = true;
      error.setAttribute('aria-live', 'polite');
      field.closest('.form-row').appendChild(error);
      field.setAttribute('aria-describedby', ((field.getAttribute('aria-describedby') || '') + ' ' + error.id).trim());
      field.addEventListener('blur', function () { validateField(field); });
      ['input', 'change'].forEach(function (event) {
        field.addEventListener(event, function () {
          if (submitted || field.hasAttribute('aria-invalid')) validateField(field);
        });
      });
    });

    function toggleB2bRequired() {
      registration.querySelectorAll('[data-b2b-required]').forEach(function (field) {
        field.required = b2b.checked;
        field.setAttribute('aria-required', b2b.checked ? 'true' : 'false');
        field.closest('label').querySelector('.required').hidden = !b2b.checked;
        if (!b2b.checked || submitted) validateField(field);
      });
    }

    b2b.addEventListener('change', toggleB2bRequired);
    toggleB2bRequired();
    registration.addEventListener('invalid', function (event) {
      submitted = true;
      if (event.target.matches('input[required]')) validateField(event.target);
    }, true);
    if (submitted) fields.forEach(validateField);
    if (b2b.checked && !submitted) registration.scrollIntoView();
  }
})();
