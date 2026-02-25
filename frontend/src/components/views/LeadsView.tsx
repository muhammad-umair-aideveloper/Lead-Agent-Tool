"use client";

import React, { useEffect, useState, useCallback } from "react";
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
  Chip,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Pagination,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  InputAdornment,
} from "@mui/material";
import {
  Search,
  Download,
  Visibility,
  FilterList,
  Refresh,
} from "@mui/icons-material";

import {
  fetchLeads,
  fetchLeadMessages,
  exportCSV,
  Lead,
  LeadFilters,
} from "@/lib/api";

const STATES = ["", "pending", "message_sent", "replied", "ignored", "opted_out"];
const INTENTS = ["", "High Intent", "Medium Intent", "Low Intent", "Not Interested"];

const stateColor = (state: string) => {
  switch (state) {
    case "pending":
      return "default";
    case "message_sent":
      return "info";
    case "replied":
      return "success";
    case "ignored":
      return "warning";
    case "opted_out":
      return "error";
    default:
      return "default";
  }
};

const intentColor = (intent: string) => {
  switch (intent) {
    case "High Intent":
      return "success";
    case "Medium Intent":
      return "info";
    case "Low Intent":
      return "warning";
    case "Not Interested":
      return "error";
    default:
      return "default";
  }
};

