import { Button, Chip, Stack } from "@mui/material";

import { authMode, useAuth } from "../auth";

export function Topbar() {
  const auth = useAuth();
  return (
    <div className="topbar">
      <span>Workspace / <strong>Enterprise AI</strong></span>
      <Stack direction="row" alignItems="center" spacing={1.2}>
        <Chip
          size="small"
          color="success"
          variant="outlined"
          label={`${authMode() === "keycloak" ? "Keycloak" : "Fixture"} · secured`}
        />
        <div className="user-summary">
          <strong>{auth.user?.display_name}</strong>
          <small>{auth.user?.roles.join(" · ")}</small>
        </div>
        <Button size="small" onClick={auth.logout}>Sign out</Button>
      </Stack>
    </div>
  );
}
