import type { AppState } from '../state';

export function Nav({ appState }: { appState: AppState }) {
    return <nav>
        <ul>
            <li><strong>dgc-app backend </strong></li>
        </ul>
        <ul>
            {appState.authData.value ?
                <>
                    <li><a href="#">Patients</a></li>
                    <li><a href="/demo/organisations">Organisations</a></li>
                    <li>|</li>
                    <li>{appState.authData.value.email}</li>
                    <li><a href="#" onClick={() => appState.logout()}>Logout</a></li>
                </>
            : ''}
        </ul>
    </nav>;
}