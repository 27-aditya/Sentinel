const TOKEN_KEY = "sentinel_access_token";

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

export async function login(username, password) {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
    method: "POST",
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
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
    ...options,
    headers: authHeaders(options.headers),
  });
  if (response.status === 401) {
    clearAccessToken();
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
