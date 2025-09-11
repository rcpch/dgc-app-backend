import { defineConfig } from 'vite';

export default defineConfig({
   base: '/demo/',
   plugins: [
        {
      name: 'requestLogger',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
          next();
        });
      },
    },
   ]
});