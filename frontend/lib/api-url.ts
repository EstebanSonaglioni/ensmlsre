export function apiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL;
  if (raw === undefined || raw === "") {
    return "/backend";
  }
  return raw.replace(/\/$/, "");
}

export function wsUrl(): string {
  const base = apiBaseUrl();
  if (base.startsWith("/")) {
    const proto =
      typeof window !== "undefined" && window.location.protocol === "https:"
        ? "wss:"
        : "ws:";
    const host =
      typeof window !== "undefined" ? window.location.host : "localhost:3000";
    return `${proto}//${host}${base}/ws`;
  }
  return `${base.replace(/^http/, "ws")}/ws`;
}
