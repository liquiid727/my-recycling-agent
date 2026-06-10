/*
 * CN: React 前端入口，挂载 RouterProvider 并加载全局样式。
 * EN: React frontend entrypoint that mounts RouterProvider and global styles.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import { router } from "./app/router";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
