import { useEffect, useState } from "react";

import { AssetDetailPage } from "./AssetDetailPage";
import { authMode, useAuth } from "./auth";
import { GovernancePage, RuntimePage, SecurityPage } from "./ControlPages";
import {
  type AssetFilter,
  type Page,
  type RouteState,
  routeFromLocation,
} from "./app/navigation";
import { AgentDetailPage } from "./features/assets/agent/AgentDetailPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { InventoryPage } from "./features/inventory/InventoryPage";
import { RegisterAssetDialog } from "./features/inventory/RegisterAssetDialog";
import { LoginScreen } from "./layout/LoginScreen";
import { Sidebar } from "./layout/Sidebar";
import { Topbar } from "./layout/Topbar";
import type { Asset } from "./types";

export function App() {
  const auth = useAuth();
  const [route, setRoute] = useState<RouteState>(routeFromLocation);
  const [assetFilter, setAssetFilter] = useState<AssetFilter>("all");
  const [registerOpen, setRegisterOpen] = useState(false);

  useEffect(() => {
    const onPopState = () => setRoute(routeFromLocation());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  function navigate(page: Page) {
    window.history.pushState({}, "", page === "overview" ? "/" : `/${page}`);
    setRoute({ page });
  }

  function chooseAssetFilter(type: AssetFilter) {
    setAssetFilter(type);
    window.history.pushState({}, "", "/inventory");
    setRoute({ page: "inventory" });
  }

  function openAsset(asset: Asset) {
    window.history.pushState(
      {},
      "",
      `/assets/${asset.asset_type}/${encodeURIComponent(asset.asset_id)}/versions/${encodeURIComponent(asset.version)}`,
    );
    setAssetFilter(asset.asset_type);
    setRoute({
      page: asset.asset_type === "agent" ? "agent" : "asset",
      assetId: asset.asset_id,
      version: asset.version,
    });
  }

  if (auth.loading || !auth.authenticated) return <LoginScreen />;

  return (
    <div className="app-shell" data-auth-mode={authMode()}>
      <Sidebar
        page={route.page}
        assetFilter={assetFilter}
        onNavigate={navigate}
        onAssetFilter={chooseAssetFilter}
      />
      <main>
        <Topbar />
        <div className="page-content">
          {route.page === "overview" && (
            <DashboardPage onRegister={() => setRegisterOpen(true)} />
          )}
          {route.page === "inventory" && (
            <InventoryPage
              assetFilter={assetFilter}
              onFilter={chooseAssetFilter}
              onRegister={() => setRegisterOpen(true)}
              onOpen={openAsset}
            />
          )}
          {route.page === "agent" && route.assetId && route.version && (
            <AgentDetailPage
              assetId={route.assetId}
              version={route.version}
              onBack={() => chooseAssetFilter("agent")}
            />
          )}
          {route.page === "asset" && route.assetId && route.version && (
            <AssetDetailPage
              assetId={route.assetId}
              version={route.version}
              onBack={chooseAssetFilter}
            />
          )}
          {route.page === "lifecycle" && <GovernancePage />}
          {route.page === "runtime" && <RuntimePage />}
          {route.page === "security" && <SecurityPage />}
        </div>
      </main>
      <RegisterAssetDialog
        open={registerOpen}
        onClose={() => setRegisterOpen(false)}
      />
    </div>
  );
}
