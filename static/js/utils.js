(function(){
  const TOAST_DEFAULT_DURATION_MS = 2200;
  const TOAST_MIN_DURATION_MS = 1200;
  const TOAST_FADE_DURATION_MS = 180;
  const TOAST_REMOVE_DELAY_MS = 200;

  if (!window.getCookie) {
    window.getCookie = function(name) {
      if (!document.cookie) return null;
      for (const value of document.cookie.split(";")) {
        const cookie = value.trim();
        if (cookie.startsWith(name + "=")) {
          return decodeURIComponent(cookie.substring(name.length + 1));
        }
      }
      return null;
    }
  }
  if (!window.toast) {
    function ensureContainer() {
      let c = document.getElementById('tf-toast-container');
      if (c) return c;
      c = document.createElement('div');
      c.id = 'tf-toast-container';
      c.style.position = 'fixed';
      c.style.left = '50%';
      c.style.top = '50%';
      c.style.transform = 'translate(-50%, -50%)';
      c.style.display = 'flex';
      c.style.flexDirection = 'column';
      c.style.alignItems = 'center';
      c.style.gap = '8px';
      c.style.zIndex = '2147483647';
      document.body.appendChild(c);
      return c;
    }

    window.toast = function(message, opts = {}) {
      const { type = 'info', duration = TOAST_DEFAULT_DURATION_MS } = opts;
      const container = ensureContainer();

      const el = document.createElement('div');
      el.textContent = message;
      el.style.maxWidth = '90vw';
      el.style.background = type === 'error' ? 'rgba(220, 38, 38, 0.95)' : 'rgba(17,17,17,0.92)';
      el.style.color = '#fff';
      el.style.padding = '12px 16px';
      el.style.borderRadius = '8px';
      el.style.boxShadow = '0 6px 20px rgba(0,0,0,0.25)';
      el.style.fontSize = '14px';
      el.style.lineHeight = '1.35';
      el.style.wordBreak = 'break-all';
      el.style.textAlign = 'center';
      el.style.opacity = '0';
      el.style.transition = `opacity ${TOAST_FADE_DURATION_MS}ms ease`;

      container.appendChild(el);
      requestAnimationFrame(() => { el.style.opacity = '1'; });

      setTimeout(() => {
        el.style.opacity = '0';
        setTimeout(() => {
          el.remove();
        }, TOAST_REMOVE_DELAY_MS);
      }, Math.max(TOAST_MIN_DURATION_MS, duration));
    }
  }
})();
