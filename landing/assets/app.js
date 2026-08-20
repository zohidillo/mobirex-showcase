// ============================================
// Mobirex — App-wide behavior
// i18n, lang toggle, mobile menu, form validation,
// reveal-on-scroll, legal TOC scrollspy
// ============================================

(function () {
  const STORAGE_KEY = 'mobirex.lang';
  const DEFAULT_LANG = 'uz';
  const SUPPORTED = ['uz', 'ru', 'en'];

  // ---------- i18n ----------
  function getLang() {
    // URL ?lang= takes precedence so hreflang URLs deep-link directly to a language.
    try {
      const urlLang = new URLSearchParams(window.location.search).get('lang');
      if (urlLang && SUPPORTED.includes(urlLang)) {
        localStorage.setItem(STORAGE_KEY, urlLang);
        return urlLang;
      }
    } catch (_) {}
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && SUPPORTED.includes(stored)) return stored;
    const nav = (navigator.language || 'uz').toLowerCase().slice(0, 2);
    return SUPPORTED.includes(nav) ? nav : DEFAULT_LANG;
  }

  function applyLang(lang) {
    const dict = (window.MOBIREX_I18N || {})[lang] || {};
    document.documentElement.setAttribute('lang', lang);
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const key = el.getAttribute('data-i18n');
      if (dict[key] != null) el.textContent = dict[key];
    });
    document.querySelectorAll('[data-i18n-attr]').forEach((el) => {
      // format: "attr:key, attr2:key2"
      const spec = el.getAttribute('data-i18n-attr');
      spec.split(',').forEach((pair) => {
        const [attr, key] = pair.trim().split(':');
        if (attr && key && dict[key] != null) el.setAttribute(attr, dict[key]);
      });
    });
    // Update toggle pressed state
    document.querySelectorAll('.lang-switch button').forEach((b) => {
      b.setAttribute('aria-pressed', b.dataset.lang === lang ? 'true' : 'false');
    });
    // Update document title if a key is set
    const titleKey = document.body.getAttribute('data-title-key');
    if (titleKey && dict[titleKey]) {
      document.title = 'Mobirex — ' + dict[titleKey];
    }
  }

  function initLangSwitch() {
    const groups = document.querySelectorAll('.lang-switch');
    groups.forEach((group) => {
      group.addEventListener('click', (e) => {
        const btn = e.target.closest('button[data-lang]');
        if (!btn) return;
        const lang = btn.dataset.lang;
        if (!SUPPORTED.includes(lang)) return;
        localStorage.setItem(STORAGE_KEY, lang);
        applyLang(lang);
      });
    });
  }

  // ---------- Mobile menu ----------
  function initMobileMenu() {
    const toggle = document.querySelector('.menu-toggle');
    const menu = document.querySelector('.mobile-nav');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', () => {
      const open = menu.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    });
    menu.addEventListener('click', (e) => {
      if (e.target.tagName === 'A') {
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      }
    });
  }

  // ---------- Form validation ----------
  function validateField(field) {
    const input = field.querySelector('input, textarea');
    if (!input) return true;
    const required = input.required || field.hasAttribute('data-required');
    const value = (input.value || '').trim();
    let valid = true;
    let errKey = '';

    if (required && !value) {
      valid = false;
      errKey = 'form.err.required';
    } else if (value && input.type === 'email') {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        valid = false; errKey = 'form.err.email';
      }
    } else if (value && input.type === 'tel') {
      if (!/^[+0-9\s\-()]{7,}$/.test(value)) {
        valid = false; errKey = 'form.err.phone';
      }
    }

    field.classList.toggle('has-error', !valid);
    const errEl = field.querySelector('.error-msg');
    if (errEl) {
      const dict = (window.MOBIREX_I18N || {})[getLang()] || {};
      errEl.textContent = errKey ? (dict[errKey] || 'Invalid') : '';
    }
    return valid;
  }

  function normalizePhone(value) {
    return value.replace(/[\s\-\(\)]/g, '');
  }

  function buildMessage(form) {
    let msg = (form.message && form.message.value) ? form.message.value.trim() : '';
    const email = form.email && form.email.value ? form.email.value.trim() : '';
    if (email) msg += (msg ? '\n\n' : '') + 'Email: ' + email;
    if (form.reason && form.reason.value && form.reason.value.trim()) {
      msg = 'Sabab: ' + form.reason.value.trim() + (msg ? '\n\n' + msg : '');
    }
    return msg;
  }

  function showFormError(form, err) {
    const dict = (window.MOBIREX_I18N || {})[getLang()] || {};
    const message = navigator.onLine === false
      ? (dict['form.err.offline'] || "Internet aloqasi yo'q. Qayta urinib ko'ring.")
      : (dict['form.err.server'] || "Yuborishda xatolik. Iltimos, keyinroq urinib ko'ring yoki Telegram orqali bogʻlaning.");

    let errorEl = form.querySelector('.error-banner');
    if (!errorEl) {
      errorEl = document.createElement('div');
      errorEl.className = 'error-banner';
      form.prepend(errorEl);
    }
    errorEl.textContent = message;
    errorEl.classList.add('is-shown');
    setTimeout(() => errorEl.classList.remove('is-shown'), 5000);
  }

  function initForms() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach((form) => {
      // Live clear errors as user types
      form.querySelectorAll('.field input, .field textarea').forEach((inp) => {
        inp.addEventListener('input', () => {
          const field = inp.closest('.field');
          if (field && field.classList.contains('has-error')) {
            validateField(field);
          }
        });
        inp.addEventListener('blur', () => {
          const field = inp.closest('.field');
          if (field && (inp.value || '').trim()) validateField(field);
        });
      });

      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        let ok = true;
        form.querySelectorAll('.field').forEach((f) => {
          if (!validateField(f)) ok = false;
        });
        if (!ok) {
          const firstErr = form.querySelector('.field.has-error input, .field.has-error textarea');
          if (firstErr) firstErr.focus();
          return;
        }

        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.style.opacity = '0.7';
        }

        try {
          const platform = form.platform ? form.platform.value : '';
          let requestType = form.dataset.requestType || 'CONTACT';

          const formData = {
            request_type: requestType,
            source: 'LANDING_SITE',
            full_name: ((form.first ? form.first.value.trim() : '') + ' ' + (form.last ? form.last.value.trim() : '')).trim(),
            phone: normalizePhone(form.phone ? form.phone.value : ''),
            message: buildMessage(form),
          };

          const cfg = window.MOBIREX_CONFIG || {};
          const response = await fetch(
            (cfg.API_BASE || '') + '/api/support/requests/',
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Key': cfg.SUPPORT_X_KEY || '',
              },
              body: JSON.stringify(formData),
            }
          );

          if (!response.ok) throw new Error('Server ' + response.status);

          const banner = form.querySelector('.success-banner') ||
                         form.parentElement.querySelector('.success-banner');
          if (banner) {
            banner.classList.add('is-shown');
            banner.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            setTimeout(() => banner.classList.remove('is-shown'), 5000);
          }
          form.reset();
        } catch (err) {
          showFormError(form, err);
        } finally {
          if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.style.opacity = '';
          }
        }
      });
    });
  }

  // ---------- Reveal on scroll ----------
  function initReveal() {
    if (!('IntersectionObserver' in window)) {
      document.querySelectorAll('.reveal').forEach((el) => el.classList.add('is-visible'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el));
  }

  // ---------- Legal TOC scroll spy ----------
  function initTocSpy() {
    const toc = document.querySelector('.legal-toc');
    if (!toc) return;
    const sections = [...document.querySelectorAll('.legal-content section[id]')];
    if (!sections.length) return;
    const links = new Map();
    toc.querySelectorAll('a[href^="#"]').forEach((a) => {
      const id = a.getAttribute('href').slice(1);
      links.set(id, a);
    });

    const io = new IntersectionObserver((entries) => {
      // pick first that is intersecting most
      const visible = entries.filter((e) => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
      if (visible[0]) {
        const id = visible[0].target.id;
        toc.querySelectorAll('a').forEach((a) => a.classList.remove('is-active'));
        const link = links.get(id);
        if (link) link.classList.add('is-active');
      }
    }, { rootMargin: '-30% 0px -55% 0px', threshold: [0, 0.5, 1] });
    sections.forEach((s) => io.observe(s));

    // Smooth scroll
    toc.addEventListener('click', (e) => {
      const a = e.target.closest('a[href^="#"]');
      if (!a) return;
      const id = a.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        history.replaceState(null, '', '#' + id);
      }
    });
  }

  // ---------- Active nav link ----------
  function markActiveNav() {
    const path = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-primary a, .mobile-nav a').forEach((a) => {
      const href = (a.getAttribute('href') || '').split('#')[0];
      if (href === path) a.classList.add('is-active');
    });
  }

  // ---------- Init ----------
  function init() {
    initLangSwitch();
    initMobileMenu();
    initForms();
    initReveal();
    initTocSpy();
    markActiveNav();
    applyLang(getLang());
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
