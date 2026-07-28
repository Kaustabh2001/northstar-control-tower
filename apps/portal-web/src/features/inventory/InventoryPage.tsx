import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import { getAssets } from "../../api";
import type { AssetFilter } from "../../app/navigation";
import { assetTypes, typeLabels } from "../../shared/assetCatalog";
import { LoadingPanel, PageHeader, StatusChip } from "../../shared/components";
import type { Asset } from "../../types";

export function InventoryPage({
  assetFilter,
  onFilter,
  onRegister,
  onOpen,
}: {
  assetFilter: AssetFilter;
  onFilter: (value: AssetFilter) => void;
  onRegister: () => void;
  onOpen: (asset: Asset) => void;
}) {
  const [query, setQuery] = useState("");
  const assets = useQuery({
    queryKey: ["assets", assetFilter, query],
    queryFn: () => getAssets(assetFilter, query),
  });
  return (
    <>
      <PageHeader
        eyebrow="Governed portfolio"
        title={assetFilter === "all" ? "All AI assets" : assetTypes.find((type) => type.value === assetFilter)!.label}
        description="Open any version to inspect its contract, evidence, controls, lineage and decisions."
        action={<Button variant="contained" onClick={onRegister}>Register asset</Button>}
      />
      <Paper className="content-card">
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.5} mb={2}>
          <TextField size="small" fullWidth label="Search name, ID or owner" value={query} onChange={(event) => setQuery(event.target.value)} />
          <FormControl size="small" sx={{ minWidth: 210 }}>
            <InputLabel>Asset type</InputLabel>
            <Select value={assetFilter} label="Asset type" onChange={(event) => onFilter(event.target.value as AssetFilter)}>
              {assetTypes.map((type) => <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>)}
            </Select>
          </FormControl>
        </Stack>
        {assets.isError && <Alert severity="error">{assets.error.message}</Alert>}
        {assets.isPending ? <LoadingPanel /> : (
          <TableContainer>
            <Table size="small">
              <TableHead><TableRow><TableCell>Asset</TableCell><TableCell>Type</TableCell><TableCell>Governance state</TableCell><TableCell>Risk</TableCell><TableCell>Owner</TableCell><TableCell>Updated</TableCell></TableRow></TableHead>
              <TableBody>
                {assets.data?.map((asset) => (
                  <TableRow
                    key={`${asset.asset_id}:${asset.version}`}
                    hover
                    className="clickable-row"
                    tabIndex={0}
                    onClick={() => onOpen(asset)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") onOpen(asset);
                    }}
                  >
                    <TableCell><div className="asset-name"><span>{assetTypes.find((type) => type.value === asset.asset_type)?.mark}</span><div><strong>{asset.display_name}</strong><small>{asset.asset_id} · {asset.version}</small></div></div></TableCell>
                    <TableCell><strong>{typeLabels[asset.asset_type]}</strong></TableCell>
                    <TableCell><StatusChip asset={asset} /></TableCell>
                    <TableCell><Chip size="small" variant="outlined" label={asset.risk_level} sx={{ textTransform: "capitalize", fontWeight: 700 }} /></TableCell>
                    <TableCell>{asset.owner}</TableCell>
                    <TableCell>{new Date(asset.updated_at).toLocaleDateString()}</TableCell>
                  </TableRow>
                ))}
                {!assets.data?.length && <TableRow><TableCell colSpan={6}><Typography color="text.secondary" textAlign="center" py={4}>No assets match this filter.</Typography></TableCell></TableRow>}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </>
  );
}
