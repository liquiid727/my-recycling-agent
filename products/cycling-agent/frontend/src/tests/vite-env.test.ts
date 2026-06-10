/*
 * CN: Vite 环境变量解析测试，保护高德 JS Key 的唯一前端变量口径。
 * EN: Vite env resolution tests for the single frontend AMap JS key variable.
 */

import { describe, expect, test } from "vitest";

import { resolveAmapJsKey } from "../../vite.env";

describe("resolveAmapJsKey", () => {
  test("returns explicit frontend amap js key", () => {
    expect(resolveAmapJsKey({ VITE_AMAP_JS_API_KEY: "vite-key", OTHER_MAP_KEY: "web-key" })).toBe("vite-key");
  });

  test("does not expose non-vite amap keys", () => {
    expect(resolveAmapJsKey({ OTHER_MAP_KEY: "web-key" })).toBe("");
  });
});
