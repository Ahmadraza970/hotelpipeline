import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Landing } from "./pages/Landing";
import { Workspace } from "./pages/Workspace";
import { Pricing } from "./pages/Pricing";
import { Leads } from "./pages/Leads";
import "./index.css";

const router = createBrowserRouter([
  { path: "/", element: <Landing /> },
  { path: "/workspace/:projectId", element: <Workspace /> },
  { path: "/pricing", element: <Pricing /> },
  { path: "/leads", element: <Leads /> },
  { path: "*", element: <Landing /> },
]);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
