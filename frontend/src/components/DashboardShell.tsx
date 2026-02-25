"use client";

import React, { useState } from "react";
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Divider,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import {
  Dashboard as DashboardIcon,
  CloudUpload as UploadIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  AutoAwesome as AgentIcon,
} from "@mui/icons-material";

import DashboardView from "./views/DashboardView";
import UploadView from "./views/UploadView";
import LeadsView from "./views/LeadsView";
import ConfigView from "./views/ConfigView";

const DRAWER_WIDTH = 260;

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: <DashboardIcon /> },
  { key: "upload", label: "Upload Leads", icon: <UploadIcon /> },
  { key: "leads", label: "Lead Audit Log", icon: <PeopleIcon /> },
  { key: "config", label: "Configuration", icon: <SettingsIcon /> },
];

export default function DashboardShell() {
  const [activeView, setActiveView] = useState("dashboard");
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const drawerContent = (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <Toolbar sx={{ gap: 1, px: 2 }}>
        <AgentIcon color="primary" />
        <Typography variant="h6" noWrap sx={{ fontSize: "1rem" }}>
          Lead Reactivation
        </Typography>
      </Toolbar>
      <Divider />
      <List sx={{ flex: 1, px: 1, pt: 1 }}>
        {NAV_ITEMS.map(({ key, label, icon }) => (
          <ListItemButton
            key={key}
            selected={activeView === key}
            onClick={() => {
              setActiveView(key);
              if (isMobile) setMobileOpen(false);
            }}
            sx={{
              borderRadius: 2,
              mb: 0.5,
              "&.Mui-selected": {
                bgcolor: "primary.main",
                color: "#fff",
                "&:hover": { bgcolor: "primary.dark" },
                "& .MuiListItemIcon-root": { color: "#fff" },
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{icon}</ListItemIcon>
            <ListItemText primary={label} />
          </ListItemButton>
        ))}
      </List>
      <Box sx={{ p: 2, textAlign: "center" }}>
        <Typography variant="caption" color="text.secondary">
          Google Antigravity v1.0
        </Typography>
      </Box>
    </Box>
  );

  const renderView = () => {
    switch (activeView) {
      case "dashboard":
        return <DashboardView />;
      case "upload":
        return <UploadView />;
      case "leads":
        return <LeadsView />;
      case "config":
        return <ConfigView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar */}
      {isMobile ? (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          sx={{
            "& .MuiDrawer-paper": {
              width: DRAWER_WIDTH,
              bgcolor: "background.paper",
            },
          }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            "& .MuiDrawer-paper": {
              width: DRAWER_WIDTH,
              bgcolor: "background.paper",
              borderRight: "1px solid rgba(255,255,255,0.08)",
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
          minHeight: "100vh",
        }}
      >
        {isMobile && (
          <AppBar position="sticky" elevation={0}>
            <Toolbar>
              <IconButton
                color="inherit"
                edge="start"
                onClick={() => setMobileOpen(true)}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="h6" noWrap sx={{ ml: 1 }}>
                Lead Reactivation Agent
              </Typography>
            </Toolbar>
          </AppBar>
        )}

        <Box sx={{ flex: 1, p: { xs: 2, md: 3 }, overflow: "auto" }}>
          {renderView()}
        </Box>
      </Box>
    </Box>
  );
}
