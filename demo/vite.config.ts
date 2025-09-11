import { defineConfig } from 'vite';

export default defineConfig({
   base: '/demo/',
   build: {
    rollupOptions: {
        input: {
            main: 'demo/index.html',
            oauthCallback: 'demo/oauth-callback.html'
        }
    }
   }
});