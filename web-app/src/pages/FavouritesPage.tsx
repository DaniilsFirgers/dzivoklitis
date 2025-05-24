// src/pages/FavouritesPage.tsx
import React from "react";
import Favourite from "../features/favourite/Favourite";
import { type Favourite as FavoriteType } from "../features/favourite/types";
import { useTelegramUser } from "../context/UserContext";

const FavouritesPage: React.FC = () => {
  const user = useTelegramUser();
  console.log("User data:", user);
  // Simulated data for favourites
  const favourites: FavoriteType[] = [
    {
      flat_id: "1",
      source: "ss.lv",
      city: "Rīga",
      district: "Centrs",
      street: "Brīvības iela",
      deal_type: "Pārdod",
      series: "Jaunais projekts",
      url: "https://ss.lv/msg/lv/real-estate/flats/riga/centre/flat-1-2-3-4-5-6-7-8-9-10-11-12-13-14-15.html",
      price: 100000,
      price_per_m2: 2000,
      rooms: 3,
      floor: 2,
      floors_total: 5,
      area: 50,
    },
    {
      flat_id: "2",
      source: "city24.lv",
      city: "Rīga",
      district: "Teika",
      street: "Brīvības iela",
      deal_type: "Pārdod",
      series: "Jaunais projekts",
      url: "https://city24.lv/lv/real-estate/flats/riga/teika/flat-1-2-3-4-5-6-7-8-9-10.html",
      price: 120000,
      price_per_m2: 2400,
      rooms: 4,
      floor: 3,
      floors_total: 6,
      area: 60,
    },
  ];
  return (
    <div>
      <h1 className="text-indigo-breeze/80 pb-3 w-full text-center text-md font-medium">
        <span className="opacity-70">⭐</span> Jūsu iecienītākie dzīvokļu
        sludinājumi <span className="opacity-80">⭐</span>
      </h1>
      <div className="flex flex-wrap gap-3">
        {favourites.map((favourite) => (
          <div key={favourite.flat_id} className="mb-4 md:mx-0 mx-auto">
            <Favourite favourite={favourite} />
          </div>
        ))}
      </div>
    </div>
  );
};

export default FavouritesPage;
