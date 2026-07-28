import { type FormEvent, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import { registerAsset } from "../../api";
import { assetTypes } from "../../shared/assetCatalog";
import type { AssetType, NewAsset } from "../../types";

const initialAsset: NewAsset = {
  asset_id: "",
  version: "0.1.0",
  asset_type: "agent",
  display_name: "",
  owner: "",
  intended_use: "",
};

export function RegisterAssetDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [asset, setAsset] = useState<NewAsset>(initialAsset);
  const mutation = useMutation({
    mutationFn: registerAsset,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["assets"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
      setAsset(initialAsset);
      onClose();
    },
  });
  const valid = useMemo(() => Object.values(asset).every((value) => value.trim()), [asset]);
  function update<K extends keyof NewAsset>(key: K, value: NewAsset[K]) {
    setAsset((current) => ({ ...current, [key]: value }));
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    if (valid) mutation.mutate(asset);
  }
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <Box component="form" onSubmit={submit}>
        <DialogTitle className="strong-heading">Register governed asset</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>Create a versioned registry record attributed to your signed-in identity.</Typography>
          <Stack spacing={2}>
            {mutation.isError && <Alert severity="error">{mutation.error.message}</Alert>}
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField required fullWidth label="Asset ID" placeholder="agent.policy-risk" value={asset.asset_id} onChange={(event) => update("asset_id", event.target.value)} />
              <TextField required label="Version" value={asset.version} onChange={(event) => update("version", event.target.value)} />
            </Stack>
            <TextField required label="Display name" value={asset.display_name} onChange={(event) => update("display_name", event.target.value)} />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <FormControl fullWidth><InputLabel>Asset type</InputLabel><Select value={asset.asset_type} label="Asset type" onChange={(event) => update("asset_type", event.target.value as AssetType)}>{assetTypes.filter((type) => type.value !== "all").map((type) => <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>)}</Select></FormControl>
              <TextField required fullWidth label="Owner" value={asset.owner} onChange={(event) => update("owner", event.target.value)} />
            </Stack>
            <TextField required multiline minRows={3} label="Intended use" value={asset.intended_use} onChange={(event) => update("intended_use", event.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={onClose}>Cancel</Button><Button type="submit" variant="contained" disabled={!valid || mutation.isPending}>{mutation.isPending ? "Registering…" : "Register asset"}</Button></DialogActions>
      </Box>
    </Dialog>
  );
}
