// src/components/Footer.tsx
import React from "react";
import dayjs from "../utils/dayjsConfig";

const Footer: React.FC = () => {
  const currentYear = dayjs().tz("Europe/Riga").year();
  return (
    <footer className="bg-midnight-indigo border-t border-midnight-azure px-2.5 py-2 text-center">
      <p className="text-indigo-bright">&copy; {currentYear} Dzīvoklītis</p>
      <a href="/terms" className="text-xs text-indigo-breeze">
        Nosacījumi un noteikumi
      </a>
    </footer>
  );
};

export default Footer;
