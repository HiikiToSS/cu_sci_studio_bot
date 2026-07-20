import { useState } from "react";
import Menu from "./layouts/Menu";
import { MenuItem } from "./types";
import Statistics from "./layouts/Statistics";
import Graph from "./layouts/Graph";
import "./global.css";
import { library } from "@fortawesome/fontawesome-svg-core";
import { fas } from "@fortawesome/free-solid-svg-icons";

library.add(fas);

const menuItems = [MenuItem.STATISTICS, MenuItem.GRAPH];

function ApplyTelegramTheme() {
  const tg = window.Telegram?.WebApp;
  const themeParams = tg?.themeParams;
  if (!themeParams) return;

  const root = document.documentElement;
  const map = {
    "--tg-theme-bg-color": themeParams.bg_color,
    "--tg-theme-secondary-bg-color": themeParams.secondary_bg_color,
    "--tg-theme-text-color": themeParams.text_color,
    "--tg-theme-hint-color": themeParams.hint_color,
    "--tg-theme-link-color": themeParams.link_color,
    "--tg-theme-button-color": themeParams.button_color,
    "--tg-theme-button-text-color": themeParams.button_text_color,
  };

  Object.entries(map).forEach(([key, value]) => {
    if (value) {
      root.style.setProperty(key, value);
    }
  });

  if (tg.colorScheme) {
    root.dataset.tgColorScheme = tg.colorScheme;
  }
}

ApplyTelegramTheme();

export default function App() {
  const [selectedItem, setSelectedItem] = useState<MenuItem>(
    MenuItem.STATISTICS,
  );

  function handleMenuSelection(menuItem: MenuItem) {
    setSelectedItem(menuItem);
  }

  return (
    <>
      <main>
        {selectedItem == MenuItem.STATISTICS ? (
          <Statistics></Statistics>
        ) : (
          <Graph></Graph>
        )}
      </main>
      <Menu
        menuItems={menuItems}
        selectedItem={selectedItem}
        onClick={handleMenuSelection}
      ></Menu>
    </>
  );
}
