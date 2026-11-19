const TOKEN_KEY = "sentinel_access_token";
const REFRESH_SKEW_SECONDS = 60;

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token) {
  window.sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken() {
  window.sessionStorage.removeItem(TOKEN_KEY);
}

function tokenExpirySeconds(token) {
  try {
    const segment = token.split(".")[1];
    const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const payload = JSON.parse(
      typeof atob === "function"
        ? atob(padded)
        : Buffer.from(normalized, "base64").toString("utf8")
    );
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch (_) {
    return null;
  }
}

export async function refreshAccessToken() {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    clearAccessToken();
    return false;
  }
  const data = await response.json();
  if (!data.access_token) {
    clearAccessToken();
    return false;
  }
  setAccessToken(data.access_token);
  return true;
}

// Ensure the token used for API calls and WebSocket reconnects is still valid.
// The refresh token lives in an httpOnly cookie, so it cannot be read from JS.
export async function ensureFreshToken() {
  const token = getAccessToken();
  if (!token) return false;
  const exp = tokenExpirySeconds(token);
  if (exp !== null && exp > Date.now() / 1000 + REFRESH_SKEW_SECONDS) {
    return true;
  }
  return refreshAccessToken();
}

export async function login(username, password) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password }),
  });
  if (!response.ok) {
    throw new Error("Invalid credentials");
  }
  const data = await response.json();
  setAccessToken(data.access_token);
  return data.access_token;
}

export function authHeaders(headers = {}) {
  const token = getAccessToken();
  return token ? { ...headers, Authorization: `Bearer ${token}` } : headers;
}

export async function apiFetch(path, options = {}) {
  const send = () =>
    fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
      ...options,
      headers: authHeaders(options.headers),
    });

  let response = await send();
  if (response.status === 401 && (await refreshAccessToken())) {
    response = await send();
  }
  return response;
}

export function mediaUrl(url) {
  if (!url) return url;
  const token = getAccessToken();
  if (url.startsWith("/static/")) {
    const query = token ? `?token=${encodeURIComponent(token)}` : "";
    return `${process.env.NEXT_PUBLIC_API_URL}${url}${query}`;
  }
  const root = process.env.NEXT_PUBLIC_MEDIA_ROOT;
  if (root && url.startsWith(root + "/")) {
    const relative = url.slice(root.length + 1);
    const tokenQuery = token ? `&token=${encodeURIComponent(token)}` : "";
    return `${process.env.NEXT_PUBLIC_API_URL}/api/media?path=${encodeURIComponent(relative)}${tokenQuery}`;
  }
  return url;
}

export function websocketUrl() {
  const base = process.env.NEXT_PUBLIC_WS_URL;
  const token = getAccessToken();
  return token ? `${base}?token=${encodeURIComponent(token)}` : base;
}
