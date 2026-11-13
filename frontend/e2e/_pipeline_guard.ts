// Installed by the Product Studio pipeline and re-copied before every E2E run.
// Do not edit it and do not stop importing it: edits are overwritten, and a spec
// that imports `@playwright/test` directly is rerouted here automatically.
//
// Every spec imports `test` and `expect` from './_pipeline_guard'. Everything
// `@playwright/test` exports is available from here too. At the end of each test
// the guard fails it if the app hit any of:
//   - an API response with status >= 400 (API = path containing E2E_API_PATH, default '/api/')
//   - a 2xx JSON API response whose body reports a failed state
//     (`"state": "FailedInternalError"`, `"scan_status": "failed"`, `"success": false`)
//   - a 2xx JSON API response carrying an exception message as data
//     (`"failure_summary": "too many values to unpack (expected 2)"`) - never allowable
//   - an API request that never got a response (wrong base URL, CORS)
//   - an uncaught exception in the page
// Requests a spec makes itself with `page.request` are checked the same way.
// A test whose purpose IS an error response says so:
//   test('rejects a wrong password', async ({ page, apiGuard }) => {
//     apiGuard.allow(401, '/auth/login');
//     ...
//   });
// and a test whose purpose IS a failed operation (an unreachable target, say):
//   apiGuard.allowFailedState('/api/scan/');
// A 401 on a request sent without an Authorization header is never reported:
// that is the app checking a session that does not exist, not a defect.
import { test as base } from '@playwright/test';

export * from '@playwright/test';

const API_PATH = process.env.E2E_API_PATH || '/api/';

export interface ApiGuard {
  /** Expect an error response in this test: `allow(401, '/auth/login')`. */
  allow(status: number, urlPart: string): void;
  /** Expect a 2xx response that reports a failed state: `allowFailedState('/api/jobs/')`. */
  allowFailedState(urlPart: string): void;
}

type Observed = {
  status: number;
  url: string;
  failedState?: boolean;
  // Exception text in a 2xx body: never permitted by `allow`/`allowFailedState`.
  crash?: boolean;
  describe: () => Promise<string | null>;
};

// Fields an API uses to say how an operation ended, and the values that mean it
// did not. Only the top level and a `data`/`result`/`payload` envelope are read:
// a list of past jobs that includes a failed one is data, not a failure. A
// resource prefix counts (`scan_status`, `job_state`): a scan
// that crashed answered every poll with 200 and `"scan_status": "failed"`.
const STATE_KEY =
  /^(?:[a-z][a-z0-9]*_)?(state|status|lifecycle_?state|outcome|terminal_?outcome|result)$/i;
const FAILED_VALUE =
  /^(failed|failure|error|errored|fatal|crashed|aborted)$|^(failed|error)[-_ ]?[a-z]|[-_ ]?(failed|failure|error)$/i;
const ENVELOPE_KEY = /^(data|result|payload)$/i;

function failedState(body: unknown, depth = 0): string | null {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return null;
  for (const [key, value] of Object.entries(body as Record<string, unknown>)) {
    if ((key === 'success' || key === 'ok') && value === false) return `${key}=false`;
    if (STATE_KEY.test(key) && typeof value === 'string' && FAILED_VALUE.test(value.trim())) {
      return `${key}=${value}`;
    }
  }
  if (depth > 0) return null;
  for (const [key, value] of Object.entries(body as Record<string, unknown>)) {
    if (!ENVELOPE_KEY.test(key)) continue;
    const found = failedState(value, depth + 1);
    if (found) return `${key}.${found}`;
  }
  return null;
}

// An interpreter's error message returned as data: the same scan stored
// `"failure_summary": "too many values to unpack (expected 2)"` and served it
// with a 200. A failed operation is sometimes what a test is about; an exception
// message in a response never is, so `allowFailedState` does not cover it.
const CRASH_TEXT =
  /Traceback \(most recent call last\)|(?:too many|not enough) values to unpack|object has no attribute '|object is not (?:subscriptable|callable|iterable)|unsupported operand type\(s\)|takes \d+ positional arguments? but \d+ (?:were|was) given|missing \d+ required (?:positional|keyword-only) arguments?|got an unexpected keyword argument|name '[A-Za-z_]\w*' is not defined|'NoneType' object|list index out of range|Cannot read propert(?:y|ies) of (?:undefined|null)/;

function crashText(body: unknown, depth = 0): string | null {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return null;
  for (const [key, value] of Object.entries(body as Record<string, unknown>)) {
    if (typeof value === 'string' && CRASH_TEXT.test(value)) {
      return `${key}="${value.trim().slice(0, 160)}"`;
    }
  }
  if (depth > 0) return null;
  for (const [key, value] of Object.entries(body as Record<string, unknown>)) {
    if (!ENVELOPE_KEY.test(key)) continue;
    const found = crashText(value, depth + 1);
    if (found) return `${key}.${found}`;
  }
  return null;
}

function isApi(url: string): boolean {
  try {
    return new URL(url).pathname.includes(API_PATH);
  } catch {
    return false;
  }
}

function pathOf(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.pathname + parsed.search;
  } catch {
    return url;
  }
}

type GuardState = ApiGuard & {
  allowed: { status: number; urlPart: string }[];
  allowedFailedStates: string[];
  observed: Observed[];
  pageErrors: string[];
};

