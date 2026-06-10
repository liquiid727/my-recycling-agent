/*
 * CN: 前端路由表，定义首页、结果页、路线详情、设置和后台页面。
 * EN: Frontend route table for home, result, route detail, settings, and admin pages.
 */

import { createBrowserRouter } from "react-router-dom";

import HomePage from "../pages/HomePage";
import AdminPage from "../pages/AdminPage";
import PlanResultPage from "../pages/PlanResultPage";
import RouteDetailPage from "../pages/RouteDetailPage";
import SettingsPage from "../pages/SettingsPage";

export const router = createBrowserRouter([
  { path: "/", element: <HomePage /> },
  { path: "/admin", element: <AdminPage /> },
  { path: "/plans/:requestNo", element: <PlanResultPage /> },
  { path: "/routes/:routeCode", element: <RouteDetailPage /> },
  { path: "/settings", element: <SettingsPage /> }
]);
