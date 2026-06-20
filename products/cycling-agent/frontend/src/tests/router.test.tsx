import { expect, test } from "vitest";

import { router } from "../app/router";

test("registers a dedicated planner route", () => {
  expect(router.routes.some((route) => route.path === "/planner")).toBe(true);
});
