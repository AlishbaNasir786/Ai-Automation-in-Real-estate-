/**
 * user_auth_banner.js — Dynamic User Auth & Persona Banner Component
 * Handles login, registration, Google OAuth modal, persona onboarding interstitial,
 * and top-of-page personalized banner injection on every route.
 */

document.addEventListener('DOMContentLoaded', () => {
  initAuthAndBanner();
});

let currentUser = null;

async function initAuthAndBanner() {
  injectAuthStyles();
  injectAuthModal();
  injectPersonaModal();

  try {
    const res = await fetch('/api/auth/me');
    const data = await res.json();

    if (data.authenticated && data.user) {
      currentUser = data.user;
      renderUserHeaderBadge(true);

      if (!currentUser.segment) {
        openPersonaModal(true); // Forced onboarding interstitial
      } else {
        loadPersonalizedBanner();
      }
    } else {
      renderUserHeaderBadge(false);
      loadPersonalizedBanner();
      // Always open login modal first on initial unauthenticated visit
      openAuthModal('login');
    }
  } catch (err) {
    console.error('Error initializing auth:', err);
  }
}

/* ── RENDER HEADER USER BADGE & ROLE NAV PROTECTION ───────────── */
function renderUserHeaderBadge(isLoggedIn) {
  let nav = document.querySelector('.top-nav');
  if (!nav) return;

  // Enforce Admin-Only Nav Links:
  // - Admins: show all nav links
  // - Clients/guests: fully HIDE admin-only links (not just CSS hidden)
  const isAdmin = isLoggedIn && currentUser && currentUser.role === 'admin';
  nav.querySelectorAll('[data-admin-only]').forEach(link => {
    if (isAdmin) {
      link.style.display = '';
      link.removeAttribute('aria-hidden');
      link.removeAttribute('tabindex');
    } else {
      link.style.display = 'none';
      link.setAttribute('aria-hidden', 'true');
      link.setAttribute('tabindex', '-1');
    }
  });

  // Show access-denied toast if redirected from a protected page
  const params = new URLSearchParams(window.location.search);
  if (params.get('access') === 'denied') {
    const reason = params.get('reason');
    const msg = reason === 'login'
      ? '🔒 Please sign in to access that page.'
      : '🚫 That section is only available to Admins.';
    _showAccessToast(msg);
    // Clean URL without reload
    window.history.replaceState({}, '', window.location.pathname);
  }

  let existing = document.getElementById('userAuthBadge');
  if (existing) existing.remove();

  const container = document.createElement('div');
  container.id = 'userAuthBadge';
  container.className = 'user-auth-badge';

  if (isLoggedIn && currentUser) {
    const segName = currentUser.segment ? currentUser.segment.toUpperCase() : 'NOT SET';
    const roleBadge = isAdmin ? '<span class="u-role-admin">🛡️ ADMIN</span>' : '<span class="u-role-client">👤 CLIENT</span>';

    container.innerHTML = `
      ${roleBadge}
      <span class="u-name">${esc(currentUser.full_name || currentUser.email)}</span>
      <span class="u-seg" onclick="openPersonaModal(false)">🎯 Goal: <b>${segName}</b> ✏️</span>
      ${isAdmin ? '<button class="u-btn-add-prop" onclick="openAdminAddPropertyModal()">➕ Add Property</button>' : ''}
      <button class="u-btn-logout" onclick="handleLogout()">🚪 Logout</button>
    `;
  } else {
    container.innerHTML = `
      <button class="u-btn-login" onclick="openAuthModal('login')">🔑 Sign In</button>
      <button class="u-btn-google" onclick="handleGoogleAuth()">
        <svg width="14" height="14" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>
        Continue with Google
      </button>
    `;
  }

  nav.appendChild(container);
}

/* ── LOAD & INJECT PERSONALIZED TOP BANNER ──────────────────── */
async function loadPersonalizedBanner() {
  try {
    const res = await fetch('/api/auth/banner');
    const data = await res.json();
    if (data.status === 'success' && data.banner_ad && data.listing) {
      renderTopBanner(data.banner_ad, data.listing, data.segment);
    }
  } catch (err) {
    console.error('Error loading banner:', err);
  }
}

