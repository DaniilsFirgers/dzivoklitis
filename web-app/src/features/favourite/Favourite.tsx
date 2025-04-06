// src/components/Footer.tsx
import React from "react";
import { Favourite as FavouriteType } from "./types";

type Props = {
  favourite: FavouriteType;
};

const Favourite: React.FC<Props> = ({ favourite }) => {
  return (
    <div className="w-fit p-3 rounded-md shadow-md bg-midnight-storm shadow text-md">
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Avots:</b>
        <h1 className="text-steel-blue">{favourite.source}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Pilsēta:</b>
        <h1 className="text-steel-blue">{favourite.city}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Darījums:</b>
        <h1 className="text-steel-blue">{favourite.deal_type}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Apkaime:</b>
        <h1 className="text-steel-blue">{favourite.district}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Iela:</b>
        <h1 className="text-steel-blue">{favourite.street}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Sērija:</b>
        <h1 className="text-steel-blue">{favourite.series}</h1>
      </h2>
      <h2 className="flex ">
        <b className="mr-1.5 text-midnight-moody">Cena €:</b>
        <h1 className="text-steel-blue">{favourite.price}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Cena €/m²:</b>
        <h1 className="text-steel-blue"> {favourite.price_per_m2}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Istabas:</b>
        <h1 className="text-steel-blue">{favourite.rooms}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Stāvs:</b>
        <h1 className="text-steel-blue">
          {favourite.floor}/{favourite.floors_total}
        </h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Platība m²:</b>
        <h1 className="text-steel-blue">{favourite.area}</h1>
      </h2>
      <div className="pt-2 flex gap-2">
        <button className="bg-indigo-breeze hover:bg-indigo-breeze/60 px-1.5 py-1 rounded w-[100px]">
          <a
            href={favourite.url}
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline text-gray-400"
          >
            🔍 Aplūkot
          </a>
        </button>
        <button className="bg-red-500/50 hover:bg-red-600/60 px-1.5 py-1 rounded w-[100px]">
          <a
            href={favourite.url}
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline text-gray-400"
          >
            ❌ Dzēst
          </a>
        </button>
      </div>
    </div>
  );
};

export default Favourite;
