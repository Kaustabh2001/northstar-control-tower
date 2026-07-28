import { Button, Chip, Paper, Stack, Typography } from "@mui/material";

import { useAuth } from "../../auth";
import type { HumanReview } from "../../types";

export function HumanReviewPanel({
  reviews,
  onDecision,
}: {
  reviews: HumanReview[];
  onDecision: (review: HumanReview, value: "approve" | "reject") => void;
}) {
  const auth = useAuth();
  return (
    <Paper className="content-card review-rail">
      <Typography className="section-heading" variant="h6">Human review</Typography>
      <Chip size="small" color="warning" label={`${reviews.length} paused`} sx={{ my: 1 }} />
      {reviews.map((review) => (
        <div className="review-card" key={review.review_id}>
          <strong>{review.title}</strong>
          <p>{review.reason}</p>
          <Stack direction="row" gap={0.5} flexWrap="wrap">
            {review.policy_evidence.map((item) => <Chip size="small" variant="outlined" key={item} label={item} />)}
          </Stack>
          <Typography className="subsection-heading">Requested action</Typography>
          {Object.entries(review.requested_action).map(([key, value]) => (
            <small key={key}><b>{key.replaceAll("_", " ")}:</b> {String(value)}</small>
          ))}
          {auth.hasRole("reviewer", "admin") && (
            <Stack direction="row" spacing={1} mt={2}>
              <Button size="small" color="error" onClick={() => onDecision(review, "reject")}>Reject</Button>
              <Button size="small" variant="contained" onClick={() => onDecision(review, "approve")}>Approve & resume</Button>
            </Stack>
          )}
        </div>
      ))}
    </Paper>
  );
}
