import { Button, CircularProgress, Paper, Typography } from "@mui/material";

import { useAuth } from "../auth";

export function LoginScreen() {
  const auth = useAuth();
  if (auth.loading) {
    return <div className="login-shell"><CircularProgress /></div>;
  }
  return (
    <div className="login-shell">
      <Paper className="login-card">
        <span className="brand-mark large">NS</span>
        <Typography className="strong-heading" variant="h3">
          Govern every AI decision.
        </Typography>
        <Typography color="text.secondary">
          Sign in to inspect assets, evidence, lifecycle decisions and runtime
          accountability.
        </Typography>
        <Button variant="contained" size="large" onClick={() => void auth.login()}>
          Sign in with Keycloak
        </Button>
        <div className="login-note">
          <strong>Local demonstration</strong>
          <span>admin@northstar.local / northstar</span>
        </div>
      </Paper>
    </div>
  );
}
