import { createContext } from "preact";
import { AuthData, clearAuthData, getAuthData } from "./auth";
import { useContext } from "preact/hooks";
import { signal, Signal } from "@preact/signals";

type AppState = {
  authData: Signal<AuthData | undefined>;
  logout: () => void;
}

export function createAppState(): AppState {
  const authData = signal<AuthData | undefined>(getAuthData());

  return {
    authData: authData,
    logout: () => {
      authData.value = undefined;
      clearAuthData();
    }
  };
}

export const AppStateCtx = createContext<AppState>(createAppState());

export const useAppState = () => {
  return useContext(AppStateCtx);
};