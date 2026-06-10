/*
 * CN: Vite 环境变量解析，避免把整组非 VITE 变量暴露给前端。
 * EN: Vite env helpers without exposing all non-VITE variables.
 */

type EnvMap = Record<string, string | undefined>;

export function resolveAmapJsKey(env: EnvMap): string {
  return env.VITE_AMAP_JS_API_KEY || "";
}
