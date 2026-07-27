import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import type { SessionUser } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const AUTH_MODE = import.meta.env.VITE_AUTH_MODE ?? "fixture";
const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL ?? "http://localhost:8080";
const REALM = "northstar";
const CLIENT_ID = "northstar-portal";
const TOKEN_KEY = "northstar.tokens";
const VERIFIER_KEY = "northstar.pkce.verifier";
const STATE_KEY = "northstar.oidc.state";

interface TokenSet {
  access_token: string;
  refresh_token?: string;
  id_token?: string;
  expires_in?: number;
}

interface AuthContextValue {
  loading: boolean;
  authenticated: boolean;
  user: SessionUser | null;
  login: () => Promise<void>;
  logout: () => void;
  hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function encode(bytes: Uint8Array): string {
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

function randomValue(): string {
  return encode(crypto.getRandomValues(new Uint8Array(32)));
}

function readTokens(): TokenSet | null {
  const value = sessionStorage.getItem(TOKEN_KEY);
  return value ? (JSON.parse(value) as TokenSet) : null;
}

export function getAccessToken(): string | null {
  if (AUTH_MODE === "fixture") return "fixture-admin";
  return readTokens()?.access_token ?? null;
}

async function exchangeCode(code: string): Promise<void> {
  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  if (!verifier) throw new Error("The sign-in verifier is missing. Please sign in again.");
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CLIENT_ID,
    code,
    code_verifier: verifier,
    redirect_uri: `${window.location.origin}/`,
  });
  const response = await fetch(
    `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`,
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    },
  );
  if (!response.ok) throw new Error("Keycloak could not complete sign-in.");
  sessionStorage.setItem(TOKEN_KEY, JSON.stringify(await response.json()));
  sessionStorage.removeItem(VERIFIER_KEY);
  sessionStorage.removeItem(STATE_KEY);
}

async function beginLogin(): Promise<void> {
  if (AUTH_MODE === "fixture") return;
  const verifier = randomValue();
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(verifier),
  );
  const state = randomValue();
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  sessionStorage.setItem(STATE_KEY, state);
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    redirect_uri: `${window.location.origin}/`,
    response_type: "code",
    scope: "openid profile email",
    state,
    code_challenge: encode(new Uint8Array(digest)),
    code_challenge_method: "S256",
  });
  window.location.assign(
    `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/auth?${params}`,
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<SessionUser | null>(null);

  const loadUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    const response = await fetch(`${API_BASE}/api/v1/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      sessionStorage.removeItem(TOKEN_KEY);
      setUser(null);
      setLoading(false);
      return;
    }
    setUser((await response.json()) as SessionUser);
    setLoading(false);
  }, []);

  useEffect(() => {
    async function initialise() {
      try {
        const params = new URLSearchParams(window.location.search);
        const code = params.get("code");
        const state = params.get("state");
        if (code) {
          if (state !== sessionStorage.getItem(STATE_KEY)) {
            throw new Error("The sign-in state did not match.");
          }
          await exchangeCode(code);
          window.history.replaceState({}, "", "/");
        }
        await loadUser();
      } catch {
        sessionStorage.removeItem(TOKEN_KEY);
        setUser(null);
        setLoading(false);
      }
    }
    void initialise();
  }, [loadUser]);

  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    setUser(null);
    if (AUTH_MODE === "keycloak") {
      const params = new URLSearchParams({
        client_id: CLIENT_ID,
        post_logout_redirect_uri: `${window.location.origin}/`,
      });
      window.location.assign(
        `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/logout?${params}`,
      );
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      loading,
      authenticated: Boolean(user),
      user,
      login: beginLogin,
      logout,
      hasRole: (...roles) => Boolean(user?.roles.some((role) => roles.includes(role))),
    }),
    [loading, logout, user],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}

export function authMode(): string {
  return AUTH_MODE;
}
