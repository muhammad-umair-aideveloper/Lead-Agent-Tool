"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Skeleton,
  Chip,
} from "@mui/material";
import {
  People,
  Send,
  Reply,
  DoNotDisturb,
  Block,
  Timer,
  TrendingUp,
  TrendingDown,
} from "@mui/icons-material";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
} from "recharts";

import { fetchDashboard, DashboardData } from "@/lib/api";

const COLORS = ["#6C63FF", "#FF6584", "#4CAF50", "#FF9800", "#29B6F6", "#AB47BC"];

interface KPICardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  subtitle?: string;
  color: string;
}

function KPICard({ title, value, icon, subtitle, color }: KPICardProps) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
          <Box
            sx={{
              bgcolor: `${color}22`,
              borderRadius: "50%",
              width: 40,
              height: 40,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color,
            }}
          >
            {icon}
          </Box>
        </Box>
        <Typography variant="h4" sx={{ mb: 0.5 }}>
          {value}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardView() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const result = await fetchDashboard();
      setData(result);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 3 }}>
          Dashboard
        </Typography>
        <Grid container spacing={3}>
          {[...Array(6)].map((_, i) => (
            <Grid item xs={12} sm={6} md={4} lg={2} key={i}>
              <Skeleton variant="rounded" height={140} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (!data) {
    return (
      <Typography color="error">Failed to load dashboard data.</Typography>
    );
  }

  const { kpis } = data;

  // Prepare data for charts
  const stateData = Object.entries(data.state_distribution).map(
    ([name, value]) => ({ name, value })
  );

  const sourceData = Object.entries(data.source_distribution).map(
    ([name, value]) => ({ name, value })
  );

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", mb: 3, gap: 2 }}>
        <Typography variant="h4">Dashboard</Typography>
        <Chip
          label="Live"
          size="small"
          color="success"
          variant="outlined"
          sx={{ animation: "pulse 2s infinite" }}
        />
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KPICard
            title="Total Leads"
            value={kpis.total_leads.toLocaleString()}
            icon={<People fontSize="small" />}
            color="#6C63FF"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KPICard
            title="Messages Sent"
            value={kpis.total_messages_sent.toLocaleString()}
            icon={<Send fontSize="small" />}
            color="#29B6F6"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KPICard
            title="Replies"
            value={kpis.total_replies.toLocaleString()}
            icon={<Reply fontSize="small" />}
            subtitle={`${kpis.reply_rate}% rate`}
            color="#4CAF50"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KPICard
            title="Ignored"
            value={kpis.total_ignored.toLocaleString()}
            icon={<DoNotDisturb fontSize="small" />}
            subtitle={`${kpis.ignored_rate}% rate`}
            color="#FF9800"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KPICard
            title="Opted Out"
            value={kpis.total_opted_out.toLocaleString()}
            icon={<Block fontSize="small" />}
            color="#f44336"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={4} lg={2}>
          <KPICard
            title="Avg Reply Time"
            value={
              kpis.avg_reply_time_minutes
                ? `${kpis.avg_reply_time_minutes}m`
                : "N/A"
            }
            icon={<Timer fontSize="small" />}
            color="#AB47BC"
          />
        </Grid>
      </Grid>

      {/* Charts Row 1 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Daily messages trend */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: 360 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Daily Messages Sent
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={data.daily_messages}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="date" stroke="#888" fontSize={12} />
                  <YAxis stroke="#888" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1d29",
                      border: "1px solid #333",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#6C63FF"
                    strokeWidth={2}
                    dot={{ fill: "#6C63FF", r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* State distribution pie */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: 360 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Lead State Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie
                    data={stateData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }: { name: string; percent: number }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {stateData.map((_, idx) => (
                      <Cell
                        key={idx}
                        fill={COLORS[idx % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1d29",
                      border: "1px solid #333",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Row 2 */}
      <Grid container spacing={3}>
        {/* Intent performance */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: 360 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Intent Category Performance
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={data.intent_breakdown}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="intent_category" stroke="#888" fontSize={11} />
                  <YAxis stroke="#888" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1d29",
                      border: "1px solid #333",
                    }}
                  />
                  <Legend />
                  <Bar dataKey="count" name="Total" fill="#6C63FF" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="reply_count" name="Replies" fill="#4CAF50" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Source distribution */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: 360 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Lead Source Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={sourceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis type="number" stroke="#888" fontSize={12} />
                  <YAxis
                    dataKey="name"
                    type="category"
                    stroke="#888"
                    fontSize={11}
                    width={120}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1d29",
                      border: "1px solid #333",
                    }}
                  />
                  <Bar dataKey="value" fill="#FF6584" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
