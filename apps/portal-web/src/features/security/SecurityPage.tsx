import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import { getMcpInvocations } from "../../api";
import { PageHeader } from "../../shared/components";
import { ControlLoading } from "../control/shared";

export function SecurityPage() {
  const invocations = useQuery({
    queryKey: ["mcp-invocations"],
    queryFn: getMcpInvocations,
  });
  if (invocations.isPending) return <ControlLoading />;
  if (invocations.isError) {
    return <Alert severity="error">{invocations.error.message}</Alert>;
  }
  return (
    <>
      <PageHeader
        eyebrow="Zero-trust tool access"
        title="MCP security boundary."
        description="Workflows never call privileged tools directly; the gateway evaluates identity, workflow, stage and human evidence."
      />
      <div className="detail-grid">
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Enforcement sequence</Typography>
          <div className="security-flow">
            {[
              ["01", "Verify identity", "Validate the Keycloak token and realm roles."],
              ["02", "Bind workflow context", "Require a registered run and declared stage for scoped tools."],
              ["03", "Evaluate tool policy", "Default deny; match the exact server, tool and role allowlist."],
              ["04", "Require human evidence", "Privileged mutations need an approved review at the same stage."],
              ["05", "Invoke and audit", "Forward through MCP and retain decision, arguments and result metadata."],
            ].map(([number, title, copy]) => (
              <div key={number}>
                <span>{number}</span>
                <div><strong>{title}</strong><p>{copy}</p></div>
              </div>
            ))}
          </div>
        </Paper>
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Registered policy</Typography>
          <div className="policy-table">
            <div><strong>lookup_access_policy</strong><Chip size="small" color="success" label="viewer+" /><small>Discovery; no run required</small></div>
            <div><strong>validate_entitlement</strong><Chip size="small" color="warning" label="operator+" /><small>policy-evaluation stage only</small></div>
            <div><strong>submit_access_decision</strong><Chip size="small" color="error" label="reviewer+" /><small>manager-approval + approved human review</small></div>
          </div>
        </Paper>
      </div>
      <Paper className="content-card" sx={{ mt: 2 }}>
        <Typography className="section-heading" variant="h6">Gateway decision audit</Typography>
        {!invocations.data.length ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            No gateway calls have been attempted in this database yet.
          </Alert>
        ) : (
          <Table size="small">
            <TableHead><TableRow><TableCell>Decision</TableCell><TableCell>Tool</TableCell><TableCell>Identity</TableCell><TableCell>Context</TableCell><TableCell>Reason</TableCell></TableRow></TableHead>
            <TableBody>
              {invocations.data.map((item) => (
                <TableRow key={item.request_id}>
                  <TableCell><Chip size="small" color={item.decision === "allowed" ? "success" : "error"} label={item.decision} /></TableCell>
                  <TableCell>{item.tool_name}</TableCell>
                  <TableCell>{item.actor_email}</TableCell>
                  <TableCell>{item.stage_id ?? "discovery"}</TableCell>
                  <TableCell>{item.reason}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>
    </>
  );
}
