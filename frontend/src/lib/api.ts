const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://192.168.1.153:8009';

type FetchOptions = RequestInit & { authToken?: string };

export async function apiFetch<TResponse>(
  path: string,
  { authToken, headers, ...init }: FetchOptions = {}
): Promise<TResponse> {
  const request = new Request(new URL(path, API_BASE_URL), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(headers ?? {}),
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    },
    credentials: 'omit',
  });

  const response = await fetch(request);

  if (!response.ok) {
    const text = await response.text();
    const message = parseErrorMessage(text) ?? response.statusText;
    const error = new Error(message);
    (error as Error & { status?: number }).status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return response.json() as Promise<TResponse>;
}

function parseErrorMessage(payload: string) {
  if (!payload) {
    return null;
  }
  try {
    const data = JSON.parse(payload);
    if (typeof data.detail === 'string') {
      return data.detail;
    }
    if (Array.isArray(data.detail) && data.detail.length > 0) {
      const first = data.detail[0];
      if (typeof first?.msg === 'string') {
        return first.msg;
      }
    }
  } catch {
    /* ignore malformed JSON */
  }
  return payload;
}

export type AuthTokens = {
  access_token: string;
  refresh_token?: string | null;
  token_type: string;
  expires_in: number;
};

export type UserProfile = {
  user_id: number;
  username: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
};

