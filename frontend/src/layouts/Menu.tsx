import { MenuItem } from "../types";
import "./Menu.css";

interface MenuProps {
  menuItems: MenuItem[];
  onClick?: (menuItem: MenuItem) => void;
  selectedItem: MenuItem;
}
export default function Menu({ menuItems, onClick, selectedItem }: MenuProps) {
  return (
    <nav className="menu">
      <ul className="menu-list">
        {menuItems.map((MenuItem: MenuItem) => (
          <li key={MenuItem.toString()}>
            <a
              className={`menu-item${selectedItem === MenuItem ? " menu-item-selected" : ""}`}
              href="#"
              onClick={() => onClick?.(MenuItem)}
            >
              {MenuItem.icon}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
}
