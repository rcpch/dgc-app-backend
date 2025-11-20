export type AuthData = {
    access_token: string;
    refresh_token: string;
    name: string;
    email: string;
}

export function getAuthData(): AuthData | undefined {
    const json = localStorage['auth_data'];
    if (!json) {
        return undefined;
    }

    return JSON.parse(json);
}

export function saveAuthData(data: AuthData) {
    localStorage['auth_data'] = JSON.stringify(data);
}

export function clearAuthData() {
    delete localStorage['auth_data'];
}