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
// 自定义插件：重命名入口文件
const devProfileLicenseOverlayPlugin = (enabled: boolean) => {
  return {
    name: 'dev-profile-license-overlay',
    configureServer(server: any) {
      server.middlewares.use(async (req: any, res: any, next: any) => {
        const url = req.url?.split('?')[0] || '/'
        if (!enabled || req.method !== 'GET' || url !== '/admin/api/profile') {
          next()
          return
        }

        try {
          const upstream = await fetch(`${backendTarget}${req.url}`)
          const body = await upstream.json()
          const data = {
            ...body,
            data: {
              ...(body.data || {}),
              edition: 'PE',
              license_is_valid: true,
            },
          }

          res.statusCode = upstream.status
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify(data))
        } catch (error) {
          next(error)
        }
      })
    },
  }
}
const adminApiMockPlugin = () => {
  return {
    name: 'admin-api-mock-response',
    configureServer(server: any) {
      server.middlewares.use((req: any, res: any, next: any) => {
        const url = req.url?.split('?')[0] || '/'
        if (req.method !== 'GET') {
          next()
          return
        }

        const responses: Record<string, unknown> = {
          '/admin/api/display/info': {
            code: 200,
            message: '\u6210\u529f',
            data: {
              theme: '#3370FF',
              icon: '',
              loginLogo: '',
              loginImage: '',
              title: 'MaxKB',
              slogan: '\u5f3a\u5927\u6613\u7528\u7684\u4f01\u4e1a\u7ea7\u667a\u80fd\u4f53\u5e73\u53f0',
              showUserManual: true,
              userManualUrl: 'https://maxkb.cn/docs/v2/',
              showForum: true,
              forumUrl: 'https://bbs.fit2cloud.com/c/mk/11',
              showProject: true,
              projectUrl: 'https://github.com/1Panel-dev/MaxKB',
            },
          },
          '/admin/api/user/profile': JSON.parse(String.raw`{
            "code": 200,
            "message": "\u6210\u529f",
            "data": {
              "id": "f0dd8f71-e4ee-11ee-8c84-a8a1595801ab",
              "username": "admin",
              "nick_name": "\u7cfb\u7edf\u7ba1\u7406\u5458",
              "email": "",
              "source": "LOCAL",
              "role": [
                "USER",
                "ADMIN",
                "USER:/WORKSPACE/default",
                "WORKSPACE_MANAGE",
                "WORKSPACE_MANAGE:/WORKSPACE/default"
              ],
              "permissions": [
                "APPLICATION_CHAT_LOG:READ+EXPORT:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION_OVERVIEW:READ+API_KEY:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION_CHAT_LOG:READ+CLEAR_POLICY:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION:READ:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_DOCUMENT:READ+DOWNLOAD:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL:READ+RELATE_VIEW:/WORKSPACE/default/TOOL/default",
                "APPLICATION_OVERVIEW:READ+EMBED:/WORKSPACE/default/APPLICATION/default",
                "TOOL:READ+RECORD:/WORKSPACE/default/TOOL/default",
                "KNOWLEDGE_TAG:READ+EDIT:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION_ACCESS:READ:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE:READ+RELATE_VIEW:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_FOLDER:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION_FOLDER:READ+DELETE:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_FOLDER:READ+CREATE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_PROBLEM:READ+EDIT:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION:READ+TRIGGER_READ:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_DOCUMENT:READ+TAG:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_DOCUMENT:READ+CREATE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_DOCUMENT:READ+SYNC:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL_FOLDER:READ+DELETE:/WORKSPACE/default/TOOL/default",
                "TOOL:READ+BATCH_DELETE:/WORKSPACE/default/TOOL/default",
                "APPLICATION:READ+TRIGGER_DELETE:/WORKSPACE/default/APPLICATION/default",
                "TOOL_FOLDER:READ+CREATE:/WORKSPACE/default/TOOL/default",
                "KNOWLEDGE_TAG:READ+DELETE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE:READ+SYNC:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION_FOLDER:READ+AUTH:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_PROBLEM:READ+CREATE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE:READ+VECTOR:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_DOCUMENT:READ+REPLACE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_PROBLEM:READ+DELETE:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION_CHAT_LOG:READ:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION:READ+CREATE:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE:READ+DELETE:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION:READ+IMPORT:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION:READ+AUTH:/WORKSPACE/default/APPLICATION/default",
                "TOOL:READ+TRIGGER_CREATE:/WORKSPACE/default/TOOL/default",
                "KNOWLEDGE_WORKFLOW:READ+EXPORT:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_CHAT_USER:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION:READ+BATCH_MOVE:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_FOLDER:READ+AUTH:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_DOCUMENT:READ+VECTOR:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_CHAT_USER:READ+EDIT:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_HIT_TEST:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_FOLDER:READ+DELETE:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL_FOLDER:READ:/WORKSPACE/default/TOOL/default",
                "APPLICATION_ACCESS:READ+EDIT:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION_FOLDER:READ+CREATE:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_WORKFLOW:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_WORKFLOW:READ+PUBLISH:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL:READ+AUTH:/WORKSPACE/default/TOOL/default",
                "KNOWLEDGE:READ+GENERATE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_DOCUMENT:READ+GENERATE:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION:READ+EDIT:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_PROBLEM:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION_CHAT_USER:READ+EDIT:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_DOCUMENT:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL:READ+BATCH_MOVE:/WORKSPACE/default/TOOL/default",
                "TOOL:READ+IMPORT:/WORKSPACE/default/TOOL/default",
                "KNOWLEDGE_DOCUMENT:READ+DELETE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE:READ+AUTH:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_DOCUMENT:READ+EDIT:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION_FOLDER:READ+EDIT:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_TAG:READ+CREATE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_DOCUMENT:READ+MIGRATE:/WORKSPACE/default/KNOWLEDGE/default",
                "APPLICATION:READ+RELATE_VIEW:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION:READ+PUBLISH:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION:READ+BATCH_DELETE:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION_FOLDER:READ:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION:READ+EXPORT:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION_OVERVIEW:READ+PUBLIC_ACCESS:/WORKSPACE/default/APPLICATION/default",
                "TOOL:READ+DELETE:/WORKSPACE/default/TOOL/default",
                "APPLICATION:READ+TRIGGER_CREATE:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION_CHAT_LOG:READ+ANNOTATION:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION_OVERVIEW:READ+DISPLAY:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE:READ+EXPORT:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL:READ+EDIT:/WORKSPACE/default/TOOL/default",
                "KNOWLEDGE:READ+CREATE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_PROBLEM:READ+RELATE:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL_FOLDER:READ+EDIT:/WORKSPACE/default/TOOL/default",
                "APPLICATION_CHAT_USER:READ:/WORKSPACE/default/APPLICATION/default",
                "TOOL:READ+TRIGGER_READ:/WORKSPACE/default/TOOL/default",
                "APPLICATION_CHAT_LOG:READ+ADD_KNOWLEDGE:/WORKSPACE/default/APPLICATION/default",
                "APPLICATION_OVERVIEW:READ:/WORKSPACE/default/APPLICATION/default",
                "TOOL:READ:/WORKSPACE/default/TOOL/default",
                "KNOWLEDGE:READ+BATCH_DELETE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE:READ+EDIT:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE:READ+BATCH_MOVE:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_TAG:READ:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL:READ+CREATE:/WORKSPACE/default/TOOL/default",
                "APPLICATION:READ+TRIGGER_EDIT:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_FOLDER:READ+EDIT:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL:READ+EXPORT:/WORKSPACE/default/TOOL/default",
                "TOOL:READ+TRIGGER_EDIT:/WORKSPACE/default/TOOL/default",
                "APPLICATION_OVERVIEW:READ+ACCESS:/WORKSPACE/default/APPLICATION/default",
                "TOOL_FOLDER:READ+AUTH:/WORKSPACE/default/TOOL/default",
                "APPLICATION:READ+DELETE:/WORKSPACE/default/APPLICATION/default",
                "KNOWLEDGE_DOCUMENT:READ+EXPORT:/WORKSPACE/default/KNOWLEDGE/default",
                "KNOWLEDGE_WORKFLOW:READ+EDIT:/WORKSPACE/default/KNOWLEDGE/default",
                "TOOL:READ+TRIGGER_DELETE:/WORKSPACE/default/TOOL/default",
                "TOOL:READ+PUBLISH:/WORKSPACE/default/TOOL/default"
              ],
              "is_edit_password": false,
              "language": null,
              "workspace_list": [
                {
                  "id": "default",
                  "name": "default"
                }
              ],
              "role_name": [
                "\u7cfb\u7edf\u7ba1\u7406\u5458",
                "\u666e\u901a\u7528\u6237",
                "\u5de5\u4f5c\u7a7a\u95f4\u7ba1\u7406\u5458"
              ]
            }
          }`),
          '/admin/api/workspace/default/APPLICATION/folder': {
            code: 200,
            message: '\u6210\u529f',
            data: [
              {
                id: 'default',
                name: 'default',
                desc: '',
                parent_id: null,
                type: 'folder',
                children: [],
              },
            ],
          },
          '/admin/api/workspace/default/application/1/30': {
            code: 200,
            message: '\u6210\u529f',
            data: {
              total: 0,
              records: [],
            },
          },
        }

        const body = responses[url]
        if (!body) {
          next()
          return
        }

        res.statusCode = 200
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify(body))
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

      // 检查文件是否存在
      if (fs.existsSync(oldFile)) {
        // 删除已存在的 index.html
        if (fs.existsSync(newFile)) {
          fs.unlinkSync(newFile)
        }
        // 重命名文件
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

  // 前端静态资源转发到本身
  proxyConf[`^${ENV.VITE_BASE_PATH}.+\/oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  // 前端静态资源转发到本身
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/file\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  proxyConf[`^${ENV.VITE_BASE_PATH}oss\/get_url\/.*$`] = {
    target: `http://127.0.0.1:8080`,
    changeOrigin: true,
  }
  // 前端静态资源转发到本身
  proxyConf[ENV.VITE_BASE_PATH] = {
    target: `http://127.0.0.1:${ENV.VITE_APP_PORT}`,
    changeOrigin: true,
    rewrite: (path: string) => path.replace(ENV.VITE_BASE_PATH, '/'),
  }

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
      devProfileLicenseOverlayPlugin(ENV.VITE_DEV_UI_MOCK_LICENSE === 'true'),
      adminApiMockPlugin(),
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