function renderTopBanner(ad, listing, segment) {
  let existing = document.getElementById('personalizedTopBanner');
  if (existing) existing.remove();

  const target = document.querySelector('.top-nav') || document.querySelector('.header') || document.querySelector('header') || document.body;
  if (!target) return;

  const icon = segment ? (segment.icon || '🎯') : '🎯';
  const label = segment ? segment.label : 'Featured Islamabad Opportunity';

  const banner = document.createElement('div');
  banner.id = 'personalizedTopBanner';
  banner.className = 'personalized-banner';
  banner.innerHTML = `
    <div class="p-banner-left">
      <div class="p-banner-icon-ring">${icon}</div>
      <div class="p-banner-content">
        <div class="p-banner-badge">
          <span>RECOMMENDED FOR YOU</span> · <b>${esc(label)}</b>
        </div>
        <div class="p-banner-title">${esc(ad.headline)}</div>
        <div class="p-banner-sub">
          <span class="p-sub-title">📍 ${esc(listing.title || listing.location)}</span> · 
          <span class="p-sub-price">${esc(listing.price || 'Contact for Price')}</span>
        </div>
      </div>
    </div>

    <div class="p-banner-right">
      <button class="p-banner-btn-primary" onclick="window.open('https://wa.me/923165756055?text=' + encodeURIComponent('Hi, I saw your feature offer: ${esc(ad.headline)} for ${esc(listing.title)}. Please send virtual tour details.'), '_blank')">
        ${esc(ad.cta || 'Claim Offer &amp; Virtual Tour')}
      </button>
      <button class="p-banner-close" onclick="document.getElementById('personalizedTopBanner').remove()" title="Dismiss ad">✕</button>
    </div>
  `;

  if (target === document.body) {
    document.body.insertBefore(banner, document.body.firstChild);
  } else if (target.parentNode) {
    target.parentNode.insertBefore(banner, target.nextSibling);
  }
}

/* ── AUTH MODAL (LOGIN & SIGNUP) ────────────────────────────── */
function injectAuthModal() {
  const modal = document.createElement('div');
  modal.id = 'authModalOverlay';
  modal.className = 'auth-modal-overlay';
  modal.innerHTML = `
    <div class="auth-modal-card">
      <button class="modal-close" onclick="closeAuthModal()">✕</button>
      
      <div class="auth-brand-head">
        <div class="auth-brand-logo">🏛️ RealEstate AI</div>
        <div class="auth-brand-sub">Access hyper-personalized Islamabad property deals</div>
      </div>

      <div class="preset-credentials-bar">
        <span style="font-size:0.72rem; color:#94a3b8; font-weight:700;">Demo Login Shortcuts:</span>
        <div style="display:flex; gap:0.4rem; margin-top:0.3rem;">
          <button type="button" class="preset-btn admin-p" onclick="fillAuthDemo('admin')">🛡️ Fill Admin</button>
          <button type="button" class="preset-btn client-p" onclick="fillAuthDemo('client')">👤 Fill Client</button>
        </div>
      </div>

      <div class="auth-tabs">
        <button id="tabLogin" class="active" onclick="switchAuthTab('login')">Sign In</button>
        <button id="tabSignup" onclick="switchAuthTab('signup')">Create Account</button>
      </div>

      <form id="authForm" onsubmit="handleAuthSubmit(event)">
        <div id="nameGroup" class="form-group" style="display:none;">
          <label>Full Name</label>
          <input type="text" id="authName" class="form-control" placeholder="Ahsan Iqbal" />
        </div>
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" id="authEmail" class="form-control" placeholder="name@domain.com" required />
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" id="authPassword" class="form-control" placeholder="••••••••" required />
        </div>

        <div id="authError" class="auth-error" style="display:none;"></div>

        <button type="submit" id="authSubmitBtn" class="btn-auth-submit">Sign In &amp; Continue</button>
      </form>

      <div class="auth-divider"><span>OR CONTINUE WITH</span></div>

      <button class="btn-google-large" onclick="handleGoogleAuth()">
        <svg width="18" height="18" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/></svg>
        Continue with Google
      </button>
    </div>
  `;
  document.body.appendChild(modal);
}

function fillAuthDemo(role) {
  switchAuthTab('login');
  if (role === 'admin') {
    document.getElementById('authEmail').value = 'admin@realestate-ai.pk';
    document.getElementById('authPassword').value = 'Admin@2026!';
  } else {
    document.getElementById('authEmail').value = 'client@realestate-ai.pk';
    document.getElementById('authPassword').value = 'Client@2026!';
  }
}

