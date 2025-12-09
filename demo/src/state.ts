import { createContext } from "preact";
import { AuthData, clearAuthData, getAuthData } from "./auth";
import { useContext } from "preact/hooks";
import { signal, Signal } from "@preact/signals";
import { useLocation } from "preact-iso";
import { getOrganisations, Organisation, Child, getChildren, addChild } from "./api";

export type AppState = {
  authData: Signal<AuthData | undefined>;
  organisations: Signal<Organisation[]>;
  children: Signal<Child[]>;
  addChild: (organisationId: string, child: Omit<Child, 'id' | 'organisation_ids'>) => Promise<void>;
  refetchChildren: () => Promise<void>;
  logout: () => void;
}

export function createAppState(): AppState {
  const authData = signal<AuthData | undefined>(getAuthData());
  const organisations = signal<Organisation[]>([]);
  const children = signal<Child[]>([]);

  // TODO MRB: catch errors
  if(authData.value?.access_token) {
    getOrganisations().then(orgs => organisations.value = orgs);
    getChildren().then(chs => children.value = chs);
  }

  return {
    authData: authData,
    organisations: organisations,
    children: children,
    addChild: async (organisationId: string, child: Omit<Child, 'id' | 'organisation_ids'>) => {
      const newChild = await addChild(organisationId, child);
      newChild.organisation_ids = [organisationId];

      children.value = [...children.value, newChild];
    },
    refetchChildren: async () => {
      children.value = await getChildren();
    },
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