export default function LeadsView() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState<LeadFilters>({
    page: 1,
    page_size: 25,
    state: "",
    intent: "",
    source: "",
    search: "",
    date_from: "",
    date_to: "",
  });
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [detailOpen, setDetailOpen] = useState(false);

  const loadLeads = useCallback(async () => {
    setLoading(true);
    try {
      const cleanFilters: any = { ...filters };
      Object.keys(cleanFilters).forEach((k) => {
        if (cleanFilters[k] === "" || cleanFilters[k] == null) {
          delete cleanFilters[k];
        }
      });
      const result = await fetchLeads(cleanFilters);
      setLeads(result.leads);
      setTotal(result.total);
    } catch (err) {
      console.error("Failed to load leads:", err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  const handlePageChange = (_: any, page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const handleViewDetails = async (lead: Lead) => {
    setSelectedLead(lead);
    try {
      const msgs = await fetchLeadMessages(lead.lead_id);
      setMessages(msgs);
    } catch (err) {
      setMessages([]);
    }
    setDetailOpen(true);
  };

  const totalPages = Math.ceil(total / (filters.page_size || 25));

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
        <Typography variant="h4">Lead Audit Log</Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadLeads}
            size="small"
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => exportCSV(filters)}
            size="small"
          >
            Export CSV
          </Button>
        </Stack>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="Search"
                placeholder="Name, ID, or phone..."
                value={filters.search}
                onChange={(e) => handleFilterChange("search", e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={6} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>State</InputLabel>
                <Select
                  value={filters.state || ""}
                  label="State"
                  onChange={(e) => handleFilterChange("state", e.target.value)}
                >
                  <MenuItem value="">All States</MenuItem>
                  {STATES.filter(Boolean).map((s) => (
                    <MenuItem key={s} value={s}>
                      {s}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sm={3} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Intent</InputLabel>
                <Select
                  value={filters.intent || ""}
                  label="Intent"
                  onChange={(e) => handleFilterChange("intent", e.target.value)}
                >
                  <MenuItem value="">All Intents</MenuItem>
                  {INTENTS.filter(Boolean).map((i) => (
                    <MenuItem key={i} value={i}>
                      {i}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sm={3} md={2.5}>
              <TextField
                fullWidth
                size="small"
                label="From Date"
                type="date"
                value={filters.date_from || ""}
                onChange={(e) => handleFilterChange("date_from", e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={6} sm={3} md={2.5}>
              <TextField
                fullWidth
                size="small"
                label="To Date"
                type="date"
                value={filters.date_to || ""}
                onChange={(e) => handleFilterChange("date_to", e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Lead table */}
      <Card>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Lead ID</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Last Interaction</TableCell>
                <TableCell>Intent</TableCell>
                <TableCell>State</TableCell>
                <TableCell>Tone</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {leads.map((lead) => (
                <TableRow key={lead.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {lead.lead_id}
                    </Typography>
                  </TableCell>
                  <TableCell>{lead.full_name}</TableCell>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace">
                      {lead.phone_number}
                    </Typography>
                  </TableCell>
                  <TableCell>{lead.lead_source}</TableCell>
                  <TableCell>
                    {new Date(lead.last_interaction_date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {lead.intent_category && (
                      <Chip
                        label={lead.intent_category}
                        size="small"
                        color={intentColor(lead.intent_category) as any}
                        variant="outlined"
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={lead.state}
                      size="small"
                      color={stateColor(lead.state) as any}
                    />
                  </TableCell>
                  <TableCell>
                    {lead.sms_tone && (
                      <Chip label={lead.sms_tone} size="small" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => handleViewDetails(lead)}
                      >
                        <Visibility fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {leads.length === 0 && (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      {loading ? "Loading..." : "No leads found."}
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            px: 2,
            py: 1.5,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            {total} total leads
          </Typography>
          <Pagination
            count={totalPages}
            page={filters.page || 1}
            onChange={handlePageChange}
            color="primary"
            size="small"
          />
        </Box>
      </Card>

      {/* Lead Detail Dialog */}
      <Dialog
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedLead && (
          <>
            <DialogTitle>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Typography variant="h6">
                  {selectedLead.full_name}
                </Typography>
                <Chip
                  label={selectedLead.state}
                  color={stateColor(selectedLead.state) as any}
                  size="small"
                />
              </Box>
            </DialogTitle>
            <DialogContent dividers>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6} sm={4}>
                  <Typography variant="caption" color="text.secondary">
                    Lead ID
                  </Typography>
                  <Typography variant="body2" fontFamily="monospace">
                    {selectedLead.lead_id}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={4}>
                  <Typography variant="caption" color="text.secondary">
                    Phone
                  </Typography>
                  <Typography variant="body2">
                    {selectedLead.phone_number}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={4}>
                  <Typography variant="caption" color="text.secondary">
                    Email
                  </Typography>
                  <Typography variant="body2">
                    {selectedLead.email || "—"}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={4}>
                  <Typography variant="caption" color="text.secondary">
                    Source
                  </Typography>
                  <Typography variant="body2">
                    {selectedLead.lead_source}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={4}>
                  <Typography variant="caption" color="text.secondary">
                    Intent
                  </Typography>
                  <Typography variant="body2">
                    {selectedLead.intent_category || "—"}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={4}>
                  <Typography variant="caption" color="text.secondary">
                    Tone
                  </Typography>
                  <Typography variant="body2">
                    {selectedLead.sms_tone || "—"}
                  </Typography>
                </Grid>
              </Grid>

              {selectedLead.intent_rationale && (
                <Box sx={{ mb: 3 }}>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    sx={{ mb: 0.5 }}
                  >
                    AI Intent Rationale
                  </Typography>
                  <Paper
                    sx={{ p: 2, bgcolor: "rgba(108,99,255,0.08)" }}
                    variant="outlined"
                  >
                    <Typography variant="body2">
                      {selectedLead.intent_rationale}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {selectedLead.recommended_angle && (
                <Box sx={{ mb: 3 }}>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    sx={{ mb: 0.5 }}
                  >
                    Recommended SMS
                  </Typography>
                  <Paper
                    sx={{ p: 2, bgcolor: "rgba(76,175,80,0.08)" }}
                    variant="outlined"
                  >
                    <Typography variant="body2">
                      {selectedLead.recommended_angle}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {selectedLead.notes && (
                <Box sx={{ mb: 3 }}>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    sx={{ mb: 0.5 }}
                  >
                    Historical Notes
                  </Typography>
                  <Paper sx={{ p: 2 }} variant="outlined">
                    <Typography variant="body2">
                      {selectedLead.notes}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {/* Message history */}
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Message History ({messages.length})
              </Typography>
              {messages.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No messages yet.
                </Typography>
              ) : (
                <Stack spacing={1}>
                  {messages.map((msg: any) => (
                    <Paper
                      key={msg.id}
                      sx={{
                        p: 1.5,
                        bgcolor:
                          msg.direction === "outbound"
                            ? "rgba(108,99,255,0.06)"
                            : "rgba(76,175,80,0.06)",
                        borderLeft: `3px solid ${
                          msg.direction === "outbound"
                            ? "#6C63FF"
                            : "#4CAF50"
                        }`,
                      }}
                      variant="outlined"
                    >
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 0.5,
                        }}
                      >
                        <Chip
                          label={msg.direction}
                          size="small"
                          color={
                            msg.direction === "outbound" ? "primary" : "success"
                          }
                          variant="outlined"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {msg.sent_at || msg.received_at || msg.created_at
                            ? new Date(
                                msg.sent_at || msg.received_at || msg.created_at
                              ).toLocaleString()
                            : "—"}
                        </Typography>
                      </Box>
                      <Typography variant="body2">{msg.body}</Typography>
                    </Paper>
                  ))}
                </Stack>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
}