let currentAuthMode = 'login';

function openAuthModal(mode = 'login') {
  currentAuthMode = mode;
  switchAuthTab(mode);
  document.getElementById('authModalOverlay').classList.add('visible');
}

function closeAuthModal() {
  document.getElementById('authModalOverlay').classList.remove('visible');
}

function switchAuthTab(mode) {
  currentAuthMode = mode;
  document.getElementById('tabLogin').classList.toggle('active', mode === 'login');
  document.getElementById('tabSignup').classList.toggle('active', mode === 'signup');
  document.getElementById('nameGroup').style.display = mode === 'signup' ? 'block' : 'none';
  document.getElementById('authSubmitBtn').textContent = mode === 'signup' ? 'Create Account & Continue' : 'Sign In & Continue';
  document.getElementById('authError').style.display = 'none';
}

async function handleAuthSubmit(e) {
  e.preventDefault();
  const errDiv = document.getElementById('authError');
  errDiv.style.display = 'none';

  const email = document.getElementById('authEmail').value;
  const password = document.getElementById('authPassword').value;
  const fullName = document.getElementById('authName').value;

  const url = currentAuthMode === 'signup' ? '/api/auth/signup' : '/api/auth/login';
  const payload = currentAuthMode === 'signup' ? { email, password, full_name: fullName } : { email, password };

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.status === 'success' && data.user) {
      currentUser = data.user;
      closeAuthModal();
      renderUserHeaderBadge(true);
      // ALWAYS open persona onboarding screen immediately right after login/signup
      openPersonaModal(true);
    } else {
      errDiv.textContent = data.error || 'Authentication failed.';
      errDiv.style.display = 'block';
    }
  } catch (err) {
    errDiv.textContent = 'Server error. Please try again.';
    errDiv.style.display = 'block';
  }
}

/* ── GOOGLE OAUTH — Real GSI popup with polished fallback ──── */
let _googleClientId = null;
let _googleConfigured = false;

// Fetch config on load
fetch('/api/auth/config').then(r => r.json()).then(cfg => {
  _googleClientId = cfg.google_client_id;
  _googleConfigured = cfg.google_configured;
  if (_googleConfigured) _loadGsiScript();
}).catch(() => {});

function _loadGsiScript() {
  if (document.getElementById('gsi-script')) return;
  const s = document.createElement('script');
  s.id = 'gsi-script';
  s.src = 'https://accounts.google.com/gsi/client';
  s.async = true;
  s.defer = true;
  document.head.appendChild(s);
}

async function handleGoogleAuth() {
  // ── Path A: Real GSI Popup (Client ID configured) ──────────
  if (_googleConfigured && _googleClientId && window.google) {
    try {
      const client = google.accounts.oauth2.initCodeClient({
        client_id: _googleClientId,
        scope: 'email profile openid',
        ux_mode: 'popup',
        callback: async (response) => {
          if (response.error) {
            console.error('Google OAuth error:', response.error);
            return;
          }
          // Exchange code for user info via backend
          const res = await fetch('/api/auth/google_callback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: response.code })
          });
          const data = await res.json();
          if (data.status === 'success' && data.user) {
            currentUser = data.user;
            closeAuthModal();
            renderUserHeaderBadge(true);
            openPersonaModal(true);
          }
        }
      });
      client.requestCode();
    } catch (e) {
      console.error('GSI init error:', e);
      _showGoogleSignInFallback();
    }
    return;
  }

  // ── Path B: GSI not loaded yet (configured but still loading) ─
  if (_googleConfigured && _googleClientId && !window.google) {
    // Try One-Tap prompt as alternative
    _loadGsiScript();
    setTimeout(handleGoogleAuth, 1200);
    return;
  }

  // ── Path C: No Client ID — Professional branded fallback modal ─
  _showGoogleSignInFallback();
}

