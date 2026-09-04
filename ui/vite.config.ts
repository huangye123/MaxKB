import {fileURLToPath, URL} from 'node:url'
import type {ProxyOptions} from 'vite'
import {defineConfig, loadEnv} from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import DefineOptions from 'unplugin-vue-define-options/vite'
import path from 'path'
import {createHtmlPlugin} from 'vite-plugin-html'
import fs from 'fs'
// import vueDevTools from 'vite-plugin-vue-devtools'
const envDir = './env'
const backendTarget = 'http://127.0.0.1:8080'
const devHistoryFallbackPlugin = (basePath: string, entry: string) => {
  const normalizedBasePath = basePath.endsWith('/') ? basePath : `${basePath}/`
  return {
    name: 'dev-history-fallback',
    configureServer(server: any) {
      server.middlewares.use(async (req: any, res: any, next: any) => {
        const url = req.url?.split('?')[0] || '/'
        if (
          req.method !== 'GET' ||
          !url.startsWith(normalizedBasePath) ||
          url.startsWith(`${normalizedBasePath}api`) ||
          url.includes('/oss/')
        ) {
          next()
          return
        }

        try {
          const entryPath = path.resolve(__dirname, entry)
          const html = fs.readFileSync(entryPath, 'utf-8')
          const transformedHtml = await server.transformIndexHtml(url, html)
          res.statusCode = 200
          res.setHeader('Content-Type', 'text/html')
          res.end(transformedHtml)
        } catch (error) {
          next(error)
        }
      })
    },
  }
}
const renameHtmlPlugin = (outDir: string, entry: string) => {
  return {
    name: 'rename-html',
    closeBundle: () => {
      const buildDir = path.resolve(__dirname, outDir)
      const oldFile = path.join(buildDir, entry)
      const newFile = path.join(buildDir, 'index.html')

      if (fs.existsSync(oldFile)) {
        if (fs.existsSync(newFile)) {
          fs.unlinkSync(newFile)
        }
        fs.renameSync(oldFile, newFile)
      }
    },
  }
}
// https://vite.dev/config/
export default defineConfig((conf: any) => {
  const mode = conf.mode
  const ENV = loadEnv(mode, envDir)
  const proxyConf: Record<string, string | ProxyOptions> = {}
  proxyConf['/admin/api'] = {
    target: backendTarget,
    changeOrigin: true,
  }
  proxyConf['/chat/api'] = {
    target: backendTarget,
    changeOrigin: true,
  }
  proxyConf['/doc'] = {
    target: backendTarget,
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }
  proxyConf['/schema'] = {
    target: backendTarget,
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }
  proxyConf['/static'] = {
    target: backendTarget,
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }

  // Proxy static OSS resources to the backend.
  proxyConf[`^${ENV.VITE_BASE_PATH}.+\/oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  // Proxy static OSS resources to the backend.
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/get_url\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  // Proxy static OSS resources to the backend.
  return {
    preflight: false,
    lintOnSave: false,
    base: './',
    envDir: envDir,
    plugins: [
      vue(),
      vueJsx(),
      DefineOptions(),
      createHtmlPlugin({template: ENV.VITE_ENTRY}),
      devHistoryFallbackPlugin(ENV.VITE_BASE_PATH, ENV.VITE_ENTRY),
      renameHtmlPlugin(`dist${ENV.VITE_BASE_PATH}`, ENV.VITE_ENTRY),
    ],
    server: {
      cors: true,
      host: '0.0.0.0',
      port: Number(ENV.VITE_APP_PORT),
      strictPort: true,
      proxy: proxyConf,
    },
    build: {
      outDir: `dist${ENV.VITE_BASE_PATH}`,
      target: 'es2022',
      rollupOptions: {
        input: ENV.VITE_ENTRY,
      },
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
