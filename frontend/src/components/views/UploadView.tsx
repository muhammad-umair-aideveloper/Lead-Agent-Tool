"use client";

import React, { useState, useCallback } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  Stack,
} from "@mui/material";
import {
  CloudUpload,
  CheckCircle,
  Error as ErrorIcon,
  PlayArrow,
  InsertDriveFile,
} from "@mui/icons-material";
import { useDropzone } from "react-dropzone";
import { useSnackbar } from "notistack";
import { uploadCSV, processBatch, Batch } from "@/lib/api";

export default function UploadView() {
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [batch, setBatch] = useState<Batch | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processResult, setProcessResult] = useState<any>(null);
  const { enqueueSnackbar } = useSnackbar();

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      if (!file.name.endsWith(".csv")) {
        setError("Please upload a CSV file.");
        return;
      }

      setError(null);
      setUploading(true);
      setBatch(null);
      setProcessResult(null);

      try {
        const result = await uploadCSV(file);
        setBatch(result);
        enqueueSnackbar(
          `Successfully uploaded ${result.total_leads} leads!`,
          { variant: "success" }
        );
      } catch (err: any) {
        const msg =
          err.response?.data?.detail || "Failed to upload CSV file.";
        setError(msg);
        enqueueSnackbar(msg, { variant: "error" });
      } finally {
        setUploading(false);
      }
    },
    [enqueueSnackbar]
  );

  const handleProcess = async () => {
    if (!batch) return;
    setProcessing(true);
    setProcessResult(null);

    try {
      const result = await processBatch(batch.batch_id);
      setProcessResult(result.stats);
      enqueueSnackbar("Batch processing complete!", { variant: "success" });
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || "Failed to process batch.";
      enqueueSnackbar(msg, { variant: "error" });
    } finally {
      setProcessing(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        Upload Leads
      </Typography>

      {/* Upload zone */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: "2px dashed",
              borderColor: isDragActive
                ? "primary.main"
                : "rgba(255,255,255,0.15)",
              borderRadius: 3,
              p: 6,
              textAlign: "center",
              cursor: "pointer",
              transition: "all 0.2s",
              bgcolor: isDragActive
                ? "rgba(108,99,255,0.08)"
                : "transparent",
              "&:hover": {
                borderColor: "primary.main",
                bgcolor: "rgba(108,99,255,0.04)",
              },
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload
              sx={{ fontSize: 48, color: "primary.main", mb: 2 }}
            />
            <Typography variant="h6" sx={{ mb: 1 }}>
              {isDragActive
                ? "Drop your CSV file here..."
                : "Drag & drop a CSV file, or click to browse"}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Accepted format: .csv — Required columns: lead_id, full_name,
              phone_number, last_interaction_date, lead_source
            </Typography>
          </Box>

          {uploading && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 1, textAlign: "center" }}
              >
                Validating and ingesting leads...
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Batch result */}
      {batch && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                mb: 2,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <InsertDriveFile color="primary" />
                <Typography variant="h6">
                  Batch: {batch.batch_id}
                </Typography>
              </Box>
              <Chip
                label={batch.status}
                color={
                  batch.status === "completed"
                    ? "success"
                    : batch.status === "failed"
                    ? "error"
                    : "warning"
                }
                size="small"
              />
            </Box>

            <List dense>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle color="success" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={`File: ${batch.filename || "unknown"}`}
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle color="success" fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={`Total leads ingested: ${batch.total_leads}`}
                />
              </ListItem>
            </List>

            <Divider sx={{ my: 2 }} />

            <Button
              variant="contained"
              size="large"
              startIcon={<PlayArrow />}
              onClick={handleProcess}
              disabled={processing || batch.status === "completed"}
              fullWidth
            >
              {processing
                ? "Processing... (AI Analysis + SMS Dispatch)"
                : "Start Autonomous Processing"}
            </Button>

            {processing && <LinearProgress sx={{ mt: 2 }} />}
          </CardContent>
        </Card>
      )}

      {/* Process results */}
      {processResult && (
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Processing Results
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
              <Chip
                icon={<CheckCircle />}
                label={`Analyzed: ${processResult.analyzed}`}
                color="info"
              />
              <Chip
                icon={<CheckCircle />}
                label={`SMS Sent: ${processResult.sent}`}
                color="success"
              />
              <Chip
                label={`Skipped: ${processResult.skipped}`}
                color="warning"
              />
              {processResult.errors > 0 && (
                <Chip
                  icon={<ErrorIcon />}
                  label={`Errors: ${processResult.errors}`}
                  color="error"
                />
              )}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
