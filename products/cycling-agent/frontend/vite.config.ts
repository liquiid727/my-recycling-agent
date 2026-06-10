/*
 * CN: Vite 配置，设置 React 插件、API 代理和 Vitest/jsdom 测试环境。
 * EN: Vite config for the React plugin, API proxy, and Vitest/jsdom test environment.
 */

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { resolveAmapJsKey } from "./vite.env";

export default defineConfig(({ mode }) => {
  const configDir = dirname(fileURLToPath(import.meta.url));
  const workspaceRoot = resolve(configDir, "../../..");
  const env = {
    ...loadEnv(mode, workspaceRoot, ""),
    ...loadEnv(mode, configDir, "")
  };
  const proxyTarget = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";
  const amapJsKey = mode === "test" ? "" : resolveAmapJsKey(env);

  return {
    plugins: [react()],
    define: {
      "import.meta.env.VITE_AMAP_JS_API_KEY": JSON.stringify(amapJsKey)
    },
    server: {
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true
        }
      }
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
      globals: true
    }
  };
});
