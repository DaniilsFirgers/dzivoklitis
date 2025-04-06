// src/components/Footer.tsx
import React from "react";
import Button from "@mui/material/Button";
import { Favourite as FavouriteType } from "./types";

type Props = {
  favourite: FavouriteType;
};

const Favourite: React.FC<Props> = ({ favourite }) => {
  return (
    <div className="w-fit p-3 rounded-md shadow-md bg-midnight-storm shadow text-md">
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Avots:</b>
        <h1 className="text-steel-bluee">{favourite.source}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Pilsēta:</b>
        <h1 className="text-steel-bluee">{favourite.city}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Darījums:</b>
        <h1 className="text-steel-bluee">{favourite.deal_type}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Apkaime:</b>
        <h1 className="text-steel-bluee">{favourite.district}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Iela:</b>
        <h1 className="text-steel-bluee">{favourite.street}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Sērija:</b>
        <h1 className="text-steel-bluee">{favourite.series}</h1>
      </h2>
      <h2 className="flex ">
        <b className="mr-1.5 text-midnight-moody">Cena €:</b>
        <h1 className="text-steel-bluee">{favourite.price}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Cena €/m²:</b>
        <h1 className="text-steel-bluee"> {favourite.price_per_m2}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Istabas:</b>
        <h1 className="text-steel-bluee">{favourite.rooms}</h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Stāvs:</b>
        <h1 className="text-steel-bluee">
          {favourite.floor}/{favourite.floors_total}
        </h1>
      </h2>
      <h2 className="flex">
        <b className="mr-1.5 text-midnight-moody">Platība m²:</b>
        <h1 className="text-steel-bluee">{favourite.area}</h1>
      </h2>
      <div>
        <Button variant="contained" color="primary">
          <a href={favourite.url} target="_blank" rel="noopener noreferrer">
            🔍 Aplūkot
          </a>
        </Button>
      </div>
    </div>
  );
};

export default Favourite;
