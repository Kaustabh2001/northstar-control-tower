import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#10221b", contrastText: "#ffffff" },
    secondary: { main: "#b8f35a", contrastText: "#10221b" },
    background: { default: "#f3f3ed", paper: "#fffefa" },
    text: { primary: "#18241f", secondary: "#67716c" },
    divider: "#dfe1d8",
    success: { main: "#167653" },
    warning: { main: "#a86313" },
    error: { main: "#bd3b44" },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
    h1: { fontWeight: 760, letterSpacing: "-0.045em" },
    h2: { fontWeight: 740, letterSpacing: "-0.025em" },
    h3: { fontWeight: 800, letterSpacing: "-0.035em" },
    h4: { fontWeight: 800, letterSpacing: "-0.025em" },
    h5: { fontWeight: 800, letterSpacing: "-0.018em" },
    h6: { fontWeight: 800, letterSpacing: "-0.01em" },
    button: { textTransform: "none", fontWeight: 700 },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: "none", border: "1px solid #dfe1d8" },
      },
    },
  },
});