function _showGoogleSignInFallback() {
  // Remove old if exists
  let old = document.getElementById('googleFallbackOverlay');
  if (old) old.remove();

  const overlay = document.createElement('div');
  overlay.id = 'googleFallbackOverlay';
  overlay.style.cssText = [
    'position:fixed; top:0; left:0; width:100vw; height:100vh;',
    'background:rgba(9,13,22,0.92); backdrop-filter:blur(20px);',
    'display:flex; align-items:center; justify-content:center; z-index:20000;',
    'animation:gfIn 0.3s ease;'
  ].join('');

  overlay.innerHTML = `
    <style>
      @keyframes gfIn { from{opacity:0;transform:scale(.96)} to{opacity:1;transform:scale(1)} }
      .gf-card {
        background:#fff; border-radius:28px; padding:2.5rem 2.2rem;
        width:100%; max-width:400px; box-shadow:0 30px 80px rgba(0,0,0,.5);
        font-family:'Roboto','Segoe UI',sans-serif; position:relative; text-align:center;
      }
      .gf-logo { display:flex; align-items:center; justify-content:center; gap:10px; margin-bottom:1.8rem; }
      .gf-logo svg { width:92px; }
      .gf-title { font-size:1.4rem; font-weight:500; color:#202124; margin-bottom:0.4rem; }
      .gf-sub { font-size:0.88rem; color:#5f6368; margin-bottom:1.8rem; }
      .gf-divider { font-size:0.78rem; color:#5f6368; margin:1.2rem 0; position:relative; }
      .gf-divider::before, .gf-divider::after { content:''; position:absolute; top:50%; width:42%; height:1px; background:#e0e0e0; }
      .gf-divider::before{left:0} .gf-divider::after{right:0}
      .gf-input {
        width:100%; box-sizing:border-box; padding:0.9rem 1rem; border-radius:4px;
        border:1px solid #dadce0; font-size:1rem; color:#202124; outline:none;
        transition:border-color .2s; margin-bottom:1.2rem;
      }
      .gf-input:focus { border-color:#1a73e8; box-shadow:0 0 0 2px rgba(26,115,232,.15); }
      .gf-btn-row { display:flex; justify-content:space-between; align-items:center; }
      .gf-btn-next {
        background:#1a73e8; color:#fff; border:none; border-radius:4px;
        padding:0.65rem 1.6rem; font-size:0.95rem; font-weight:500; cursor:pointer;
        transition:background .2s; letter-spacing:.25px;
      }
      .gf-btn-next:hover { background:#1557b0; }
      .gf-btn-cancel { background:none; border:none; color:#1a73e8; font-size:0.9rem; cursor:pointer; font-weight:500; }
      .gf-btn-cancel:hover { text-decoration:underline; }
      .gf-close { position:absolute; top:14px; right:18px; background:none; border:none; font-size:1.4rem; color:#5f6368; cursor:pointer; line-height:1; }
      .gf-err { font-size:0.8rem; color:#d93025; margin-top:-0.8rem; margin-bottom:0.8rem; text-align:left; }
    </style>
    <div class="gf-card">
      <button class="gf-close" onclick="document.getElementById('googleFallbackOverlay').remove()">✕</button>
      <div class="gf-logo">
        <svg viewBox="0 0 272 92" xmlns="http://www.w3.org/2000/svg">
          <path fill="#4285F4" d="M115.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18C71.25 34.32 81.24 25 93.5 25s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44S80.99 39.2 80.99 47.18c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/>
          <path fill="#D14836" d="M163.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18c0-12.85 9.99-22.18 22.25-22.18s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44s-12.51 5.46-12.51 13.44c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/>
          <path fill="#FBBC05" d="M209.75 26.34v39.82c0 16.38-9.66 23.07-21.08 23.07-10.75 0-17.22-7.19-19.66-13.07l8.48-3.53c1.51 3.61 5.21 7.87 11.17 7.87 7.31 0 11.84-4.51 11.84-13v-3.19h-.34c-2.18 2.69-6.38 5.04-11.68 5.04-11.09 0-21.25-9.66-21.25-22.09 0-12.52 10.16-22.26 21.25-22.26 5.29 0 9.49 2.35 11.68 4.96h.34v-3.61h9.25zm-8.56 20.92c0-7.81-5.21-13.52-11.84-13.52-6.72 0-12.35 5.71-12.35 13.52 0 7.73 5.63 13.36 12.35 13.36 6.63 0 11.84-5.63 11.84-13.36z"/>
          <path fill="#4285F4" d="M225 3v65h-9.5V3h9.5z"/>
          <path fill="#34A853" d="M262.02 54.48l7.56 5.04c-2.44 3.61-8.32 9.83-18.48 9.83-12.6 0-22.01-9.74-22.01-22.18 0-13.19 9.49-22.18 20.92-22.18 11.51 0 17.14 9.16 18.98 14.11l1.01 2.52-29.65 12.28c2.27 4.45 5.8 6.72 10.75 6.72 4.96 0 8.4-2.44 10.92-6.14zm-23.27-7.98l19.82-8.23c-1.09-2.77-4.37-4.7-8.23-4.7-4.95 0-11.84 4.37-11.59 12.93z"/>
          <path fill="#4285F4" d="M35.29 41.41V32h31.24c.31 1.63.47 3.55.47 5.63 0 7.06-1.93 15.79-8.15 22.01-6.05 6.3-13.78 9.66-24.02 9.66C16.32 69.3.85 54.33.85 35.57.85 16.8 16.32 1.83 35.38 1.83c10.5 0 17.98 4.12 23.6 9.49l-6.64 6.64c-4.03-3.78-9.49-6.72-16.97-6.72-13.86 0-24.7 11.17-24.7 25.03 0 13.86 10.84 25.03 24.7 25.03 8.99 0 14.11-3.61 17.39-6.89 2.66-2.66 4.41-6.46 5.1-11.65l-22.57.25z"/>
        </svg>
      </div>
      <div class="gf-title">Sign in with Google</div>
      <div class="gf-sub">to continue to RealEstate AI Platform</div>
      <div id="gf-err" class="gf-err" style="display:none;"></div>
      <input id="gf-email" class="gf-input" type="email" placeholder="Enter your email" autocomplete="email" />
      <div class="gf-btn-row">
        <button class="gf-btn-cancel" onclick="document.getElementById('googleFallbackOverlay').remove()">Cancel</button>
        <button class="gf-btn-next" onclick="_submitGoogleFallback()">Next</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  // Focus email input
  setTimeout(() => {
    const inp = document.getElementById('gf-email');
    if (inp) inp.focus();
  }, 100);

  // Allow Enter key
  overlay.addEventListener('keydown', e => {
    if (e.key === 'Enter') _submitGoogleFallback();
    if (e.key === 'Escape') overlay.remove();
  });
}

async function _submitGoogleFallback() {
  const emailEl = document.getElementById('gf-email');
  const errEl   = document.getElementById('gf-err');
  const email   = (emailEl?.value || '').trim();

  if (!email || !email.includes('@')) {
    if (errEl) { errEl.textContent = 'Enter a valid Google email address.'; errEl.style.display = 'block'; }
    return;
  }

  // Derive display name from email prefix
  const namePart = email.split('@')[0].replace(/[._]/g, ' ');
  const fullName = namePart.replace(/\b\w/g, c => c.toUpperCase());
  const googleId = 'gsi_' + btoa(email).replace(/[^a-zA-Z0-9]/g, '').substring(0, 20);

  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, full_name: fullName, google_id: googleId })
    });
    const data = await res.json();
    if (data.status === 'success' && data.user) {
      currentUser = data.user;
      document.getElementById('googleFallbackOverlay')?.remove();
      closeAuthModal();
      renderUserHeaderBadge(true);
      openPersonaModal(true);
    } else {
      if (errEl) { errEl.textContent = data.error || 'Sign-in failed.'; errEl.style.display = 'block'; }
    }
  } catch (err) {
    if (errEl) { errEl.textContent = 'Network error. Please try again.'; errEl.style.display = 'block'; }
  }
}

async function handleLogout() {
  await fetch('/api/auth/logout', { method: 'POST' });
  currentUser = null;
  renderUserHeaderBadge(false);
  loadPersonalizedBanner();
}

/* ── PERSONA ONBOARDING INTERSTITIAL MODAL ────────────────── */
function injectPersonaModal() {
  const modal = document.createElement('div');
  modal.id = 'personaModalOverlay';
  modal.className = 'auth-modal-overlay';
  modal.innerHTML = `
    <div class="persona-modal-card">
      <button class="modal-close" onclick="closePersonaModal()">✕</button>
      <div class="p-modal-title">🎯 Personalize Your Experience</div>
      <div class="p-modal-sub">What is your primary goal today? We will customize real estate listings &amp; ad offers specifically for you.</div>

      <div class="p-modal-grid">
        <div class="p-modal-item" onclick="saveUserPersona('family')">
          <div class="p-m-icon">👨‍👩‍👧‍👦</div>
          <div class="p-m-name">Family &amp; Parent</div>
          <div class="p-m-desc">Safety, schools &amp; spacious homes</div>
        </div>
        <div class="p-modal-item" onclick="saveUserPersona('investor')">
          <div class="p-m-icon">📈</div>
          <div class="p-m-name">Investor &amp; High ROI</div>
          <div class="p-m-desc">8-12% rental yield &amp; capital growth</div>
        </div>
        <div class="p-modal-item" onclick="saveUserPersona('overseas')">
          <div class="p-m-icon">✈️</div>
          <div class="p-m-name">Overseas Pakistani</div>
          <div class="p-m-desc">100% legal verification &amp; virtual tours</div>
        </div>
        <div class="p-modal-item" onclick="saveUserPersona('luxury')">
          <div class="p-m-icon">👑</div>
          <div class="p-m-name">Luxury Seeker</div>
          <div class="p-m-desc">Penthouses, smart homes &amp; VIP sector</div>
        </div>
        <div class="p-modal-item" onclick="saveUserPersona('budget')">
          <div class="p-m-icon">💡</div>
          <div class="p-m-name">Budget Buyer</div>
          <div class="p-m-desc">3-year easy installment plans</div>
        </div>
        <div class="p-modal-item" onclick="saveUserPersona('tenant')">
          <div class="p-m-icon">🎓</div>
          <div class="p-m-name">Young Pro / Student</div>
          <div class="p-m-desc">Near Metro &amp; high-speed fiber ready</div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function openPersonaModal(isForced = false) {
  const overlay = document.getElementById('personaModalOverlay');
  overlay.classList.add('visible');
  const closeBtn = overlay.querySelector('.modal-close');
  if (closeBtn) closeBtn.style.display = isForced ? 'none' : 'block';
}

function closePersonaModal() {
  document.getElementById('personaModalOverlay').classList.remove('visible');
}

async function saveUserPersona(segmentKey) {
  try {
    const res = await fetch('/api/auth/segment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ segment: segmentKey })
    });
    const data = await res.json();
    if (data.status === 'success') {
      if (currentUser) currentUser.segment = segmentKey;
      closePersonaModal();
      renderUserHeaderBadge(!!currentUser);
      loadPersonalizedBanner();
    }
  } catch (err) {
    console.error('Error saving persona segment:', err);
  }
}

