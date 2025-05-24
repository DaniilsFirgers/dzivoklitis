// src/components/Layout.tsx

import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import Footer from "./Footer";

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const navItems = [
    { name: "Sākums", path: "/" },
    { name: "Favorīti", path: "/favourites" },
    { name: "Par mums", path: "/about" },
  ];

  return (
    <div className="flex flex-col min-h-screen w-full">
      <header className="bg-midnight-indigo border-b border-midnight-azure w-full h-10">
        <div className="flex justify-between items-center h-full mx-4">
          <h1 className="text-xl text-indigo-bright">Dzīvoklītis</h1>
          <nav>
            <ul className="flex space-x-4">
              {navItems.map((item) => (
                <li key={item.name}>
                  <NavLink
                    to={item.path}
                    className={`text-md ${
                      location.pathname == item.path
                        ? "text-indigo-bright"
                        : "text-indigo-breeze"
                    }`}
                  >
                    {item.name}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <main className="flex-grow p-4 bg-midnight-indigo">{children}</main>
      <Footer />
    </div>
  );
};

export default Layout;
