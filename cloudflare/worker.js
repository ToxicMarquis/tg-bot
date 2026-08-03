const TELEGRAM_HOST = "api.telegram.org";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const secret = (env.PROXY_SECRET || "").trim();
    if (!secret) {
      return new Response("PROXY_SECRET is not configured", { status: 500 });
    }
    const prefix = "/" + secret;
    if (url.pathname !== prefix && !url.pathname.startsWith(prefix + "/")) {
      return new Response("Not found", { status: 404 });
    }
    url.pathname = url.pathname.slice(prefix.length) || "/";
    url.protocol = "https:";
    url.hostname = TELEGRAM_HOST;
    url.port = "";
    return fetch(new Request(url, request));
  },
};
