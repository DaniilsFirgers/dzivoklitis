// src/components/Footer.tsx
import React from "react";
import dayjs from "../utils/dayjsConfig";

const Footer: React.FC = () => {
  const currentYear = dayjs().tz("Europe/Riga").year();
  return (
    <footer className="bg-gray-800 px-2.5 py-2 text-center">
      <p className="text-white">&copy; {currentYear} Dzīvoklitis</p>
      <a href="/terms" className="text-xs text-gray-500">
        Nosacījumi un noteikumi
      </a>
    </footer>
  );
};

export default Footer;
