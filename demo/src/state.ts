import { createContext } from "preact";
import { AuthData, clearAuthData, getAuthData } from "./auth";
import { useContext } from "preact/hooks";
import { signal, Signal } from "@preact/signals";
import { useLocation } from "preact-iso";
import { getOrganisations, Organisation } from "./api";

export type AppState = {
  authData: Signal<AuthData | undefined>;
  organisations: Signal<Organisation[]>;
  logout: () => void;
}

export function createAppState(): AppState {
  const authData = signal<AuthData | undefined>(getAuthData());
  const organisations = signal<Organisation[]>([]);

  // TODO MRB: catch errors
  if(authData.value?.access_token) {
    getOrganisations().then(orgs => organisations.value = orgs);
  }

  return {
    authData: authData,
    organisations: organisations,
    logout: () => {
      authData.value = undefined;
      clearAuthData();
    }
  };
}

// @ts-ignore
export const AppStateCtx = createContext<AppState>();

export const useAppState = () => {
  return useContext(AppStateCtx);
};

export const useLoggedInAppState = (): AppState => {
  const { route } = useLocation();
  const appState = useAppState();

  if (!appState.authData.value) {
    route("/demo/login");
  }

  return appState;
}