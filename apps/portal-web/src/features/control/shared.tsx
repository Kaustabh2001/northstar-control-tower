import { useState } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  LinearProgress,
  Paper,
  TextField,
  Typography,
} from "@mui/material";

export function ControlLoading() {
  return (
    <Paper className="loading-panel">
      <LinearProgress sx={{ width: 220 }} />
    </Paper>
  );
}

export function DecisionDialog({
  title,
  open,
  pending,
  onClose,
  onSubmit,
}: {
  title: string;
  open: boolean;
  pending: boolean;
  onClose: () => void;
  onSubmit: (note: string) => void;
}) {
  const [note, setNote] = useState("");
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle className="strong-heading">{title}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" mb={2}>
          This rationale is retained with the accountable identity and decision.
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={3}
          label="Decision rationale"
          value={note}
          onChange={(event) => setNote(event.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          disabled={note.trim().length < 3 || pending}
          onClick={() => onSubmit(note)}
        >
          Record decision
        </Button>
      </DialogActions>
    </Dialog>
  );
}