/* ── STYLES INJECTION ────────────────────────────────────────── */
function injectAuthStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .user-auth-badge {
      display: flex; align-items: center; gap: 0.6rem; margin-left: auto; font-size: 0.8rem;
    }
    .u-name { font-weight: 700; color: #fff; }
    .u-seg {
      background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);
      padding: 0.3rem 0.7rem; border-radius: 20px; cursor: pointer; transition: all 0.2s ease;
    }
    .u-seg:hover { background: rgba(168, 85, 247, 0.3); }
    .u-btn-login, .u-btn-logout {
      background: rgba(255,255,255,0.08); color: #fff; border: 1px solid rgba(255,255,255,0.15);
      padding: 0.35rem 0.8rem; border-radius: 20px; font-weight: 600; cursor: pointer; font-size: 0.78rem;
    }
    .u-btn-google {
      background: #ffffff; color: #1e293b; border: none; padding: 0.35rem 0.85rem; border-radius: 20px;
      font-weight: 700; cursor: pointer; font-size: 0.78rem; display: flex; align-items: center; gap: 0.4rem;
    }

    .personalized-banner {
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(56, 189, 248, 0.15) 50%, rgba(15, 23, 42, 0.9) 100%);
      border: 1px solid rgba(16, 185, 129, 0.35);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08);
      border-radius: 16px; margin: 1rem 2rem 0.5rem; padding: 0.9rem 1.4rem;
      display: flex; align-items: center; justify-content: space-between; gap: 1rem;
      animation: slideDown 0.4s ease; flex-wrap: wrap;
    }
    @keyframes slideDown { from { transform: translateY(-30px); opacity:0; } to { transform: translateY(0); opacity:1; } }
    .p-banner-left { display: flex; align-items: center; gap: 1rem; flex: 1; min-width: 280px; }
    .p-banner-icon-ring {
      font-size: 1.8rem; background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.4);
      width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
      box-shadow: 0 0 15px rgba(16, 185, 129, 0.3); flex-shrink: 0;
    }
    .p-banner-content { text-align: left; }
    .p-banner-badge { font-size: 0.7rem; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.15rem; }
    .p-banner-badge span { color: #38bdf8; }
    .p-banner-title { font-weight: 800; font-size: 1.05rem; color: #fff; line-height: 1.3; }
    .p-banner-sub { font-size: 0.82rem; color: #cbd5e1; margin-top: 0.15rem; }
    .p-sub-title { color: #f8fafc; font-weight: 600; }
    .p-sub-price { color: #10b981; font-weight: 800; }
    .p-banner-right { display: flex; align-items: center; gap: 0.75rem; }
    .p-banner-btn-primary {
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: #042f2e; font-weight: 800; font-size: 0.85rem; padding: 0.6rem 1.2rem;
      border: none; border-radius: 30px; cursor: pointer; transition: all 0.25s ease;
      box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35); white-space: nowrap;
    }
    .p-banner-btn-primary:hover {
      transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5);
      background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
    }
    .p-banner-close {
      background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
      color: #94a3b8; font-size: 0.9rem; cursor: pointer; width: 28px; height: 28px;
      border-radius: 50%; display: flex; align-items: center; justify-content: center;
      transition: all 0.2s ease;
    }
    .p-banner-close:hover { background: rgba(255,255,255,0.15); color: #fff; }

    .auth-brand-head {
      text-align: center; margin-bottom: 1.25rem;
    }
    .auth-brand-logo {
      font-family: 'Outfit', sans-serif; font-size: 1.4rem; font-weight: 800;
      background: linear-gradient(135deg, #ffffff 30%, #38bdf8 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      margin-bottom: 0.25rem;
    }
    .auth-brand-sub {
      font-size: 0.78rem; color: #94a3b8; line-height: 1.4;
    }

    .auth-modal-overlay {
      position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(9, 13, 22, 0.85); backdrop-filter: blur(16px);
      display: none; align-items: center; justify-content: center; z-index: 10000;
    }
    .auth-modal-overlay.visible { display: flex; }
    .auth-modal-card, .persona-modal-card {
      background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
      border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px;
      padding: 2.2rem 2rem; width: 100%; max-width: 440px; position: relative;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6), 0 0 30px rgba(56, 189, 248, 0.1);
      animation: modalFadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    }
    @keyframes modalFadeIn {
      from { opacity: 0; transform: scale(0.95) translateY(10px); }
      to { opacity: 1; transform: scale(1) translateY(0); }
    }
    .persona-modal-card { max-width: 680px; text-align: center; }
    .modal-close {
      position: absolute; top: 18px; right: 18px; background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.1); color: #94a3b8; font-size: 1rem;
      width: 32px; height: 32px; border-radius: 50%; cursor: pointer; transition: all 0.2s ease;
      display: flex; align-items: center; justify-content: center;
    }
    .modal-close:hover { background: rgba(255, 255, 255, 0.15); color: #fff; }

    .auth-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.25rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.5rem; }
    .auth-tabs button { background: none; border: none; color: #94a3b8; font-weight: 700; font-size: 0.95rem; cursor: pointer; padding: 0.4rem 0.8rem; transition: color 0.2s ease; }
    .auth-tabs button.active { color: #38bdf8; border-bottom: 2px solid #38bdf8; }

    .form-group { display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 0.9rem; text-align: left; }
    .form-group label { font-size: 0.78rem; font-weight: 600; color: #94a3b8; }
    .form-control {
      background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 10px; padding: 0.65rem 0.9rem; color: #fff; font-size: 0.88rem;
      outline: none; transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .form-control:focus { border-color: #38bdf8; box-shadow: 0 0 12px rgba(56, 189, 248, 0.25); }

    .btn-auth-submit {
      background: linear-gradient(135deg, #10b981 0%, #38bdf8 100%); color: #042f2e; font-weight: 800;
      width: 100%; padding: 0.8rem; border: none; border-radius: 12px; cursor: pointer; margin-top: 0.8rem;
      font-size: 0.92rem; transition: all 0.25s ease; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    .btn-auth-submit:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.45); }

    .auth-divider { text-align: center; margin: 1.2rem 0; font-size: 0.72rem; font-weight: 700; color: #64748b; position: relative; letter-spacing: 0.5px; }
    .auth-divider::before, .auth-divider::after { content: ''; position: absolute; top: 50%; width: 35%; height: 1px; background: rgba(255,255,255,0.08); }
    .auth-divider::before { left: 0; } .auth-divider::after { right: 0; }
    .btn-google-large {
      background: #ffffff; color: #1e293b; font-weight: 700; font-size: 0.88rem; width: 100%;
      padding: 0.75rem; border: none; border-radius: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.65rem;
      transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .btn-google-large:hover { background: #f8fafc; transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.3); }
    .auth-error { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.55rem; border-radius: 8px; font-size: 0.8rem; margin-top: 0.6rem; text-align: center; }

    .u-role-admin {
      background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(249, 115, 22, 0.2));
      color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4);
      padding: 0.25rem 0.6rem; border-radius: 20px; font-weight: 800; font-size: 0.7rem; letter-spacing: 0.5px;
    }
    .u-role-client {
      background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 0.25rem 0.6rem; border-radius: 20px; font-weight: 800; font-size: 0.7rem; letter-spacing: 0.5px;
    }
    .u-btn-add-prop {
      background: linear-gradient(135deg, #10b981, #059669); color: #fff; border: none;
      padding: 0.35rem 0.85rem; border-radius: 20px; font-weight: 800; font-size: 0.78rem; cursor: pointer;
      box-shadow: 0 0 12px rgba(16, 185, 129, 0.3); transition: all 0.2s ease;
    }
    .u-btn-add-prop:hover { transform: translateY(-1px); box-shadow: 0 0 18px rgba(16, 185, 129, 0.5); }

    .preset-credentials-bar {
      background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 12px; padding: 0.65rem 0.9rem; margin-bottom: 1.1rem; text-align: left;
    }
    .preset-btn {
      background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.12);
      color: #fff; font-size: 0.75rem; font-weight: 700; padding: 0.3rem 0.65rem; border-radius: 8px; cursor: pointer;
      transition: all 0.2s ease;
    }
    .preset-btn:hover { background: rgba(255, 255, 255, 0.18); }
    .preset-btn.admin-p { border-color: rgba(239, 68, 68, 0.4); color: #fca5a5; }
    .preset-btn.client-p { border-color: rgba(56, 189, 248, 0.4); color: #7dd3fc; }

    .p-modal-title { font-family: 'Outfit', sans-serif; font-size: 1.7rem; font-weight: 800; color: #fff; margin-bottom: 0.4rem; }
    .p-modal-sub { color: #94a3b8; font-size: 0.88rem; margin-bottom: 1.5rem; line-height: 1.5; }
    .p-modal-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; text-align: left; }
    .p-modal-item {
      background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px;
      padding: 1.1rem; cursor: pointer; transition: all 0.25s ease; position: relative; overflow: hidden;
    }
    .p-modal-item:hover { background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(56, 189, 248, 0.15) 100%); border-color: #c084fc; transform: translateY(-3px); box-shadow: 0 8px 20px rgba(168, 85, 247, 0.25); }
    .p-m-icon { font-size: 2rem; margin-bottom: 0.4rem; }
    .p-m-name { font-weight: 700; font-size: 0.95rem; color: #fff; }
    .p-m-desc { font-size: 0.76rem; color: #94a3b8; margin-top: 0.25rem; line-height: 1.3; }

    /* Access Denied Toast */
    .access-toast {
      position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
      background: linear-gradient(135deg, rgba(239,68,68,0.95), rgba(220,38,38,0.95));
      color: #fff; padding: 0.85rem 1.6rem; border-radius: 30px;
      font-size: 0.9rem; font-weight: 700; z-index: 99999;
      box-shadow: 0 8px 30px rgba(239,68,68,0.45); border: 1px solid rgba(255,255,255,0.15);
      animation: toastIn 0.35s cubic-bezier(0.16,1,0.3,1);
      display: flex; align-items: center; gap: 0.6rem; white-space: nowrap;
    }
    @keyframes toastIn { from { opacity:0; transform:translateX(-50%) translateY(20px); } to { opacity:1; transform:translateX(-50%) translateY(0); } }
  `;
  document.head.appendChild(style);
}

/* ── ACCESS DENIED TOAST ─────────────────────────────────────── */
function _showAccessToast(message) {
  const old = document.getElementById('accessDeniedToast');
  if (old) old.remove();

  const toast = document.createElement('div');
  toast.id = 'accessDeniedToast';
  toast.className = 'access-toast';
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.4s ease';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
