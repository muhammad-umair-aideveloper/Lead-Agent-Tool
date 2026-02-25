"use client";

import { ThemeProvider, CssBaseline } from "@mui/material";
import { SnackbarProvider } from "notistack";
import theme from "@/lib/theme";
import DashboardShell from "@/components/DashboardShell";

export default function HomePage() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SnackbarProvider
        maxSnack={3}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <DashboardShell />
      </SnackbarProvider>
    </ThemeProvider>
  );
}
