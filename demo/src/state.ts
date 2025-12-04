import { createContext } from "preact";
import { AuthData, clearAuthData, getAuthData } from "./auth";
import { useContext } from "preact/hooks";
import { signal, Signal } from "@preact/signals";
import { useLocation } from "preact-iso";
import { getOrganisations, Organisation, Child, ExpandedChild, getChildren, addChild, Observation, addObservation } from "./api";

export type AppState = {
  authData: Signal<AuthData | undefined>;
  organisations: Signal<Organisation[]>;
  children: Signal<ExpandedChild[]>;
  addChild: (organisationId: string, name: string, date_of_birth: string) => Promise<void>;
  addObservation: (childId: string, observation: Observation) => Promise<void>;
  refetchChildren: () => Promise<void>;
  logout: () => void;
}

export function createAppState(): AppState {
  const authData = signal<AuthData | undefined>(getAuthData());
  const organisations = signal<Organisation[]>([]);
  const children = signal<ExpandedChild[]>([]);

  // TODO MRB: catch errors
  if(authData.value?.access_token) {
    getOrganisations().then(orgs => organisations.value = orgs);
    getChildren().then(chs => children.value = chs);
  }

  return {
    authData: authData,
    organisations: organisations,
    children: children,
    addChild: async (organisationId: string, name: string, date_of_birth: string) => {
      const child = {
        ...await addChild(organisationId, name, date_of_birth),
        organisation_ids: [organisationId],
        observations: []
      };

      children.value = [...children.value, child];
    },
    addObservation: async (childId: string, observation: Observation) => {
      await addObservation(childId, observation);
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