// A 2xx JSON body is not proof the operation worked: record the two ways it can
// say otherwise. `pending` is read when the response arrives - the body can be
// gone by the end of the test.
function observeBody(
  state: GuardState,
  status: number,
  url: string,
  label: string,
  pending: Promise<unknown>,
): void {
  state.observed.push({
    status,
    url,
    failedState: true,
    describe: async () => {
      const body = await pending;
      const found = failedState(body);
      return found
        ? `API ${status} ${label} reported ${found} - the request succeeded but the operation failed`
        : null;
    },
  });
  state.observed.push({
    status,
    url,
    crash: true,
    describe: async () => {
      const found = crashText(await pending);
      return found
        ? `API ${status} ${label} returned an exception message as data (${found}) - the server caught a crash and reported it as a result`
        : null;
    },
  });
}

const GUARD_STATE = Symbol.for('pipeline.apiGuard.state');

export const test = base.extend<{ apiGuard: ApiGuard }>({
  apiGuard: async ({}, use) => {
    const state: GuardState = {
      allowed: [],
      allowedFailedStates: [],
      observed: [],
      pageErrors: [],
      allow(status: number, urlPart: string) {
        state.allowed.push({ status, urlPart });
      },
      allowFailedState(urlPart: string) {
        state.allowedFailedStates.push(urlPart);
      },
    };
    await use(state);
  },

  page: async ({ page, apiGuard }, use, testInfo) => {
    const state = apiGuard as GuardState;

    page.on('response', (response) => {
      const status = response.status();
      const url = response.url();
      if (!isApi(url)) return;
      const request = response.request();
      if (status < 400) {
        // A 2xx is not proof the operation worked: an app that catches its own
        // exception and stores it as `state: "Failed..."` answers 200 to every
        // poll, and a spec that only checks the page has text passes over it.
        if (!/json/i.test(response.headers()['content-type'] || '')) return;
        const pending = response.json().catch(() => null);
        observeBody(state, status, url, `${request.method()} ${pathOf(url)}`, pending);
        return;
      }
      state.observed.push({
        status,
        url,
        describe: async () => {
          if (status === 401 && !(await request.headerValue('authorization'))) return null;
          let detail = '';
          try {
            detail = (await response.text()).replace(/\s+/g, ' ').trim().slice(0, 200);
          } catch {
            // The body can be gone once the page navigated; the status is enough.
          }
          return `API ${status} ${request.method()} ${pathOf(url)}${detail ? ` - ${detail}` : ''}`;
        },
      });
    });

    page.on('requestfailed', (request) => {
      const url = request.url();
      if (!isApi(url)) return;
      const reason = request.failure()?.errorText || 'no response';
      // Navigating away cancels in-flight requests; that is not an app defect.
      if (/ERR_ABORTED|NS_BINDING_ABORTED|cancelled/i.test(reason)) return;
      state.observed.push({
        status: 0,
        url,
        describe: async () =>
          `API request failed ${request.method()} ${pathOf(url)} - ${reason} (wrong base URL or CORS?)`,
      });
    });

    page.on('pageerror', (error) => {
      state.pageErrors.push(`Uncaught page error - ${error.message}`);
    });

    // `page.request` goes through Playwright's API client and fires none of the
    // page's events: a spec that polled a scan with `page.request.get` showed the
    // guard nothing while every poll said the scan had crashed. Wrapped once per
    // client; the state it reports to is this test's.
    const client = page.request as unknown as Record<string | symbol, unknown>;
    client[GUARD_STATE] = state;
    if (!client.__pipelineGuardWrapped) {
      client.__pipelineGuardWrapped = true;
      for (const method of ['get', 'post', 'put', 'patch', 'delete', 'head', 'fetch']) {
        const original = client[method];
        if (typeof original !== 'function') continue;
        client[method] = async (...args: unknown[]) => {
          const response = await (original as (...a: unknown[]) => Promise<any>).apply(page.request, args);
          const current = client[GUARD_STATE] as GuardState | undefined;
          const url: string = response.url();
          if (!current || !isApi(url)) return response;
          const status: number = response.status();
          const label = `${method === 'fetch' ? 'FETCH' : method.toUpperCase()} ${pathOf(url)} (page.request)`;
          if (status >= 400) {
            // A spec calling an authenticated endpoint without its token is a
            // spec mistake, not an app defect; every other status is reported.
            if (status === 401) return response;
            const detail = await response
              .text()
              .then((text: string) => text.replace(/\s+/g, ' ').trim().slice(0, 200))
              .catch(() => '');
            current.observed.push({
              status,
              url,
              describe: async () => `API ${status} ${label}${detail ? ` - ${detail}` : ''}`,
            });
          } else if (/json/i.test(response.headers()['content-type'] || '')) {
            observeBody(current, status, url, label, response.json().catch(() => null));
          }
          return response;
        };
      }
    }

    await use(page);

    const problems: string[] = [];
    for (const item of state.observed) {
      const permitted = item.crash
        ? false
        : item.failedState
          ? state.allowedFailedStates.some((urlPart) => item.url.includes(urlPart))
          : state.allowed.some(
              (rule) => rule.status === item.status && item.url.includes(rule.urlPart),
            );
      if (permitted) continue;
      const line = await item.describe().catch(() => `API ${item.status} ${pathOf(item.url)}`);
      if (line) problems.push(line);
    }
    problems.push(...state.pageErrors);
    if (problems.length === 0) return;

    await testInfo.attach('api-guard.json', {
      body: JSON.stringify({ problems, allowed: state.allowed }, null, 2),
      contentType: 'application/json',
    });
    // The first line is what the pipeline's failing-test list shows, so it names
    // the first problem rather than a count alone.
    throw new Error(
      `${problems[0]} (${problems.length} API/browser error(s) in this test)\n` +
        problems.map((problem) => `  - ${problem}`).join('\n'),
    );
  },
});
