import { createRoot } from "react-dom/client";
import App from "./App";
import { StrictMode } from "react";

const domMode = document.getElementById("root") as HTMLElement;
const root = createRoot(domMode);

root.render(
  <StrictMode>
    <App />
  </StrictMode>,
);
