import {
  Chip,
  Divider,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import type { AssetDetail } from "../../../types";
import {
  type AssetDetailTab,
  AssetTimeline,
  MetadataValue,
} from "../shared";

export function DatasetDetail({
  detail,
  tab,
}: {
  detail: AssetDetail;
  tab: AssetDetailTab;
}) {
  const metadata = detail.metadata;
  const source = metadata.source ?? {};
  const quality = metadata.quality ?? {};
  const lineage = metadata.lineage ?? {};
  if (tab === "structure") {
    return (
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Schema & privacy classification</Typography>
        <Typography className="body-emphasis">Each field carries an explicit privacy class so ingestion and retrieval policies can enforce minimisation.</Typography>
        <Table size="small">
          <TableHead><TableRow><TableCell>Field</TableCell><TableCell>Type</TableCell><TableCell>Privacy</TableCell><TableCell>Nullable</TableCell></TableRow></TableHead>
          <TableBody>
            {(metadata.schema ?? []).map((field: any) => (
              <TableRow key={field.name}>
                <TableCell><strong>{field.name}</strong></TableCell><TableCell>{field.type}</TableCell>
                <TableCell><Chip size="small" variant="outlined" label={field.privacy.replaceAll("_", " ")} /></TableCell>
                <TableCell>{field.nullable ? "Yes" : "No"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    );
  }
  if (tab === "governance") {
    return (
      <div className="detail-grid">
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Quality evidence</Typography>
          <div className="metric-detail-grid">
            <MetadataValue label="Overall quality" value={`${quality.overall_score}%`} />
            <MetadataValue label="Completeness" value={`${quality.completeness}%`} />
            <MetadataValue label="Duplicate rate" value={`${quality.duplicate_rate}%`} />
            <MetadataValue label="Label agreement" value={`${quality.label_agreement}%`} />
            <MetadataValue label="Freshness" value={`${quality.freshness_days} days`} />
            <MetadataValue label="Last validation" value={new Date(quality.last_validation).toLocaleString()} />
          </div>
          <Divider />
          <Stack spacing={1}>
            {(metadata.controls ?? []).map((control: any) => (
              <div className="control-row" key={control.name}>
                <span className={control.status === "passed" ? "control-ok" : "control-attention"}>{control.status === "passed" ? "OK" : "!"}</span>
                <div><strong>{control.name}</strong><small>{control.status}</small></div>
              </div>
            ))}
          </Stack>
        </Paper>
        <Paper className="content-card">
          <Typography className="section-heading" variant="h6">Handling policy</Typography>
          <div className="metadata-grid top-gap">
            <MetadataValue label="Classification" value={metadata.classification} />
            <MetadataValue label="License" value={metadata.license} />
            <MetadataValue label="Retention" value={metadata.retention} />
          </div>
        </Paper>
      </div>
    );
  }
  if (tab === "activity") return <AssetTimeline detail={detail} />;
  return (
    <div className="detail-grid">
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Dataset contract</Typography>
        <Typography className="body-emphasis">{detail.asset.intended_use}</Typography>
        <div className="metric-detail-grid">
          <MetadataValue label="Source" value={source.system} />
          <MetadataValue label="Format" value={source.format} />
          <MetadataValue label="Records" value={Number(source.record_count).toLocaleString()} />
          <MetadataValue label="Refresh cadence" value={source.refresh_cadence} />
        </div>
      </Paper>
      <Paper className="content-card">
        <Typography className="section-heading" variant="h6">Lineage</Typography>
        {Object.entries(lineage).map(([key, values]) => (
          <div key={key}>
            <Typography className="subsection-heading">{key}</Typography>
            <Stack direction="row" gap={1} flexWrap="wrap">
              {(values as string[]).map((value) => <Chip size="small" variant="outlined" key={value} label={value} />)}
            </Stack>
          </div>
        ))}
      </Paper>
    </div>
  );
}
