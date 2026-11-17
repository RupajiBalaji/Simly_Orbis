/**
 * Simly Orbis Client-Side Router & App Shell (frontend/router.js)
 * Standard: Section 8 & Section 18 (P1-T3) of Simly Orbis MVP Build Specification.
 *
 * Supports routes:
 * - #/lobby (or #/)
 * - #/briefing?exp=<exp_id>
 * - #/lab?exp=<exp_id>
 * - #/report?session=<session_id>
 * - #/leaderboard
 * - #/settings
 * - #/model-cards (or #/model-cards/:id)
 * - #/reality-check
 * - #/404 (or any unrecognized route)
 *
 * Supports deep linking, history pushState/replaceState, and browser back/forward buttons.
 */

export class Router {
  constructor({ routes, defaultRoute = 'lobby', notFoundRoute = '404' }) {
    this.routes = routes || {};
    this.defaultRoute = defaultRoute;
    this.notFoundRoute = notFoundRoute;
    this.currentRoute = null;
    this.currentParams = {};

    window.addEventListener('hashchange', () => this.handleHashChange());
  }

  init() {
    this.handleHashChange();
  }

  parseHash() {
    const raw = window.location.hash.slice(1).trim(); // remove leading #
    if (!raw || raw === '/') {
      return { routeName: this.defaultRoute, params: {} };
    }

    const [pathPart, queryPart] = raw.split('?');
    const cleanPath = pathPart.replace(/^\/+|\/+$/g, '');
    const segments = cleanPath.split('/');
    const routeName = segments[0] || this.defaultRoute;

    const params = {};
    if (segments.length > 1) {
      params.id = segments.slice(1).join('/');
    }

    if (queryPart) {
      const searchParams = new URLSearchParams(queryPart);
      for (const [key, value] of searchParams.entries()) {
        params[key] = value;
      }
    }

    return { routeName, params };
  }

  navigate(path) {
    if (!path.startsWith('#/')) {
      path = '#/' + path.replace(/^#?\/?/, '');
    }
    window.location.hash = path;
  }

  handleHashChange() {
    const { routeName, params } = this.parseHash();
    const handler = this.routes[routeName];

    if (handler) {
      this.currentRoute = routeName;
      this.currentParams = params;
      handler(params);
    } else {
      this.currentRoute = this.notFoundRoute;
      this.currentParams = { requestedRoute: routeName };
      if (this.routes[this.notFoundRoute]) {
        this.routes[this.notFoundRoute](this.currentParams);
      }
    }

    this.updateActiveNavLinks(routeName);
  }

  updateActiveNavLinks(routeName) {
    document.querySelectorAll('[data-nav-route]').forEach(el => {
      const target = el.getAttribute('data-nav-route');
      if (target === routeName) {
        el.setAttribute('aria-current', 'page');
        el.classList.add('nav-active');
      } else {
        el.removeAttribute('aria-current');
        el.classList.remove('nav-active');
      }
    });
  }
}

// Global helper for declarative navigation
export function initRouter(routes) {
  const router = new Router({ routes });
  window.__orbisRouter = router;
  router.init();
  return router;
}
