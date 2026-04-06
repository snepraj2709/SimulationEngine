import { createBrowserRouter } from "react-router-dom";

import { AuthGuard } from "@/components/auth/AuthGuard";
import { AnalysisResultPage } from "@/pages/AnalysisResultPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { LandingPage } from "@/pages/LandingPage";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { ScenarioComparisonPage } from "@/pages/ScenarioComparisonPage";

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    path: "/dashboard",
    element: (
      <AuthGuard>
        <DashboardPage />
      </AuthGuard>
    ),
  },
  {
    path: "/analyses/:analysisId",
    element: (
      <AuthGuard>
        <AnalysisResultPage />
      </AuthGuard>
    ),
  },
  {
    path: "/analyses/:analysisId/scenarios/compare",
    element: (
      <AuthGuard>
        <ScenarioComparisonPage />
      </AuthGuard>
    ),
  },
]);
