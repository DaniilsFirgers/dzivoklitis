// src/components/Footer.tsx
import React from "react";
import Button from "@mui/material/Button";
import { Favourite as FavouriteType } from "./types";

type Props = {
  favourite: FavouriteType;
};

const Favourite: React.FC<Props> = ({ favourite }) => {
  return (
    <div className="border w-fit p-3 rounded-md shadow-md bg-white">
      <h2 className="text-lg">
        <b>Avots </b>
        {favourite.source}
      </h2>
      <h2 className="text-lg">
        <b>Pilsēta </b>
        {favourite.city}
      </h2>
      <h2 className="text-lg">
        <b>Darījums </b>
        {favourite.deal_type}
      </h2>
      <h2 className="">
        <b>Apkaime </b>
        {favourite.district}
      </h2>
      <h2 className="">
        <b>Iela </b>
        {favourite.street}
      </h2>
      <h2 className="">
        <b>Sērija</b>: {favourite.series}
      </h2>
      <h2 className="">
        <b>Cena €</b>
        {favourite.price} EUR
      </h2>
      <h2 className="">
        <b>Cena €/m²</b>: {favourite.price_per_m2}
      </h2>
      <h2 className="">
        <b>Istabas</b>: {favourite.rooms} rooms
      </h2>
      <h2 className="">
        <b>Stāvs</b>: {favourite.floor}/{favourite.floors_total}
      </h2>
      <h2 className="">
        <b>Platība</b>: {favourite.area} m²
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
