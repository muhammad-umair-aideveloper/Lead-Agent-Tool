"use client";

import React, { useEffect, useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Button,
  Alert,
  Divider,
  Chip,
} from "@mui/material";
import { Save, Settings } from "@mui/icons-material";
import { useSnackbar } from "notistack";
import { fetchConfig, updateConfig, AppConfig } from "@/lib/api";

const TIMEZONES = [
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "America/Phoenix",
  "America/Anchorage",
  "Pacific/Honolulu",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Australia/Sydney",
  "UTC",
];

const TONES = ["professional", "casual", "urgency"];

export default function ConfigView() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await fetchConfig();
      setConfig(data);
    } catch (err) {
      enqueueSnackbar("Failed to load configuration.", { variant: "error" });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (key: keyof AppConfig, value: string | number) => {
    setConfig((prev) => (prev ? { ...prev, [key]: value } : prev));
    setDirty(true);
  };

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const updated = await updateConfig(config);
      setConfig(updated);
      setDirty(false);
      enqueueSnackbar("Configuration saved successfully.", {
        variant: "success",
      });
    } catch (err) {
      enqueueSnackbar("Failed to save configuration.", { variant: "error" });
    } finally {
      setSaving(false);
    }
  };

  if (loading || !config) {
    return <Typography>Loading configuration...</Typography>;
  }

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 3,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Settings color="primary" />
          <Typography variant="h4">Configuration</Typography>
        </Box>
        {dirty && (
          <Chip
            label="Unsaved changes"
            color="warning"
            size="small"
            variant="outlined"
          />
        )}
      </Box>

      {/* Business Hours */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Business Hours
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Outbound SMS messages will only be sent during these configured
            hours. Messages queued outside this window will be deferred.
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Start Time"
                type="time"
                value={config.business_hours_start}
                onChange={(e) =>
                  handleChange("business_hours_start", e.target.value)
                }
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="End Time"
                type="time"
                value={config.business_hours_end}
                onChange={(e) =>
                  handleChange("business_hours_end", e.target.value)
                }
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={config.business_hours_timezone}
                  label="Timezone"
                  onChange={(e) =>
                    handleChange("business_hours_timezone", e.target.value)
                  }
                >
                  {TIMEZONES.map((tz) => (
                    <MenuItem key={tz} value={tz}>
                      {tz}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* SMS Settings */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            SMS Settings
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Configure the default message tone and retry behaviour for outbound
            communications.
          </Typography>

          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Default SMS Tone</InputLabel>
                <Select
                  value={config.default_sms_tone}
                  label="Default SMS Tone"
                  onChange={(e) =>
                    handleChange("default_sms_tone", e.target.value)
                  }
                >
                  {TONES.map((t) => (
                    <MenuItem key={t} value={t}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Ignore Timeout (hours)"
                type="number"
                value={config.ignore_timeout_hours}
                onChange={(e) =>
                  handleChange(
                    "ignore_timeout_hours",
                    parseInt(e.target.value) || 48
                  )
                }
                helperText="Leads without a reply after this period are marked 'ignored'"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Max Retries"
                type="number"
                value={config.max_retries}
                onChange={(e) =>
                  handleChange("max_retries", parseInt(e.target.value) || 3)
                }
                helperText="Maximum number of retry attempts for failed operations"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* API Keys Notice */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            API Credentials
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            For security, API keys (Twilio, Gemini) are managed via environment
            variables or a secrets vault. They are not exposed through the
            dashboard UI.
          </Alert>
          <Typography variant="body2" color="text.secondary">
            To update API credentials, modify the <code>.env</code> file or your
            deployment&apos;s environment variable configuration and restart the
            backend service.
          </Typography>
        </CardContent>
      </Card>

      {/* Save button */}
      <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<Save />}
          onClick={handleSave}
          disabled={!dirty || saving}
        >
          {saving ? "Saving..." : "Save Configuration"}
        </Button>
      </Box>
    </Box>
  );
}
