// src/components/BottomNav.tsx
import React from "react";
import { NavItem, BottomNavProps } from "../types/nav.types";
// Definimos los IDs de las páginas disponibles para evitar errores de dedo

const navItems: NavItem[] = [
  {
    id: "feed",
    label: "Feed",
    icon: "bi-house-door",
    activeIcon: "bi-house-door-fill",
  },
  { id: "search", label: "Search", icon: "bi-search", activeIcon: "bi-search" },
  {
    id: "alerts",
    label: "Alerts",
    icon: "bi-bell",
    activeIcon: "bi-bell-fill",
  },
  {
    id: "friends",
    label: "Friends",
    icon: "bi-people",
    activeIcon: "bi-people-fill",
  },
  {
    id: "profile",
    label: "Profile",
    icon: "bi-person",
    activeIcon: "bi-person-fill",
  },
];

const BottomNav: React.FC<BottomNavProps> = ({ activePage, onPageChange }) => {
  return (
    <nav className="navbar fixed-bottom navbar-dark bg-dark border-top border-secondary py-0">
      <div className="container-fluid justify-content-around">
        <ul className="nav nav-pills nav-justified w-100 py-2">
          {navItems.map((item) => {
            const isActive = activePage === item.id;
            return (
              <li key={item.id} className="nav-item">
                <button
                  className={`nav-link border-0 bg-transparent d-flex flex-column align-items-center transition-all ${
                    isActive ? "text-primary" : "text-secondary"
                  }`}
                  onClick={() => onPageChange(item.id)}
                  style={{ cursor: "pointer" }}
                >
                  <i
                    className={`bi ${isActive ? item.activeIcon : item.icon} fs-4`}
                  ></i>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: isActive ? "bold" : "normal",
                    }}
                  >
                    {item.label}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
};

export default BottomNav;
