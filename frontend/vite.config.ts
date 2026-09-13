
  import { defineConfig, loadEnv } from 'vite';
  import react from '@vitejs/plugin-react-swc';
  import tailwindcss from '@tailwindcss/vite';
  import path from 'path';

  export default defineConfig(({ mode }) => {
    // Load env file based on `mode` in the current working directory.
    const env = loadEnv(mode, process.cwd(), '');
    
    return {
    plugins: [react(), tailwindcss()],
    resolve: {
      extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    build: {
      target: 'esnext',
      outDir: 'build',
    },
    server: {
      port: 3000,
      open: true,
      host: true, // Allow access from network
      allowedHosts: [
        'localhost',
        '.ngrok-free.dev', // Allow all ngrok domains
        '.ngrok.io',
        '.ngrok.app',
      ],
    },
    // Explicitly define env variables to expose to the client
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || 'http://127.0.0.1:8000/api'),
    },
  };
  });