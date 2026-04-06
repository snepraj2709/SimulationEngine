const URL_SCHEME_PATTERN = /^[a-zA-Z][a-zA-Z\d+.-]*:\/\//;

function isIpAddress(hostname: string): boolean {
  return /^[\d.:]+$/.test(hostname);
}

function hasPublicHostname(hostname: string): boolean {
  if (hostname === "localhost") {
    return false;
  }
  return hostname.includes(".") || isIpAddress(hostname);
}

export function normalizeWebsiteUrlInput(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) {
    throw new Error("invalid_url");
  }

  const candidate = URL_SCHEME_PATTERN.test(trimmed) ? trimmed : `http://${trimmed}`;
  const parsed = new URL(candidate);

  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("invalid_url");
  }
  if (!parsed.hostname || !hasPublicHostname(parsed.hostname)) {
    throw new Error("invalid_url");
  }
  if (!parsed.pathname) {
    parsed.pathname = "/";
  }

  return parsed.toString();
}
